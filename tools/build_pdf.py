#!/usr/bin/env python3
"""
Convert PAPER.md to a properly formatted scientific PDF.

Pipeline: Markdown -> (pandoc) -> LaTeX -> (tectonic) -> PDF
With post-processing to handle Unicode and formatting issues.
"""
import re
import sys
import subprocess
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PAPER_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "paper")
PAPER = os.path.join(PAPER_DIR, "PAPER.md")
OUTPUT_MD = os.path.join(PAPER_DIR, "PAPER_processed.md")
OUTPUT_TEX = os.path.join(PAPER_DIR, "PAPER_processed.tex")
OUTPUT_PDF = os.path.join(PAPER_DIR, "PAPER.pdf")
TEMPLATE = os.path.join(PAPER_DIR, "template.tex")

# ═══════════════════════════════════════════════════════════════
# Unicode → LaTeX replacements (applied to .tex output)
# Using \ensuremath{} so they work in both text and math mode
# ═══════════════════════════════════════════════════════════════
UNICODE_REPLACEMENTS = {
    # Arrows
    '⟹': r'\ensuremath{\Longrightarrow}', '⟸': r'\ensuremath{\Longleftarrow}',
    '→': r'\ensuremath{\to}', '←': r'\ensuremath{\leftarrow}',
    '↔': r'\ensuremath{\leftrightarrow}', '⇒': r'\ensuremath{\Rightarrow}',
    # Relations
    '≠': r'\ensuremath{\neq}', '≡': r'\ensuremath{\equiv}',
    '≤': r'\ensuremath{\leq}', '≥': r'\ensuremath{\geq}',
    '≈': r'\ensuremath{\approx}', '≅': r'\ensuremath{\cong}',
    '≲': r'\ensuremath{\lesssim}', '≳': r'\ensuremath{\gtrsim}',
    '∼': r'\ensuremath{\sim}', '≪': r'\ensuremath{\ll}', '≫': r'\ensuremath{\gg}',
    '∝': r'\ensuremath{\propto}',
    # Binary ops
    '×': r'\ensuremath{\times}', '±': r'\ensuremath{\pm}',
    '·': r'\ensuremath{\cdot}',
    # Large ops / misc math
    '∞': r'\ensuremath{\infty}', '∫': r'\ensuremath{\int}',
    '∑': r'\ensuremath{\sum}', '∏': r'\ensuremath{\prod}',
    '√': r'\ensuremath{\sqrt{}}', '∂': r'\ensuremath{\partial}',
    '∈': r'\ensuremath{\in}', '†': r'\ensuremath{\dagger}',
    '−': r'\ensuremath{-}',
    '∩': r'\ensuremath{\cap}', '∪': r'\ensuremath{\cup}',
    '⊂': r'\ensuremath{\subset}', '⊃': r'\ensuremath{\supset}',
    '⊆': r'\ensuremath{\subseteq}', '⊇': r'\ensuremath{\supseteq}',
    '⊕': r'\ensuremath{\oplus}', '⊗': r'\ensuremath{\otimes}',
    # Greek lowercase
    'α': r'\ensuremath{\alpha}', 'β': r'\ensuremath{\beta}',
    'γ': r'\ensuremath{\gamma}', 'δ': r'\ensuremath{\delta}',
    'ε': r'\ensuremath{\varepsilon}', 'ζ': r'\ensuremath{\zeta}',
    'η': r'\ensuremath{\eta}', 'θ': r'\ensuremath{\theta}',
    'κ': r'\ensuremath{\kappa}', 'λ': r'\ensuremath{\lambda}',
    'μ': r'\ensuremath{\mu}', 'ν': r'\ensuremath{\nu}',
    'ξ': r'\ensuremath{\xi}', 'π': r'\ensuremath{\pi}',
    'ρ': r'\ensuremath{\rho}', 'σ': r'\ensuremath{\sigma}',
    'τ': r'\ensuremath{\tau}', 'φ': r'\ensuremath{\varphi}',
    'χ': r'\ensuremath{\chi}', 'ψ': r'\ensuremath{\psi}',
    'ω': r'\ensuremath{\omega}',
    # Greek uppercase
    'Γ': r'\ensuremath{\Gamma}', 'Δ': r'\ensuremath{\Delta}',
    'Θ': r'\ensuremath{\Theta}', 'Λ': r'\ensuremath{\Lambda}',
    'Ξ': r'\ensuremath{\Xi}', 'Π': r'\ensuremath{\Pi}',
    'Σ': r'\ensuremath{\Sigma}', 'Φ': r'\ensuremath{\Phi}',
    'Ψ': r'\ensuremath{\Psi}', 'Ω': r'\ensuremath{\Omega}',
    # Script/Blackboard
    '𝒜': r'\ensuremath{\mathcal{A}}', '𝒞': r'\ensuremath{\mathcal{C}}',
    '𝒪': r'\ensuremath{\mathcal{O}}', 'ℋ': r'\ensuremath{\mathcal{H}}',
    'ℂ': r'\ensuremath{\mathbb{C}}', 'ℤ': r'\ensuremath{\mathbb{Z}}',
    'ℓ': r'\ensuremath{\ell}', 'ℏ': r'\ensuremath{\hbar}',
    # Symbols
    '☉': r'\ensuremath{\odot}', '✓': r'\checkmark{}',
    '⟨': r'\ensuremath{\langle}', '⟩': r'\ensuremath{\rangle}',
    '□': r'\ensuremath{\square}',
    # Modifier letters
    'ᶜ': r'\textsuperscript{c}', 'ʸ': r'\textsuperscript{y}',
    # Box drawing
    '─': '-', '═': '=',
    # Typography
    '…': r'\ldots{}', '—': '---', '–': '--',
    '\u201C': '``', '\u201D': "''", '\u2018': '`', '\u2019': "'",
    '′': "'", '″': "''",
    # Accented
    'Č': r'\v{C}', 'č': r'\v{c}', 'ŝ': r'\^{s}', 'Ũ': r'\~{U}',
    'ü': r'\"u', 'ö': r'\"o', 'ä': r'\"a', 'é': r"\'e", 'è': r'\`e',
}


