#!/usr/bin/env python3
"""
Independent PDF builder for PAPER.md.

Approach:
1) Normalize math symbols in Markdown before pandoc conversion.
2) Convert normalized Markdown to LaTeX with a dedicated template.
3) Compile with tectonic and fail on TeX errors, missing math markers, or glyph loss.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PAPER_DIR = REPO_ROOT / "paper"

SOURCE_MD = PAPER_DIR / "PAPER.md"
PROCESSED_MD = PAPER_DIR / "PAPER-INDEPENDENT.processed.md"
OUTPUT_TEX = PAPER_DIR / "PAPER-INDEPENDENT.tex"
OUTPUT_PDF = PAPER_DIR / "PAPER-INDEPENDENT.pdf"
TEMPLATE_TEX = PAPER_DIR / "template_independent.tex"


MATH_UNICODE_MAP = {
    # Greek lowercase
    "α": r"\alpha",
    "β": r"\beta",
    "γ": r"\gamma",
    "δ": r"\delta",
    "ε": r"\varepsilon",
    "ζ": r"\zeta",
    "η": r"\eta",
    "θ": r"\theta",
    "κ": r"\kappa",
    "λ": r"\lambda",
    "μ": r"\mu",
    "ν": r"\nu",
    "ξ": r"\xi",
    "π": r"\pi",
    "ρ": r"\rho",
    "σ": r"\sigma",
    "τ": r"\tau",
    "φ": r"\varphi",
    "χ": r"\chi",
    "ψ": r"\psi",
    "ω": r"\omega",
    # Greek uppercase
    "Γ": r"\Gamma",
    "Δ": r"\Delta",
    "Θ": r"\Theta",
    "Λ": r"\Lambda",
    "Ξ": r"\Xi",
    "Π": r"\Pi",
    "Σ": r"\Sigma",
    "Φ": r"\Phi",
    "Ψ": r"\Psi",
    "Ω": r"\Omega",
    # Script / blackboard
    "ℓ": r"\ell",
    "ℏ": r"\hbar",
    "ℂ": r"\mathbb{C}",
    "ℤ": r"\mathbb{Z}",
    "ℋ": r"\mathcal{H}",
    "𝒜": r"\mathcal{A}",
    "𝒞": r"\mathcal{C}",
    "𝒪": r"\mathcal{O}",
    # Relations and arrows
    "≈": r"\approx",
    "≅": r"\cong",
    "≤": r"\leq",
    "≥": r"\geq",
    "≠": r"\neq",
    "≡": r"\equiv",
    "∼": r"\sim",
    "≲": r"\lesssim",
    "≳": r"\gtrsim",
    "≪": r"\ll",
    "≫": r"\gg",
    "∝": r"\propto",
    "→": r"\to",
    "←": r"\leftarrow",
    "↔": r"\leftrightarrow",
    "⇒": r"\Rightarrow",
    "⟹": r"\Longrightarrow",
    "⟸": r"\Longleftarrow",
    # Operators / symbols
    "×": r"\times",
    "±": r"\pm",
    "·": r"\cdot",
    "∞": r"\infty",
    "∫": r"\int",
    "∑": r"\sum",
    "∏": r"\prod",
    "∂": r"\partial",
    "∈": r"\in",
    "∩": r"\cap",
    "∪": r"\cup",
    "⊂": r"\subset",
    "⊃": r"\supset",
    "⊆": r"\subseteq",
    "⊇": r"\supseteq",
    "⊕": r"\oplus",
    "⊗": r"\otimes",
    "√": r"\sqrt{}",
    "☉": r"\odot",
    "†": r"\dagger",
    "⟨": r"\langle",
    "⟩": r"\rangle",
    "□": r"\square",
    "−": "-",
    "§": r"\S",
}

TEXT_REPLACEMENTS = {
    "…": r"\ldots{}",
    "—": "---",
    "–": "--",
    "“": "``",
    "”": "''",
    "‘": "`",
    "’": "'",
    "′": "'",
    "″": "''",
    "✓": r"\checkmark{}",
    "ᶜ": r"\textsuperscript{c}",
    "ʸ": r"\textsuperscript{y}",
    "─": "-",
    "═": "=",
    "Č": r"\v{C}",
    "č": r"\v{c}",
    "ŝ": r"\^{s}",
    "Ũ": r"\~{U}",
    "ü": r"\"u",
    "ö": r"\"o",
    "ä": r"\"a",
    "é": r"\'e",
    "è": r"\`e",
    "\u0302": "",
    "\u0304": "",
}

SUPERSCRIPT_MAP = {
    "⁰": "0",
    "¹": "1",
    "²": "2",
    "³": "3",
    "⁴": "4",
    "⁵": "5",
    "⁶": "6",
    "⁷": "7",
    "⁸": "8",
    "⁹": "9",
    "⁺": "+",
    "⁻": "-",
    "⁽": "(",
    "⁾": ")",
    "ⁿ": "n",
}

SUBSCRIPT_MAP = {
    "₀": "0",
    "₁": "1",
    "₂": "2",
    "₃": "3",
    "₄": "4",
    "₅": "5",
    "₆": "6",
    "₇": "7",
    "₈": "8",
    "₉": "9",
    "₊": "+",
    "₋": "-",
}


def run_or_die(cmd: list[str], *, cwd: Path | None = None, input_text: str | None = None, label: str = "command") -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, cwd=cwd, input=input_text, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"{label} failed with exit code {result.returncode}", file=sys.stderr)
        if result.stdout.strip():
            print(result.stdout[-8000:], file=sys.stderr)
        if result.stderr.strip():
            print(result.stderr[-8000:], file=sys.stderr)
        raise SystemExit(1)
    return result


def parse_brace_group(text: str, start_idx: int) -> tuple[str | None, int]:
    if start_idx >= len(text) or text[start_idx] != "{":
        return None, start_idx

    depth = 1
    idx = start_idx + 1
    while idx < len(text) and depth > 0:
        if text[idx] == "{":
            depth += 1
        elif text[idx] == "}":
            depth -= 1
        idx += 1

    if depth != 0:
        return None, start_idx
    return text[start_idx:idx], idx


def parse_script_token(text: str, start_idx: int) -> tuple[str | None, int]:
    if start_idx >= len(text) or text[start_idx] not in {"_", "^"}:
        return None, start_idx

    operator = text[start_idx]
    idx = start_idx + 1
    if idx < len(text) and text[idx] == "{":
        group, end_idx = parse_brace_group(text, idx)
        if group is None:
            return None, start_idx
        return operator + group, end_idx
    if idx < len(text):
        return operator + text[idx], idx + 1
    return None, start_idx


def tighten_display_math_blocks(text: str) -> str:
    lines = text.split("\n")
    out: list[str] = []
    idx = 0
    while idx < len(lines):
        if lines[idx].strip() == "$$":
            cursor = idx + 1
            while cursor < len(lines) and lines[cursor].strip() == "":
                cursor += 1
            if cursor < len(lines) and lines[cursor].strip() != "$$":
                block: list[str] = []
                while cursor < len(lines):
                    if lines[cursor].strip() == "$$":
                        break
                    if lines[cursor].strip():
                        block.append(lines[cursor])
                    cursor += 1
                if out and out[-1].strip():
                    out.append("")
                out.append("$$")
                out.extend(block)
                out.append("$$")
                out.append("")
                idx = cursor + 1
                continue
        out.append(lines[idx])
        idx += 1
    return "\n".join(out)


def normalize_chunk(chunk: str, *, math_mode: bool) -> str:
    def normalize_script(token: str) -> str:
        operator = token[0]
        body = token[1:]
        if body.startswith("{") and body.endswith("}"):
            inner = normalize_chunk(body[1:-1], math_mode=True)
            return operator + "{" + inner + "}"

        inner = normalize_chunk(body, math_mode=True)
        if len(inner) == 1:
            return operator + inner
        return operator + "{" + inner + "}"

    out: list[str] = []
    idx = 0
    while idx < len(chunk):
        char = chunk[idx]

        if char in SUPERSCRIPT_MAP:
            cursor = idx
            values: list[str] = []
            while cursor < len(chunk) and chunk[cursor] in SUPERSCRIPT_MAP:
                values.append(SUPERSCRIPT_MAP[chunk[cursor]])
                cursor += 1
            value = "".join(values)
            if math_mode:
                out.append("^{" + value + "}")
            else:
                out.append(r"\textsuperscript{" + value + "}")
            idx = cursor
            continue

        if char in SUBSCRIPT_MAP:
            cursor = idx
            values: list[str] = []
            while cursor < len(chunk) and chunk[cursor] in SUBSCRIPT_MAP:
                values.append(SUBSCRIPT_MAP[chunk[cursor]])
                cursor += 1
            value = "".join(values)
            if math_mode:
                out.append("_{" + value + "}")
            else:
                out.append(r"\textsubscript{" + value + "}")
            idx = cursor
            continue

        if char in MATH_UNICODE_MAP:
            command = MATH_UNICODE_MAP[char]
            cursor = idx + 1
            scripts: list[str] = []
            while True:
                token, next_idx = parse_script_token(chunk, cursor)
                if token is None:
                    break
                scripts.append(normalize_script(token))
                cursor = next_idx

            separator = ""
            if cursor < len(chunk) and chunk[cursor].isalpha() and command and command[-1].isalpha():
                separator = "{}"

            if math_mode:
                out.append(command + separator + "".join(scripts))
            else:
                if scripts:
                    out.append("$" + command + separator + "".join(scripts) + "$")
                else:
                    out.append(r"\ensuremath{" + command + "}")
            idx = cursor
            continue

        if char in TEXT_REPLACEMENTS:
            out.append(TEXT_REPLACEMENTS[char])
            idx += 1
            continue

        out.append(char)
        idx += 1

    return "".join(out)


def normalize_markdown_math(text: str) -> str:
    out_lines: list[str] = []
    in_code_fence = False
    in_display_math = False

    for line in text.splitlines(keepends=True):
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            out_lines.append(line)
            continue

        if in_code_fence:
            out_lines.append(line)
            continue

        if stripped == "$$":
            in_display_math = not in_display_math
            out_lines.append(line)
            continue

        if in_display_math:
            out_lines.append(normalize_chunk(line, math_mode=True))
            continue

        rebuilt: list[str] = []
        buffer: list[str] = []
        in_inline_math = False
        idx = 0
        while idx < len(line):
            if line[idx] == "$" and (idx == 0 or line[idx - 1] != "\\"):
                if buffer:
                    rebuilt.append(normalize_chunk("".join(buffer), math_mode=in_inline_math))
                    buffer = []

                if idx + 1 < len(line) and line[idx + 1] == "$":
                    rebuilt.append("$$")
                    idx += 2
                else:
                    rebuilt.append("$")
                    idx += 1
                in_inline_math = not in_inline_math
                continue

            buffer.append(line[idx])
            idx += 1

        if buffer:
            rebuilt.append(normalize_chunk("".join(buffer), math_mode=in_inline_math))

        out_lines.append("".join(rebuilt))

    return "".join(out_lines)


def convert_markdown_fragment_to_latex(md_fragment: str) -> str:
    result = run_or_die(
        ["pandoc", "-f", "markdown", "-t", "latex", "--wrap=preserve"],
        input_text=md_fragment,
        label="abstract pandoc conversion",
    )
    return result.stdout.strip()


def prepare_markdown(source_text: str) -> tuple[str, str]:
    abstract_match = re.search(
        r"^## Abstract\s*\n(.*?)(?=^## Table of Contents)",
        source_text,
        flags=re.MULTILINE | re.DOTALL,
    )
    abstract_latex = ""
    if abstract_match:
        abstract_latex = convert_markdown_fragment_to_latex(abstract_match.group(1).strip())
        source_text = source_text[: abstract_match.start()] + source_text[abstract_match.end() :]

    source_text = re.sub(
        r"^# Observer-Patch Holography\s*\n",
        "",
        source_text,
        count=1,
        flags=re.MULTILINE,
    )
    source_text = re.sub(
        r"^## Table of Contents\s*\n.*?(?=^---\s*$)",
        "",
        source_text,
        count=1,
        flags=re.MULTILINE | re.DOTALL,
    )
    source_text = re.sub(r"^---\s*\n", "\n", source_text, count=2, flags=re.MULTILINE)
    source_text = re.sub(r"^(#{2})\s*\d+\.\s+", r"\1 ", source_text, flags=re.MULTILINE)
    source_text = re.sub(r"^(#{3})\s*\d+\.\d+\s+", r"\1 ", source_text, flags=re.MULTILINE)
    source_text = re.sub(r"^(#{4})\s*\d+\.\d+\.\d+\s+", r"\1 ", source_text, flags=re.MULTILINE)

    source_text = tighten_display_math_blocks(source_text)
    source_text = normalize_markdown_math(source_text)

    header = "---\n" 'title: "Observer-Patch Holography"\n' "---\n\n"
    return header + source_text, abstract_latex


def insert_abstract(tex: str, abstract_latex: str) -> str:
    if not abstract_latex:
        return tex
    return tex.replace(
        r"\maketitle",
        "\\maketitle\n\n\\begin{abstract}\n" + abstract_latex + "\n\\end{abstract}\n",
        1,
    )


def validate_tex_log(log: str) -> None:
    error_lines = [line for line in log.splitlines() if "error:" in line]
    missing_math = [line for line in log.splitlines() if "Missing $" in line]
    missing_glyphs = [line for line in log.splitlines() if "Missing character" in line]

    if error_lines:
        print("TeX errors detected:", file=sys.stderr)
        for line in error_lines[:20]:
            print(line, file=sys.stderr)
        raise SystemExit(1)

    if missing_math:
        print("Missing '$' diagnostics detected:", file=sys.stderr)
        for line in missing_math[:20]:
            print(line, file=sys.stderr)
        raise SystemExit(1)

    if missing_glyphs:
        print("Missing glyph diagnostics detected:", file=sys.stderr)
        for line in missing_glyphs[:20]:
            print(line, file=sys.stderr)
        raise SystemExit(1)


def main() -> int:
    if not SOURCE_MD.exists():
        print(f"Input markdown not found: {SOURCE_MD}", file=sys.stderr)
        return 1
    if not TEMPLATE_TEX.exists():
        print(f"Template not found: {TEMPLATE_TEX}", file=sys.stderr)
        return 1
    if shutil.which("pandoc") is None:
        print("pandoc not found in PATH", file=sys.stderr)
        return 1
    if shutil.which("tectonic") is None:
        print("tectonic not found in PATH", file=sys.stderr)
        return 1

    print("Step 1/3: Normalizing markdown and extracting abstract...")
    source_text = SOURCE_MD.read_text(encoding="utf-8")
    processed_md, abstract_latex = prepare_markdown(source_text)
    PROCESSED_MD.write_text(processed_md, encoding="utf-8")

    print("Step 2/3: Converting normalized markdown to LaTeX...")
    run_or_die(
        [
            "pandoc",
            str(PROCESSED_MD),
            "-f",
            "markdown+raw_tex+tex_math_dollars+tex_math_single_backslash",
            "-o",
            str(OUTPUT_TEX),
            "--template",
            str(TEMPLATE_TEX),
            "--number-sections",
            "--toc",
            "--wrap=preserve",
        ],
        cwd=PAPER_DIR,
        label="pandoc full conversion",
    )

    tex = OUTPUT_TEX.read_text(encoding="utf-8")
    tex = insert_abstract(tex, abstract_latex)
    OUTPUT_TEX.write_text(tex, encoding="utf-8")

    print("Step 3/3: Compiling with tectonic...")
    compile_result = run_or_die(
        ["tectonic", "-X", "compile", str(OUTPUT_TEX)],
        cwd=PAPER_DIR,
        label="tectonic compile",
    )
    log = (compile_result.stdout or "") + "\n" + (compile_result.stderr or "")
    validate_tex_log(log)

    generated_pdf = OUTPUT_TEX.with_suffix(".pdf")
    if not generated_pdf.exists():
        print(f"Expected PDF not found: {generated_pdf}", file=sys.stderr)
        return 1

    if generated_pdf != OUTPUT_PDF:
        generated_pdf.replace(OUTPUT_PDF)

    size_kib = os.path.getsize(OUTPUT_PDF) / 1024.0
    print(f"PDF written to {OUTPUT_PDF} ({size_kib:.1f} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
