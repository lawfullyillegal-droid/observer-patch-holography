#!/usr/bin/env python3
"""
Alternative arXiv-style PDF builder for PAPER.md.

Pipeline:
1) Markdown preprocessing (abstract extraction, TOC/title cleanup)
2) pandoc markdown -> LaTeX
3) TeX post-processing (Unicode math normalization + script repair)
4) tectonic compilation to PDF
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
PROCESSED_MD = PAPER_DIR / "PAPER-CODEX.processed.md"
OUTPUT_TEX = PAPER_DIR / "PAPER-CODEX.tex"
OUTPUT_PDF = PAPER_DIR / "PAPER-CODEX.pdf"
TEMPLATE = PAPER_DIR / "template_codex.tex"


UNICODE_REPLACEMENTS = {
    # Arrows
    "⟹": r"\ensuremath{\Longrightarrow}",
    "⟸": r"\ensuremath{\Longleftarrow}",
    "→": r"\ensuremath{\to}",
    "←": r"\ensuremath{\leftarrow}",
    "↔": r"\ensuremath{\leftrightarrow}",
    "⇒": r"\ensuremath{\Rightarrow}",
    # Relations
    "≠": r"\ensuremath{\neq}",
    "≡": r"\ensuremath{\equiv}",
    "≤": r"\ensuremath{\leq}",
    "≥": r"\ensuremath{\geq}",
    "≈": r"\ensuremath{\approx}",
    "≅": r"\ensuremath{\cong}",
    "≲": r"\ensuremath{\lesssim}",
    "≳": r"\ensuremath{\gtrsim}",
    "∼": r"\ensuremath{\sim}",
    "≪": r"\ensuremath{\ll}",
    "≫": r"\ensuremath{\gg}",
    "∝": r"\ensuremath{\propto}",
    # Ops
    "×": r"\ensuremath{\times}",
    "±": r"\ensuremath{\pm}",
    "·": r"\ensuremath{\cdot}",
    # Large ops and misc math
    "∞": r"\ensuremath{\infty}",
    "∫": r"\ensuremath{\int}",
    "∑": r"\ensuremath{\sum}",
    "∏": r"\ensuremath{\prod}",
    "√": r"\ensuremath{\sqrt{}}",
    "∂": r"\ensuremath{\partial}",
    "∈": r"\ensuremath{\in}",
    "†": r"\ensuremath{\dagger}",
    "−": r"\ensuremath{-}",
    "∩": r"\ensuremath{\cap}",
    "∪": r"\ensuremath{\cup}",
    "⊂": r"\ensuremath{\subset}",
    "⊃": r"\ensuremath{\supset}",
    "⊆": r"\ensuremath{\subseteq}",
    "⊇": r"\ensuremath{\supseteq}",
    "⊕": r"\ensuremath{\oplus}",
    "⊗": r"\ensuremath{\otimes}",
    # Greek lowercase
    "α": r"\ensuremath{\alpha}",
    "β": r"\ensuremath{\beta}",
    "γ": r"\ensuremath{\gamma}",
    "δ": r"\ensuremath{\delta}",
    "ε": r"\ensuremath{\varepsilon}",
    "ζ": r"\ensuremath{\zeta}",
    "η": r"\ensuremath{\eta}",
    "θ": r"\ensuremath{\theta}",
    "κ": r"\ensuremath{\kappa}",
    "λ": r"\ensuremath{\lambda}",
    "μ": r"\ensuremath{\mu}",
    "ν": r"\ensuremath{\nu}",
    "ξ": r"\ensuremath{\xi}",
    "π": r"\ensuremath{\pi}",
    "ρ": r"\ensuremath{\rho}",
    "σ": r"\ensuremath{\sigma}",
    "τ": r"\ensuremath{\tau}",
    "φ": r"\ensuremath{\varphi}",
    "χ": r"\ensuremath{\chi}",
    "ψ": r"\ensuremath{\psi}",
    "ω": r"\ensuremath{\omega}",
    # Greek uppercase
    "Γ": r"\ensuremath{\Gamma}",
    "Δ": r"\ensuremath{\Delta}",
    "Θ": r"\ensuremath{\Theta}",
    "Λ": r"\ensuremath{\Lambda}",
    "Ξ": r"\ensuremath{\Xi}",
    "Π": r"\ensuremath{\Pi}",
    "Σ": r"\ensuremath{\Sigma}",
    "Φ": r"\ensuremath{\Phi}",
    "Ψ": r"\ensuremath{\Psi}",
    "Ω": r"\ensuremath{\Omega}",
    # Script/blackboard
    "𝒜": r"\ensuremath{\mathcal{A}}",
    "𝒞": r"\ensuremath{\mathcal{C}}",
    "𝒪": r"\ensuremath{\mathcal{O}}",
    "ℋ": r"\ensuremath{\mathcal{H}}",
    "ℂ": r"\ensuremath{\mathbb{C}}",
    "ℤ": r"\ensuremath{\mathbb{Z}}",
    "ℓ": r"\ensuremath{\ell}",
    "ℏ": r"\ensuremath{\hbar}",
    # Symbols
    "☉": r"\ensuremath{\odot}",
    "✓": r"\checkmark{}",
    "⟨": r"\ensuremath{\langle}",
    "⟩": r"\ensuremath{\rangle}",
    "□": r"\ensuremath{\square}",
    # Superscript letters
    "ᶜ": r"\textsuperscript{c}",
    "ʸ": r"\textsuperscript{y}",
    # Typography
    "─": "-",
    "═": "=",
    "…": r"\ldots{}",
    "—": "---",
    "–": "--",
    "\u201C": "``",
    "\u201D": "''",
    "\u2018": "`",
    "\u2019": "'",
    "′": "'",
    "″": "''",
    # Accented chars used in references
    "Č": r"\v{C}",
    "č": r"\v{c}",
    "ŝ": r"\^{s}",
    "Ũ": r"\~{U}",
    "ü": r"\"u",
    "ö": r"\"o",
    "ä": r"\"a",
    "é": r"\'e",
    "è": r"\`e",
}


def run_or_die(cmd: list[str], cwd: Path | None = None, label: str = "command") -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"{label} failed with exit code {result.returncode}", file=sys.stderr)
        if result.stdout.strip():
            print(result.stdout[-5000:], file=sys.stderr)
        if result.stderr.strip():
            print(result.stderr[-5000:], file=sys.stderr)
        raise SystemExit(1)
    return result


def convert_md_fragment_to_latex(md_text: str) -> str:
    result = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "latex", "--wrap=preserve"],
        input=md_text,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr[-5000:], file=sys.stderr)
        raise SystemExit(1)
    return result.stdout.strip()


def fix_display_math_blocks(text: str) -> str:
    lines = text.split("\n")
    result: list[str] = []
    idx = 0
    while idx < len(lines):
        if lines[idx].strip() == "$$":
            cursor = idx + 1
            while cursor < len(lines) and lines[cursor].strip() == "":
                cursor += 1
            if cursor < len(lines) and lines[cursor].strip() != "$$":
                math_lines: list[str] = []
                while cursor < len(lines):
                    if lines[cursor].strip() == "$$":
                        break
                    if lines[cursor].strip():
                        math_lines.append(lines[cursor])
                    cursor += 1
                if result and result[-1].strip():
                    result.append("")
                result.append("$$")
                result.extend(math_lines)
                result.append("$$")
                result.append("")
                idx = cursor + 1
                continue
        result.append(lines[idx])
        idx += 1
    return "\n".join(result)


def preprocess_markdown(text: str) -> tuple[str, str]:
    abstract_match = re.search(
        r"^## Abstract\s*\n(.*?)(?=^## Table of Contents)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    abstract_latex = ""
    if abstract_match:
        abstract_latex = convert_md_fragment_to_latex(abstract_match.group(1).strip())
        text = text[: abstract_match.start()] + text[abstract_match.end() :]

    text = re.sub(
        r"^# Observer-Patch Holography\s*\n",
        "",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"^## Table of Contents\s*\n.*?(?=^---\s*$)",
        "",
        text,
        count=1,
        flags=re.MULTILINE | re.DOTALL,
    )
    text = re.sub(r"^---\s*\n", "\n", text, count=2, flags=re.MULTILINE)

    # Remove manual section numbering; let pandoc number sections consistently.
    text = re.sub(r"^(#{2})\s*\d+\.\s+", r"\1 ", text, flags=re.MULTILINE)
    text = re.sub(r"^(#{3})\s*\d+\.\d+\s+", r"\1 ", text, flags=re.MULTILINE)
    text = re.sub(r"^(#{4})\s*\d+\.\d+\.\d+\s+", r"\1 ", text, flags=re.MULTILINE)

    text = fix_display_math_blocks(text)

    header = (
        "---\n"
        'title: "Observer-Patch Holography"\n'
        "---\n\n"
    )
    return header + text, abstract_latex


def replace_unicode_supsub(tex: str) -> str:
    superscript_map = {
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
    subscript_map = {
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

    superscript_chars = "".join(re.escape(char) for char in superscript_map)
    subscript_chars = "".join(re.escape(char) for char in subscript_map)

    tex = re.sub(
        f"[{superscript_chars}]+",
        lambda match: r"\textsuperscript{"
        + "".join(superscript_map.get(char, char) for char in match.group(0))
        + "}",
        tex,
    )
    tex = re.sub(
        f"[{subscript_chars}]+",
        lambda match: r"\textsubscript{"
        + "".join(subscript_map.get(char, char) for char in match.group(0))
        + "}",
        tex,
    )
    return tex


def parse_escaped_group(text: str, start_idx: int) -> tuple[str | None, int]:
    # start_idx points at the leading backslash in "\{"
    if not text.startswith(r"\{", start_idx):
        return None, start_idx

    idx = start_idx + 2
    out: list[str] = []
    while idx < len(text):
        if text.startswith(r"\}", idx):
            return "{" + "".join(out) + "}", idx + 2
        out.append(text[idx])
        idx += 1
    return None, start_idx


def parse_script(text: str, start_idx: int) -> tuple[str | None, int]:
    if start_idx >= len(text):
        return None, start_idx

    if text.startswith(r"\{", start_idx):
        return parse_escaped_group(text, start_idx)

    if text[start_idx] == "{":
        depth = 1
        idx = start_idx + 1
        while idx < len(text) and depth > 0:
            if text[idx] == "{":
                depth += 1
            elif text[idx] == "}":
                depth -= 1
            idx += 1
        if depth == 0:
            return text[start_idx:idx], idx
        return None, start_idx

    if text[start_idx].isalnum():
        idx = start_idx
        while idx < len(text) and (text[idx].isalnum() or text[idx] in {"-"}):
            idx += 1
        token = text[start_idx:idx]
        if len(token) == 1:
            return token, idx
        return "{" + token + "}", idx

    return None, start_idx


def fix_ensuremath_scripts(tex: str) -> str:
    """
    Convert text-mode escaped scripts after ensuremath symbols to true math.

    Example:
      \\ensuremath{\\Lambda}\\_\\{\\overline{\\mathrm{MS}}\\}\\^{}\\{(5)\\}
    ->
      $\\Lambda_{\\overline{\\mathrm{MS}}}^{(5)}$
    """

    marker = r"\ensuremath{"
    out: list[str] = []
    idx = 0
    while idx < len(tex):
        if tex.startswith(marker, idx):
            cursor = idx + len(marker)
            depth = 1
            while cursor < len(tex) and depth > 0:
                if tex[cursor] == "{":
                    depth += 1
                elif tex[cursor] == "}":
                    depth -= 1
                cursor += 1

            if depth != 0:
                out.append(tex[idx])
                idx += 1
                continue

            core = tex[idx + len(marker) : cursor - 1]
            script_cursor = cursor
            scripts: list[str] = []
            changed = False

            while True:
                if tex.startswith(r"\_", script_cursor):
                    script_body, next_idx = parse_script(tex, script_cursor + 2)
                    if script_body is None:
                        break
                    scripts.append("_" + script_body)
                    script_cursor = next_idx
                    changed = True
                    continue

                if tex.startswith(r"\^{}", script_cursor):
                    script_body, next_idx = parse_script(tex, script_cursor + 4)
                    if script_body is None:
                        break
                    scripts.append("^" + script_body)
                    script_cursor = next_idx
                    changed = True
                    continue

                if tex.startswith(r"\^", script_cursor):
                    script_body, next_idx = parse_script(tex, script_cursor + 2)
                    if script_body is None:
                        break
                    scripts.append("^" + script_body)
                    script_cursor = next_idx
                    changed = True
                    continue

                break

            if changed:
                out.append("$" + core + "".join(scripts) + "$")
                idx = script_cursor
                continue

        out.append(tex[idx])
        idx += 1

    return "".join(out)


def postprocess_tex(tex: str, abstract_latex: str) -> str:
    if abstract_latex:
        tex = tex.replace(
            r"\maketitle",
            "\\maketitle\n\n\\begin{abstract}\n"
            + abstract_latex
            + "\n\\end{abstract}\n",
            1,
        )

    # Normalize display-math fences.
    def normalize_display_math(match: re.Match[str]) -> str:
        body = re.sub(r"\n\s*\n", "\n", match.group(1).strip())
        return "\\[\n" + body + "\n\\]"

    tex = re.sub(r"\$\$\s*\n(.*?)\n\s*\$\$", normalize_display_math, tex, flags=re.DOTALL)
    tex = re.sub(r"\$\$([^$]+?)\$\$", r"\\[\1\\]", tex)

    # Deprecated \rm -> \mathrm
    tex = re.sub(r"\{\\rm\s+(\w+)\}", r"\\mathrm{\1}", tex)

    tex = replace_unicode_supsub(tex)

    for char, replacement in UNICODE_REPLACEMENTS.items():
        tex = tex.replace(char, replacement)

    # Remove combining marks that TeX cannot interpret reliably in this setup.
    tex = tex.replace("\u0302", "")
    tex = tex.replace("\u0304", "")

    tex = fix_ensuremath_scripts(tex)
    return tex


def compile_tex_to_pdf(tex_file: Path) -> str:
    result = subprocess.run(
        ["tectonic", "-X", "compile", str(tex_file)],
        cwd=PAPER_DIR,
        capture_output=True,
        text=True,
    )

    log = (result.stdout or "") + "\n" + (result.stderr or "")
    if result.returncode != 0:
        print("tectonic failed", file=sys.stderr)
        print(log[-10000:], file=sys.stderr)
        raise SystemExit(1)

    error_lines = [line for line in log.splitlines() if "error:" in line]
    missing_math_lines = [line for line in log.splitlines() if "Missing $" in line]
    missing_char_lines = [line for line in log.splitlines() if "Missing character" in line]

    if error_lines:
        print("TeX reported errors:", file=sys.stderr)
        for line in error_lines[:20]:
            print(line, file=sys.stderr)
        raise SystemExit(1)

    if missing_math_lines:
        print("TeX reported 'Missing $' diagnostics:", file=sys.stderr)
        for line in missing_math_lines[:20]:
            print(line, file=sys.stderr)
        raise SystemExit(1)

    if missing_char_lines:
        print("TeX reported missing glyphs:", file=sys.stderr)
        for line in missing_char_lines[:20]:
            print(line, file=sys.stderr)
        raise SystemExit(1)

    return log


def main() -> int:
    if not SOURCE_MD.exists():
        print(f"Input markdown not found: {SOURCE_MD}", file=sys.stderr)
        return 1

    if not TEMPLATE.exists():
        print(f"Template not found: {TEMPLATE}", file=sys.stderr)
        return 1

    if shutil.which("pandoc") is None:
        print("pandoc is required but was not found in PATH", file=sys.stderr)
        return 1

    if shutil.which("tectonic") is None:
        print("tectonic is required but was not found in PATH", file=sys.stderr)
        return 1

    source_text = SOURCE_MD.read_text(encoding="utf-8")
    processed_md, abstract_latex = preprocess_markdown(source_text)
    PROCESSED_MD.write_text(processed_md, encoding="utf-8")

    print("Step 1/3: Converting markdown to LaTeX via pandoc...")
    run_or_die(
        [
            "pandoc",
            str(PROCESSED_MD),
            "-f",
            "markdown+raw_tex+tex_math_dollars+tex_math_single_backslash",
            "-o",
            str(OUTPUT_TEX),
            "--template",
            str(TEMPLATE),
            "--number-sections",
            "--toc",
            "--wrap=preserve",
        ],
        cwd=PAPER_DIR,
        label="pandoc full conversion",
    )

    print("Step 2/3: Normalizing LaTeX for robust scientific typesetting...")
    tex = OUTPUT_TEX.read_text(encoding="utf-8")
    tex = postprocess_tex(tex, abstract_latex)
    OUTPUT_TEX.write_text(tex, encoding="utf-8")

    print("Step 3/3: Compiling LaTeX to PDF (tectonic)...")
    compile_tex_to_pdf(OUTPUT_TEX)

    generated_pdf = OUTPUT_TEX.with_suffix(".pdf")
    if not generated_pdf.exists():
        print(f"Expected PDF not found: {generated_pdf}", file=sys.stderr)
        return 1

    if generated_pdf != OUTPUT_PDF:
        generated_pdf.replace(OUTPUT_PDF)

    file_size_kib = os.path.getsize(OUTPUT_PDF) / 1024.0
    print(f"PDF written to {OUTPUT_PDF} ({file_size_kib:.1f} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