def convert_md_to_latex(md_text):
    """Convert markdown fragment to LaTeX via pandoc."""
    r = subprocess.run(
        ['pandoc', '-f', 'markdown', '-t', 'latex', '--wrap=preserve'],
        input=md_text, capture_output=True, text=True
    )
    return r.stdout.strip()


def fix_display_math_blocks(text):
    """Remove blank lines inside $$ blocks (pandoc requires this)."""
    lines = text.split('\n')
    result, i = [], 0
    while i < len(lines):
        if lines[i].strip() == '$$':
            j = i + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            if j < len(lines) and lines[j].strip() != '$$':
                math = []
                while j < len(lines):
                    if lines[j].strip() == '$$':
                        break
                    if lines[j].strip():
                        math.append(lines[j])
                    j += 1
                if result and result[-1].strip():
                    result.append('')
                result.append('$$')
                result.extend(math)
                result.append('$$')
                result.append('')
                i = j + 1
                continue
        result.append(lines[i])
        i += 1
    return '\n'.join(result)


# ═══════════════════════════════════════════════════════════════
# Bare math wrapping: wrap subscript/superscript expressions in $...$
# ═══════════════════════════════════════════════════════════════

# Characters that can be part of a math expression base
_GREEK = frozenset('αβγδεζηθκλμνξπρσφχψωΓΔΘΛΞΠΣΦΨΩ')
_MATH_SYM = frozenset('∂∞∫∑∏∈∼≈≡≠≤≥±×·∝⊕⊗ℓℏ𝒜𝒞𝒪ℋℂℤ')
_MATH_CHARS = _GREEK | _MATH_SYM

