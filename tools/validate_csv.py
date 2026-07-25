#!/usr/bin/env python3
"""Validate a Brightspace quiz CSV before you try to import it.

This script checks rules that cause import failures or silently mis-import questions.

Usage:
    python3 validate_csv.py quiz.csv
    python3 validate_csv.py quiz.csv --strict    # warnings become errors

Exit codes: 0 clean, 1 problems found, 2 could not read the file.
"""

import argparse
import csv
import io
import re
import sys

HEADER_ROWS = ["NewQuestion", "Title", "QuestionText", "Points", "Difficulty"]
VALID_TYPES = {"MC", "TF", "WR", "SA", "MS", "M", "O"}
VALID_SCORING = {"RightAnswers", "AllOrNothing", "RightMinusWrong", "EquallyWeighted"}

# Rows that may appear in any question block regardless of type.
OPTIONAL_ROWS = {"ID", "Image", "Hint", "Feedback", "InitialText", "AnswerKey"}
SMART_CHARS = {
    "“": 'left curly double quote (")',
    "”": 'right curly double quote (")',
    "‘": "left curly single quote (')",
    "’": "right curly single quote (')",
    "–": "en dash (-)",
    "—": "em dash (-)",
}


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, line, msg):
        self.errors.append((line, msg))

    def warn(self, line, msg):
        self.warnings.append((line, msg))


def is_comment(text):
    """A row is a comment if its first cell starts with //.

    D2L uses // as a general comment syntax anywhere in the file, not only for a
    trailing FLAGS block. Comments may also be quoted, e.g. `"//(Note: ...)",,,,`.
    """
    stripped = text.lstrip().lstrip('"').lstrip()
    return stripped.startswith("//")


def is_blank_row(text):
    """True for an empty line or a row of nothing but separators (`,,,,`)."""
    return not text.strip().strip(",").strip()


def split_blocks(lines):
    """Split numbered lines into question blocks and the trailing FLAGS section.

    Returns (blocks, flag_lines). Each block is a list of (lineno, text).
    Comment rows are skipped; only a `//FLAGS:` marker opens the flags section.
    """
    blocks, current, flags = [], [], []
    in_flags = False

    for lineno, text in lines:
        if in_flags:
            flags.append((lineno, text))
            continue

        if is_comment(text):
            if text.strip().lstrip('"').upper().startswith("//FLAGS"):
                in_flags = True
                flags.append((lineno, text))
                if current:
                    blocks.append(current)
                    current = []
            # Any other comment is documentation; ignore it.
            continue

        if is_blank_row(text):
            if current:
                blocks.append(current)
                current = []
            continue

        current.append((lineno, text))

    if current:
        blocks.append(current)
    return blocks, flags


def parse_row(text):
    """Parse one CSV row, honouring quoting. Returns [] if unparseable."""
    try:
        return next(csv.reader(io.StringIO(text)))
    except (csv.Error, StopIteration):
        return []


def check_unquoted_commas(lineno, raw, rep):
    """Catch a comma inside an unquoted field.

    Brightspace rows are 5 columns. A row parsing to more than 5 fields means a
    value contained a comma and was not wrapped in quotes -- it silently became
    an extra column. This is the single most common data-corrupting mistake.
    """
    fields = parse_row(raw)
    if len(fields) > 5 and '"' not in raw:
        rep.error(
            lineno,
            f"row parses to {len(fields)} fields (expected 5) -- a value "
            f"containing a comma is not wrapped in double quotes",
        )


def check_smart_chars(lineno, raw, rep):
    for char, name in SMART_CHARS.items():
        if char in raw:
            rep.warn(lineno, f"contains {name} -- use the plain ASCII form")


