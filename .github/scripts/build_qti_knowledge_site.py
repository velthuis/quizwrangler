#!/usr/bin/env python3
"""Build the public reference site used by the M365 Copilot QTI agent."""

from __future__ import annotations

import html
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
REFERENCES = ROOT / "plugin" / "skills" / "quizwrangler-qti" / "references"
OUTPUT = ROOT / "_site"
PAGES = {
    "qti-package-profile": ("QTI package profile", "package-profile.md"),
    "qti-standard-items": ("QTI standard item patterns", "standard-items.md"),
    "qti-advanced-items": ("QTI advanced item patterns", "advanced-items.md"),
    "qti-formatting-media": ("QTI formatting and media", "formatting-media.md"),
}

BING_SITE_VERIFICATION = '<meta name="msvalidate.01" content="7F59707A2D884522BCA1C3B956DE365C" />'


def inline_markdown(text: str) -> str:
    """Render the small inline Markdown subset used by the references."""
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    return re.sub(
        r"\[([^\]]+)\]\((#[^)]+)\)",
        r'<a href="\2">\1</a>',
        escaped,
    )


def heading_id(text: str) -> str:
    """Make the same compact fragment identifiers used by the contents list."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def markdown_html(markdown: str) -> str:
    """Render the Markdown constructs used by the references without a dependency."""
    parts = []
    paragraph = []
    list_type = None
    code_lines = None
    code_language = ""

    def close_paragraph() -> None:
        if paragraph:
            parts.append(f"<p>{inline_markdown(' '.join(paragraph))}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            parts.append(f"</{list_type}>")
            list_type = None

    def table_cells(line: str) -> list[str]:
        return [cell.strip() for cell in line.strip().strip("|").split("|")]

    def is_table_row(line: str) -> bool:
        return line.startswith("|") and line.endswith("|")

    def is_table_separator(line: str) -> bool:
        return all(
            re.fullmatch(r":?-{3,}:?", cell) for cell in table_cells(line)
        )

    lines = markdown.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("```"):
            if code_lines is None:
                close_paragraph()
                close_list()
                code_lines = []
                code_language = line[3:].strip() or "text"
            else:
                parts.append(
                    f'<pre><code class="language-{html.escape(code_language)}">'
                    f"{html.escape(chr(10).join(code_lines))}</code></pre>"
                )
                code_lines = None
                code_language = ""
            index += 1
            continue

        if code_lines is not None:
            code_lines.append(line)
            index += 1
            continue

        if not line.strip():
            close_paragraph()
            close_list()
            index += 1
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            close_paragraph()
            close_list()
            level = len(heading.group(1))
            text = heading.group(2)
            if level > 1:
                parts.append(
                    f'<h{level} id="{heading_id(text)}">{inline_markdown(text)}</h{level}>'
                )
            index += 1
            continue

        if is_table_row(line):
            close_paragraph()
            close_list()
            table_lines = []
            while index < len(lines) and is_table_row(lines[index]):
                table_lines.append(lines[index])
                index += 1
            if len(table_lines) >= 2 and is_table_separator(table_lines[1]):
                headers = table_cells(table_lines[0])
                rows = [table_cells(row) for row in table_lines[2:]]
                parts.append("<table><thead><tr>" + "".join(
                    f"<th>{inline_markdown(cell)}</th>" for cell in headers
                ) + "</tr></thead><tbody>")
                for row in rows:
                    parts.append("<tr>" + "".join(
                        f"<td>{inline_markdown(cell)}</td>" for cell in row
                    ) + "</tr>")
                parts.append("</tbody></table>")
            continue

        unordered = re.match(r"^[-*]\s+(.+)$", line)
        ordered = re.match(r"^\d+\.\s+(.+)$", line)
        if unordered or ordered:
            close_paragraph()
            wanted = "ul" if unordered else "ol"
            if list_type != wanted:
                close_list()
                parts.append(f"<{wanted}>")
                list_type = wanted
            parts.append(f"<li>{inline_markdown((unordered or ordered).group(1))}</li>")
            index += 1
            continue

        paragraph.append(line.strip())
        index += 1

    close_paragraph()
    close_list()
    return "\n".join(parts)


def page(title: str, content: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  {BING_SITE_VERIFICATION}
  <title>{html.escape(title)} | QuizWrangler</title>
  <style>
    body {{ font-family: system-ui, sans-serif; line-height: 1.5; margin: 2rem auto; max-width: 72rem; padding: 0 1rem; }}
    pre {{ overflow-x: auto; white-space: pre-wrap; }}
    table {{ border-collapse: collapse; }}
    th, td {{ border: 1px solid #bbb; padding: 0.35rem 0.6rem; text-align: left; }}
  </style>
</head>
<body>
  <main>
    <h1>{html.escape(title)}</h1>
    {content}
  </main>
</body>
</html>
"""


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    links = []
    for slug, (title, filename) in PAGES.items():
        markdown = (REFERENCES / filename).read_text(encoding="utf-8")
        content = markdown_html(markdown)
        directory = OUTPUT / slug
        directory.mkdir(exist_ok=True)
        (directory / "index.html").write_text(page(title, content), encoding="utf-8")
        links.append(f'<li><a href="{slug}/">{html.escape(title)}</a></li>')

    index = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{}
<title>QuizWrangler QTI knowledge</title></head><body><main>
<h1>QuizWrangler QTI knowledge</h1>
<p>Reference material for the QuizWrangler Brightspace QTI agent.</p>
<ul>{}</ul></main></body></html>""".format(BING_SITE_VERIFICATION, "".join(links))
    (OUTPUT / "index.html").write_text(index, encoding="utf-8")


if __name__ == "__main__":
    main()