# Filename/path patterns to skip
_SKIP_WORDS = {'GAUGE', 'GROUP', 'DERIVATION', 'PAPER', 'CODE', 'README'}


def _find_brace_end(text, start):
    """Find position after matching } for { at text[start]. Returns -1 on failure."""
    if start >= len(text) or text[start] != '{':
        return -1
    depth = 1
    i = start + 1
    while i < len(text) and depth > 0:
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
        i += 1
    return i if depth == 0 else -1


def _is_math_base_char(c):
    """Check if character can be part of a math expression base."""
    return c.isalnum() or c in _MATH_CHARS


def wrap_bare_inline_math(text):
    """Wrap bare subscript/superscript expressions in $...$ in markdown.

    Finds patterns like X_Y, X_{Y}, X^{Y}, SU(2)_L etc. that are outside
    existing $...$ or $$...$$ delimiters and wraps them in inline math.
    Works on the full text to properly handle multi-line math regions.
    """
    # Step 1: Find all math regions (character index ranges) in the text
    math_mask = _build_math_mask(text)

    # Step 2: Find all header and YAML lines (skip these entirely)
    skip_mask = _build_skip_mask(text)

    # Step 3: Find bare math expressions and wrap those outside math/skip regions
    return _wrap_with_masks(text, math_mask, skip_mask)


def _build_math_mask(text):
    """Build a boolean array marking characters inside math regions."""
    mask = [False] * len(text)
    i = 0
    while i < len(text):
        if text[i] == '$':
            if i + 1 < len(text) and text[i + 1] == '$':
                # Display math $$...$$
                j = text.find('$$', i + 2)
                if j != -1:
                    for k in range(i, j + 2):
                        mask[k] = True
                    i = j + 2
                    continue
            else:
                # Inline math $...$
                j = text.find('$', i + 1)
                if j != -1:
                    for k in range(i, j + 1):
                        mask[k] = True
                    i = j + 1
                    continue
        i += 1
    return mask


def _build_skip_mask(text):
    """Build a boolean array marking characters on lines that should be skipped."""
    mask = [False] * len(text)
    pos = 0
    for line in text.split('\n'):
        s = line.strip()
        bare = re.sub(r'^(?:>\s*)+', '', s).strip()
        if s.startswith('#') or s.startswith('---') or bare == '$$':
            for k in range(pos, min(pos + len(line), len(text))):
                mask[k] = True
        pos += len(line) + 1  # +1 for \n
    return mask


def _wrap_with_masks(text, math_mask, skip_mask):
    """Find bare math expressions and wrap them, respecting masks."""
    # Find all positions of _ and ^ that are NOT in math or skip regions
    ranges = []
    i = 0
    while i < len(text):
        if text[i] in '_^' and not math_mask[i] and not skip_mask[i]:
            left = _find_base_left(text, i)
            right = _find_sub_super_right(text, i)

            if left < i and right > i + 1:
                expr = text[left:right]
                # Skip filenames, markdown emphasis, etc.
                if _looks_like_filename(expr):
                    i += 1
                    continue
                if expr.startswith('_') or expr.endswith('_'):
                    i += 1
                    continue
                # Ensure entire expression is outside math/skip
                all_outside = all(
                    not math_mask[k] and not skip_mask[k]
                    for k in range(left, right)
                )
                if all_outside:
                    ranges.append((left, right))
                    i = right
                    continue
        i += 1

    if not ranges:
        return text

    # Merge overlapping/adjacent ranges
    ranges.sort()
    merged = [ranges[0]]
    for a, b in ranges[1:]:
        pa, pb = merged[-1]
        if a <= pb + 1:
            merged[-1] = (pa, max(pb, b))
        else:
            merged.append((a, b))

    # Build output with $ delimiters
    result = []
    prev = 0
    for a, b in merged:
        result.append(text[prev:a])
        result.append('$')
        result.append(text[a:b])
        result.append('$')
        prev = b
    result.append(text[prev:])
    return ''.join(result)