# Text column and HTML-marker column per row keyword. HTML is legal in these
# fields only when the literal marker "HTML" sits in the column after the text;
# unmarked tags display to students as literal text like <b>bold</b>.
HTML_MARKER_COLS = {
    "QuestionText": (1, 2),
    "Hint": (1, 2),
    "Feedback": (1, 2),
    "InitialText": (1, 2),
    "AnswerKey": (1, 2),
    "Option": (2, 3),
    "Choice": (2, 3),
    "Match": (2, 3),
}
HTML_TAG = re.compile(r"<[a-zA-Z][^>]*>")


def check_html_marker(lineno, raw, rep):
    fields = parse_row(raw)
    if not fields or fields[0] not in HTML_MARKER_COLS:
        return
    text_col, marker_col = HTML_MARKER_COLS[fields[0]]
    text = fields[text_col] if len(fields) > text_col else ""
    marker = fields[marker_col].strip() if len(fields) > marker_col else ""
    if HTML_TAG.search(text) and marker != "HTML":
        rep.warn(
            lineno,
            f"{fields[0]} contains HTML tags but no 'HTML' marker in column "
            f"{marker_col + 1} -- the tags will display to students as literal text",
        )


def check_header(block, rep):
    """Verify the required header rows are present. Returns the type code.

    The five required rows must all appear, but not at fixed positions -- an
    optional `ID` row may sit between NewQuestion and Title.
    """
    lineno0 = block[0][0]

    first = parse_row(block[0][1])
    if not first or first[0] != "NewQuestion":
        rep.error(
            lineno0,
            f"block starts with '{first[0] if first else ''}'; every question "
            f"block must open with a NewQuestion row",
        )
        return None

    qtype = first[1].strip() if len(first) > 1 else ""
    if qtype not in VALID_TYPES:
        rep.error(
            lineno0,
            f"unknown question type '{qtype}' -- expected one of "
            f"{', '.join(sorted(VALID_TYPES))}",
        )
        qtype = None

    seen = {}
    for lineno, raw in block:
        fields = parse_row(raw)
        if fields and fields[0] in HEADER_ROWS:
            seen.setdefault(fields[0], (lineno, fields))

    for required in HEADER_ROWS[1:]:
        if required not in seen:
            rep.error(lineno0, f"block is missing its required '{required}' row")

    if "QuestionText" in seen:
        lineno, fields = seen["QuestionText"]
        if len(fields) < 2 or not fields[1].strip():
            rep.error(lineno, "QuestionText is empty")

    # The allowable range is not entirely clear.
    if "Difficulty" in seen:
        lineno, fields = seen["Difficulty"]
        raw = fields[1].strip() if len(fields) > 1 else ""
        try:
            level = int(raw)
        except ValueError:
            rep.error(lineno, f"Difficulty '{raw}' is not a whole number")
        else:
            if not 1 <= level <= 5:
                rep.warn(
                    lineno,
                    f"Difficulty {level} is outside the suggested 1-5 range",
                )

    return qtype