def _wrap_bare_math_in_text(text):
    """Find bare math expressions with _/^ in text and wrap in $...$."""
    if '_' not in text and '^' not in text:
        return text

    out = list(text)  # character list for output
    # Track which positions are part of already-wrapped expressions
    wrapped = [False] * len(text)
    # Collect (left, right) ranges to wrap
    ranges = []
    i = 0

    while i < len(text):
        if text[i] in '_^' and not wrapped[i]:
            # Found a potential subscript/superscript
            left = _find_base_left(text, i)
            right = _find_sub_super_right(text, i)

            if left < i and right > i + 1:
                expr = text[left:right]
                # Skip if it looks like a filename or path
                if _looks_like_filename(expr):
                    i += 1
                    continue
                # Skip markdown emphasis patterns like _italic_
                if expr.startswith('_') or expr.endswith('_'):
                    i += 1
                    continue
                ranges.append((left, right))
                for k in range(left, right):
                    wrapped[k] = True
                i = right
                continue
        i += 1

    if not ranges:
        return text

    # Build output: insert $ delimiters around ranges
    # Merge overlapping/adjacent ranges
    ranges.sort()
    merged = [ranges[0]]
    for a, b in ranges[1:]:
        pa, pb = merged[-1]
        if a <= pb + 1:  # overlapping or adjacent
            merged[-1] = (pa, max(pb, b))
        else:
            merged.append((a, b))

    result = []
    prev = 0
    for a, b in merged:
        result.append(text[prev:a])
        result.append('$')
        result.append(text[a:b])
        result.append('$')
        prev = b
    result.append(text[prev:])
    return ''.join(result)


def _find_base_left(text, pos):
    """Find the left boundary of the math base before a _ or ^ at pos."""
    left = pos

    # Include trailing parenthesized group: e.g., SU(2)_L
    if left > 0 and text[left - 1] == ')':
        depth = 1
        left -= 2
        while left >= 0 and depth > 0:
            if text[left] == ')':
                depth += 1
            elif text[left] == '(':
                depth -= 1
            left -= 1
        left += 1  # back to the opening paren

    # Include preceding alphanumeric/Greek/math chars
    while left > 0 and _is_math_base_char(text[left - 1]):
        left -= 1
    # Also include \ for LaTeX commands like \chi
    while left > 0 and text[left - 1] == '\\':
        left -= 1
        # Include the command name
        while left > 0 and text[left - 1].isalpha():
            left -= 1

    return left


def _find_sub_super_right(text, pos):
    """Find the right boundary of subscript/superscript starting at pos.

    Handles chained _/^ and trailing parenthesized groups.
    """
    right = pos
    while right < len(text) and text[right] in '_^':
        marker = text[right]
        right += 1
        if right >= len(text):
            break

        if text[right] == '{':
            end = _find_brace_end(text, right)
            if end > 0:
                right = end
            else:
                break
        elif _is_math_base_char(text[right]):
            right += 1
        elif text[right] == '\\' and right + 1 < len(text) and text[right + 1].isalpha():
            # LaTeX command as subscript like \overline
            right += 1
            while right < len(text) and text[right].isalpha():
                right += 1
            # If followed by {}, include the argument
            if right < len(text) and text[right] == '{':
                end = _find_brace_end(text, right)
                if end > 0:
                    right = end
        else:
            right -= 1  # undo the marker advance
            break

        # Check for trailing parenthesized group: e.g., χ_R(s)
        if right < len(text) and text[right] == '(':
            depth = 1
            j = right + 1
            while j < len(text) and depth > 0:
                if text[j] == '(':
                    depth += 1
                elif text[j] == ')':
                    depth -= 1
                j += 1
            if depth == 0:
                right = j

    return right


def _looks_like_filename(expr):
    """Check if an expression looks like a filename rather than math."""
    if '.md' in expr or '.py' in expr or '.tex' in expr:
        return True
    upper = expr.upper()
    for skip in _SKIP_WORDS:
        if skip in upper:
            return True
    # Multiple consecutive underscores in a word suggest a filename/identifier
    if '__' in expr:
        return True
    return False


def preprocess_markdown(text):
    """Prepare markdown for pandoc conversion."""
    # Extract abstract
    m = re.search(r'^## Abstract\s*\n(.*?)(?=^## Table of Contents)',
                  text, re.MULTILINE | re.DOTALL)
    abstract_latex = convert_md_to_latex(m.group(1).strip()) if m else ""
    if m:
        text = text[:m.start()] + text[m.end():]

    # Remove title, TOC, leading HRs
    text = re.sub(r'^# Observer-Patch Holography\s*\n', '', text, count=1, flags=re.MULTILINE)
    text = re.sub(r'^## Table of Contents\s*\n.*?(?=^---\s*$)', '', text,
                  count=1, flags=re.MULTILINE | re.DOTALL)
    text = re.sub(r'^---\s*\n', '\n', text, count=2, flags=re.MULTILINE)

    # Remove manual section numbers
    text = re.sub(r'^(#{2})\s*\d+\.\s+', r'\1 ', text, flags=re.MULTILINE)
    text = re.sub(r'^(#{3})\s*\d+\.\d+\s+', r'\1 ', text, flags=re.MULTILINE)
    text = re.sub(r'^(#{4})\s*\d+\.\d+\.\d+\s+', r'\1 ', text, flags=re.MULTILINE)

    # Fix display math blocks
    text = fix_display_math_blocks(text)

    # Wrap bare inline math (subscripts/superscripts outside $...$)
    text = wrap_bare_inline_math(text)

    # Add YAML header
    return '---\ntitle: "Observer-Patch Holography"\n---\n\n' + text, abstract_latex


def replace_unicode_supsub(tex):
    """Replace Unicode super/subscript digits."""
    sup = {'⁰':'0','¹':'1','²':'2','³':'3','⁴':'4','⁵':'5','⁶':'6',
           '⁷':'7','⁸':'8','⁹':'9','⁺':'+','⁻':'-','⁽':'(','⁾':')','ⁿ':'n'}
    sub = {'₀':'0','₁':'1','₂':'2','₃':'3','₄':'4','₅':'5','₆':'6',
           '₇':'7','₈':'8','₉':'9','₊':'+','₋':'-'}

    sc = ''.join(re.escape(c) for c in sup)
    tex = re.sub(f'[{sc}]+', lambda m: r'\textsuperscript{' +
                 ''.join(sup.get(c,c) for c in m.group(0)) + '}', tex)
    sc = ''.join(re.escape(c) for c in sub)
    tex = re.sub(f'[{sc}]+', lambda m: r'\textsubscript{' +
                 ''.join(sub.get(c,c) for c in m.group(0)) + '}', tex)
    return tex


def post_process_tex(tex, abstract_latex):
    """Post-process the pandoc-generated .tex file."""

    # 1. Insert abstract
    if abstract_latex:
        tex = tex.replace("\\maketitle",
            "\\maketitle\n\n\\begin{abstract}\n" + abstract_latex + "\n\\end{abstract}\n")

    # 2. Convert $$...$$ to \[...\] (remove internal blank lines)
    def fix_dm(m):
        c = re.sub(r'\n\s*\n', '\n', m.group(1).strip())
        return '\\[\n' + c + '\n\\]'
    tex = re.sub(r'\$\$\s*\n(.*?)\n\s*\$\$', fix_dm, tex, flags=re.DOTALL)
    tex = re.sub(r'\$\$([^$]+?)\$\$', r'\\[\1\\]', tex)

    # 3. Fix deprecated \rm
    tex = re.sub(r'\{\\rm\s+(\w+)\}', r'\\mathrm{\1}', tex)

    # 4. Unicode super/subscripts
    tex = replace_unicode_supsub(tex)

    # 5. Unicode symbols
    for char, repl in UNICODE_REPLACEMENTS.items():
        tex = tex.replace(char, repl)

    # 6. Fix remaining bare subscripts/superscripts in .tex output
    # After Unicode replacement, patterns like \ensuremath{X}\_Y should become $X_Y$
    tex = _fix_bare_subscripts_tex(tex)

    # 7. Fix broken $...\} patterns (escaped braces inside partial math mode)
    tex = _fix_broken_math_braces(tex)

    # 8. Handle combining characters
    tex = tex.replace('\u0302', '')  # combining circumflex (usually part of accent)
    tex = tex.replace('\u0304', '')  # combining macron

    return tex