def check_body(block, qtype, rep):
    """Type-specific answer rows."""
    lineno0 = block[0][0]
    # Answer rows are whatever is left once required and optional rows are removed.
    rows = [(ln, parse_row(raw)) for ln, raw in block]
    rows = [(ln, f) for ln, f in rows if not (f and f[0] in HEADER_ROWS)]

    # Optional rows are valid on every type; check then set them aside.
    for ln, f in rows:
        if f and f[0] == "Scoring":
            mode = f[1].strip() if len(f) > 1 else ""
            if mode not in VALID_SCORING:
                rep.error(
                    ln,
                    f"unknown Scoring mode '{mode}' -- expected one of "
                    f"{', '.join(sorted(VALID_SCORING))}",
                )
    rows = [(ln, f) for ln, f in rows if not (f and f[0] in OPTIONAL_ROWS)]

    if qtype == "WR":
        stray = [ln for ln, f in rows if f and f[0] not in OPTIONAL_ROWS]
        if stray:
            rep.error(stray[0], "written response (WR) takes no answer rows")
        return

    if qtype == "M":
        choices = {}
        for ln, f in rows:
            if f and f[0] == "Choice" and len(f) > 1:
                choices[f[1].strip()] = ln
        matches = [(ln, f) for ln, f in rows if f and f[0] == "Match"]
        if not choices:
            rep.error(lineno0, "matching question (M) has no Choice rows")
        if not matches:
            rep.error(lineno0, "matching question (M) has no Match rows")
        for ln, f in matches:
            ref = f[1].strip() if len(f) > 1 else ""
            if ref not in choices:
                rep.error(
                    ln,
                    f"Match refers to Choice '{ref}', which is not defined "
                    f"(choices present: {', '.join(sorted(choices)) or 'none'})",
                )
        return

    if qtype == "O":
        items = [(ln, f) for ln, f in rows if f and f[0] == "Item"]
        if not items:
            rep.error(lineno0, "ordering question (O) has no Item rows")
        for ln, f in items:
            if len(f) < 2 or not f[1].strip():
                rep.error(ln, "Item row has no text in column 2")
            flag = f[2].strip() if len(f) > 2 else ""
            if flag and flag not in {"HTML", "NOT HTML"}:
                rep.error(
                    ln,
                    f"Item column 3 is '{flag}' -- expected 'HTML' or 'NOT HTML'",
                )
        return

    if not rows:
        rep.error(lineno0, f"{qtype} question has no answer rows")
        return

    if qtype == "MC":
        options = [(ln, f) for ln, f in rows if f and f[0] == "Option"]
        if not options:
            rep.error(lineno0, "MC question has no Option rows")
            return
        correct = [ln for ln, f in options if len(f) > 1 and f[1].strip() == "100"]
        if len(correct) == 0:
            rep.warn(
                lineno0,
                "MC question has no Option marked 100. Valid only if the instructor "
                "intends partial credit throughout; otherwise there is no fully "
                "correct answer.",
            )
        elif len(correct) > 1:
            rep.error(
                lineno0,
                f"MC question has {len(correct)} Options marked 100 "
                f"(lines {', '.join(map(str, correct))}) -- only one answer can be "
                f"fully correct. For several correct answers use MS.",
            )
        # Weights are percentages of the question's points; partial credit is allowed.
        for ln, f in options:
            weight = f[1].strip() if len(f) > 1 else ""
            try:
                value = float(weight)
            except ValueError:
                rep.error(ln, f"MC Option weight '{weight}' is not a number")
                continue
            if not 0 <= value <= 100:
                rep.error(ln, f"MC Option weight '{weight}' is outside the range 0-100")

    elif qtype == "MS":
        scoring = [f for _, f in rows if f and f[0] == "Scoring"]
        if not scoring:
            rep.warn(lineno0, "MS question has no 'Scoring,RightAnswers' row")
        options = [(ln, f) for ln, f in rows if f and f[0] == "Option"]
        if not options:
            rep.error(lineno0, "MS question has no Option rows")
            return
        # A likely cause of MS import failures.
        hundreds = [ln for ln, f in options if len(f) > 1 and f[1].strip() == "100"]
        if hundreds:
            rep.error(
                lineno0,
                f"MS Options use weight 100 (lines {', '.join(map(str, hundreds))}) -- "
                f"multi-select scores 1 for correct and 0 for incorrect, NOT 100/0. "
                f"This is a likely cause of multi-select import failure.",
            )
        if not any(len(f) > 1 and f[1].strip() == "1" for _, f in options):
            rep.error(lineno0, "MS question has no Option marked 1 -- no correct answer")
        for ln, f in options:
            weight = f[1].strip() if len(f) > 1 else ""
            if weight not in {"1", "0", "100"}:  # 100 already reported above
                rep.error(
                    ln,
                    f"MS Option weight '{weight}' -- multi-select accepts only 1 "
                    f"(correct) or 0 (incorrect)",
                )

    elif qtype == "TF":
        trues = [(ln, f) for ln, f in rows if f and f[0] in {"TRUE", "FALSE"}]
        if len(trues) != 2:
            rep.error(lineno0, f"TF question has {len(trues)} TRUE/FALSE rows; expected exactly 2")
            return
        correct = [ln for ln, f in trues if len(f) > 1 and f[1].strip() == "100"]
        if len(correct) != 1:
            rep.error(
                lineno0,
                f"TF question has {len(correct)} rows marked 100; exactly one of "
                f"TRUE/FALSE must be 100 and the other 0",
            )

    elif qtype == "SA":
        if not any(f and f[0] == "InputBox" for _, f in rows):
            rep.warn(lineno0, "SA question has no InputBox row")
        answers = [(ln, f) for ln, f in rows if f and f[0] == "Answer"]
        if not answers:
            rep.error(lineno0, "SA question has no Answer rows")
        # Weights are percentages; partial credit on an alternative answer is allowed.
        for ln, f in answers:
            weight = f[1].strip() if len(f) > 1 else ""
            try:
                value = float(weight)
            except ValueError:
                rep.error(ln, f"SA Answer weight '{weight}' is not a number")
                continue
            if not 0 <= value <= 100:
                rep.error(ln, f"SA Answer weight '{weight}' is outside the range 0-100")