def _fix_bare_subscripts_tex(tex):
    """Fix bare \\_  and \\^{} patterns in the .tex by wrapping in $...$."""

    # Pattern: \ensuremath{X}\_ followed by a single char or \{...\}
    # Convert to $X_Y$ or $X_{Y}$
    def fix_ensuremath_sub(m):
        base = m.group(1)
        sub = m.group(2)
        # Un-escape braces in subscript
        sub = sub.replace('\\{', '{').replace('\\}', '}')
        return '$' + base + '_' + sub + '$'

    # \ensuremath{X}\_CHAR
    tex = re.sub(
        r'\\ensuremath\{([^}]+)\}\\_([a-zA-Z0-9])',
        fix_ensuremath_sub, tex
    )

    # \ensuremath{X}\_\{CONTENT\}  (with nested \ensuremath{} inside)
    # Need to handle nested braces properly
    tex = _fix_ensuremath_braced_sub(tex)

    # WORD\_CHAR or WORD\_\{CONTENT\} where WORD is a simple letter/word
    # (handles cases like N\_g, H\_\{edge\})
    tex = re.sub(
        r'(?<![\\$])([A-Za-z])\\_([a-zA-Z0-9])(?![{])',
        r'$\1_\2$', tex
    )
    tex = re.sub(
        r'(?<![\\$])([A-Za-z])\\_\\\{([^\\}]*)\\\}',
        r'$\1_{\2}$', tex
    )

    return tex


def _fix_ensuremath_braced_sub(tex):
    """Fix \\ensuremath{X}\\_\\{CONTENT\\} patterns with proper brace matching."""
    pattern = r'\\ensuremath\{([^}]+)\}\\_\\\{'
    result = []
    last = 0

    for m in re.finditer(pattern, tex):
        result.append(tex[last:m.start()])
        base = m.group(1)
        # Find matching \} for the \{ at end of match
        pos = m.end()
        depth = 1
        while pos < len(tex) and depth > 0:
            if tex[pos:pos+2] == '\\{':
                depth += 1
                pos += 2
            elif tex[pos:pos+2] == '\\}':
                depth -= 1
                if depth == 0:
                    pos += 2
                    break
                pos += 2
            elif tex[pos] == '{':
                # Real LaTeX brace (from \ensuremath etc)
                depth2 = 1
                pos += 1
                while pos < len(tex) and depth2 > 0:
                    if tex[pos] == '{':
                        depth2 += 1
                    elif tex[pos] == '}':
                        depth2 -= 1
                    pos += 1
            else:
                pos += 1

        # Extract subscript content
        sub_content = tex[m.end():pos - 2]  # -2 for trailing \}
        # Un-escape braces
        sub_content = sub_content.replace('\\{', '{').replace('\\}', '}')

        # Check for superscript following: \^{}\{...\}
        super_part = ''
        if tex[pos:pos+4] == '\\^{}':
            pos2 = pos + 4
            if tex[pos2:pos2+2] == '\\{':
                pos3 = pos2 + 2
                depth = 1
                while pos3 < len(tex) and depth > 0:
                    if tex[pos3:pos3+2] == '\\{':
                        depth += 1
                        pos3 += 2
                    elif tex[pos3:pos3+2] == '\\}':
                        depth -= 1
                        if depth == 0:
                            pos3 += 2
                            break
                        pos3 += 2
                    else:
                        pos3 += 1
                sup_content = tex[pos2+2:pos3-2].replace('\\{', '{').replace('\\}', '}')
                super_part = '^{' + sup_content + '}'
                pos = pos3

        result.append('$' + base + '_{' + sub_content + '}' + super_part + '$')
        last = pos

    result.append(tex[last:])
    return ''.join(result)