def validate(path, rep):
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        raw_lines = fh.read().splitlines()
    lines = list(enumerate(raw_lines, start=1))

    if not any(text.strip() for _, text in lines):
        rep.error(0, "file is empty")
        return

    for lineno, raw in lines:
        if raw.strip().startswith("//"):
            continue
        check_smart_chars(lineno, raw, rep)
        if raw.strip():
            check_unquoted_commas(lineno, raw, rep)
            check_html_marker(lineno, raw, rep)

    # Empty-line separators import, but each one leaves an empty junk folder behind in the 
    # Question Library. Separate blocks with rows of commas (",,,,") instead.
    last_content = max((ln for ln, text in lines if text.strip()), default=0)
    empty_seps = [ln for ln, text in lines if not text.strip() and ln < last_content]
    if empty_seps:
        rep.warn(
            empty_seps[0],
            f"{len(empty_seps)} empty line(s) used as separators -- separate "
            f"question blocks with a row of commas (,,,,) instead; every "
            f"empty-line separator leaves an empty junk folder "
            f"in the Question Library on import",
        )

    blocks, flags = split_blocks(lines)

    if not blocks:
        rep.error(0, "no question blocks found")
    for block in blocks:
        qtype = check_header(block, rep)
        if qtype:
            check_body(block, qtype, rep)

    if flags:
        stray = [ln for ln, text in flags if not text.strip().startswith("//") and text.strip()]
        for ln in stray:
            rep.error(ln, "content appears after the //FLAGS: section; flags must come last")
    else:
        # Not an error -- a clean source document legitimately produces no flags.
        rep.warn(
            0,
            "no //FLAGS: section. If the source had questions that were ambiguous or of an "
            "unsupported type, they should be listed here rather than silently dropped.",
        )


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("csvfile", help="Brightspace quiz CSV to check")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = ap.parse_args()

    rep = Report()
    try:
        validate(args.csvfile, rep)
    except FileNotFoundError:
        print(f"error: no such file: {args.csvfile}", file=sys.stderr)
        return 2
    except UnicodeDecodeError as exc:
        print(f"error: {args.csvfile} is not valid UTF-8: {exc}", file=sys.stderr)
        return 2

    for lineno, msg in sorted(rep.errors):
        print(f"{args.csvfile}:{lineno}: error: {msg}")
    for lineno, msg in sorted(rep.warnings):
        print(f"{args.csvfile}:{lineno}: warning: {msg}")

    n_err, n_warn = len(rep.errors), len(rep.warnings)
    if n_err or n_warn:
        print(f"\n{n_err} error(s), {n_warn} warning(s)")
    if n_err or (args.strict and n_warn):
        return 1
    print(f"{args.csvfile}: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