def _fix_broken_math_braces(tex):
    """Fix broken $X_{...\\} patterns where \\} should be }."""
    # Find $ that starts inline math with a subscript/superscript,
    # where the closing brace is escaped as \}
    lines = tex.split('\n')
    fixed_lines = []

    for line in lines:
        if '$' in line and '\\}' in line:
            line = _fix_line_broken_braces(line)
        fixed_lines.append(line)

    return '\n'.join(fixed_lines)


def _fix_line_broken_braces(line):
    r"""Fix a single line with broken $...\} patterns."""
    i = 0
    result = []
    while i < len(line):
        if line[i] == '$':
            # Find the next $ (or end of line)
            j = line.find('$', i + 1)
            if j == -1:
                # Unclosed math - check if there's \} that should close it
                segment = line[i:]
                # Try to fix: replace \} with } and add closing $
                if '\\}' in segment and '_{' in segment:
                    segment = segment.replace('\\}', '}')
                    segment += '$'
                result.append(segment)
                break
            else:
                result.append(line[i:j + 1])
                i = j + 1
        else:
            result.append(line[i])
            i += 1
    return ''.join(result)


def main():
    with open(PAPER) as f:
        text = f.read()

    processed, abstract_latex = preprocess_markdown(text)
    with open(OUTPUT_MD, 'w') as f:
        f.write(processed)

    # Step 1: Pandoc
    print("Step 1: Generating LaTeX via pandoc...")
    r = subprocess.run(
        ['pandoc', OUTPUT_MD, '-o', OUTPUT_TEX, '--template', TEMPLATE,
         '--number-sections', '--toc', '--wrap=preserve'],
        capture_output=True, text=True, cwd=PAPER_DIR)
    if r.returncode != 0:
        print("Pandoc error:", r.stderr[:2000])

    # Step 2: Post-process
    print("Step 2: Post-processing LaTeX...")
    with open(OUTPUT_TEX) as f:
        tex = f.read()
    tex = post_process_tex(tex, abstract_latex)
    with open(OUTPUT_TEX, 'w') as f:
        f.write(tex)

    # Step 3: Compile (continue on errors for robustness)
    print("Step 3: Compiling with tectonic...")
    r = subprocess.run(
        ['tectonic', '-X', 'compile', '-Zcontinue-on-errors', OUTPUT_TEX],
        capture_output=True, text=True, cwd=PAPER_DIR)

    generated = OUTPUT_TEX.replace('.tex', '.pdf')
    if os.path.exists(generated):
        os.rename(generated, OUTPUT_PDF)

        # Count issues
        errors = r.stderr.count('error:')
        warnings = r.stderr.count('warning:')
        missing = r.stderr.count('Missing character')
        missing_dollar = r.stderr.count('Missing $')

        print(f"PDF written to {OUTPUT_PDF}")
        if errors or missing_dollar:
            print(f"  {errors} errors, {missing_dollar} 'Missing $' issues, "
                  f"{missing} missing chars, {warnings} warnings")
            # Show first few unique errors
            seen = set()
            for line in r.stderr.split('\n'):
                if 'error:' in line and line not in seen:
                    seen.add(line)
                    print(f"  >> {line}")
                    if len(seen) >= 5:
                        break
        else:
            print(f"  Clean build! ({warnings} warnings)")
    else:
        print("Failed to produce PDF")
        print(r.stderr[-2000:])
        sys.exit(1)


if __name__ == '__main__':
    main()
