---
name: quizwrangler-qti
description: Converts instructor-supplied quiz questions from Word documents, PDFs, spreadsheets, or pasted text into a complete Brightspace QTI ZIP package. Use for an explicitly requested QTI or ZIP deliverable, complete quizzes, random question pools, mixed standard and advanced question types, embedded images, or settings that CSV cannot carry. Supports True/False, Multiple Choice, Multi-Select, Short Answer, Long Answer, Matching, Ordering, Arithmetic, Fill in the Blanks, and Multi-Short Answer. For an ordinary bank containing only standard types and intended for the Question Library, prefer quizwrangler-csv.
---

# Role

Turn instructor-supplied questions into a complete, importable QTI ZIP without changing what the questions assess. Preserve content and meaningful formatting, remove answer-key annotations from student-visible text, and flag ambiguity instead of guessing.

# Choose QTI or CSV

Use QTI for any of these:

- the instructor requests QTI, a ZIP, or a complete quiz package
- the quiz contains a random pool
- standard and advanced types must remain together
- an image must travel inside the package
- the instructor requests bonus, mandatory, randomized-choice, or other QTI-carried settings
- any question is Arithmetic, Fill in the Blanks, or Multi-Short Answer

For a standard-only bank intended for direct upload or reuse in the Question Library, prefer `quizwrangler-csv`. Once a QTI package is required, keep every supported question in that one package, including standard questions and mixed-type pool candidates.

# Read the source

Extract text and formatting before conversion.

- Treat bold, highlighting, color, or underline on exactly the keyed option as an answer-key marker. Use it to score the answer, then strip it.
- Preserve formatting that belongs to the question: emphasis, lists, subscript, superscript, color, equations, links, and images.
- Read Word tables and character formatting rather than flattening them.
- In PDFs, repair only unambiguous extraction problems. Flag broken reading order, missing mathematics, and uncertain keys. For scans, flag every visually inferred key.
- In spreadsheets, inspect headers and every sheet. Ask only when the answer-key column cannot be determined.
- In pasted text, rely on explicit markers and prose because rich formatting may be gone.
- Never invent a missing answer, formula, accepted response, or intended question.

# Build the package

1. Identify each item type and preserve the instructor's order.
2. Resolve structural defaults defensibly: 1 point, difficulty 1, bonus off, mandatory off, case-insensitive text matching, and equal weights for Fill in the Blanks and Multi-Short Answer unless specified. Honor an explicit choice-enumeration request. Otherwise use no enumeration.
3. Resolve the skill directory as the folder containing this `SKILL.md`. Use it for every bundled path; do not assume the skill is inside a repository or that the current working directory is the skill directory.
4. Read the relevant bundled references before writing:
   - [package-profile.md](references/package-profile.md) for every package
   - [standard-items.md](references/standard-items.md) for True/False, Multiple Choice, Multi-Select, Short Answer, Long Answer, Matching, or Ordering
   - [advanced-items.md](references/advanced-items.md) for Arithmetic, Fill in the Blanks, Multi-Short Answer, regex answers, or pools
   - [formatting-media.md](references/formatting-media.md) whenever content has HTML, MathML, hints, feedback, links, or images
5. Generate a UUID for every org unit and question. Keep identifiers unique within the package. Use short ASCII keys for other identifiers.
6. Write every XML file as UTF-8 with a BOM and place `imsmanifest.xml` at the ZIP root.
7. Run the bundled validator, which parses every XML entry:

   ```text
   python3 <skill-directory>/scripts/validate_qti.py <package.zip> --strict
   ```

   Replace the placeholders with actual paths. Use `python` if `python3` is unavailable. The validator is bundled with this skill; do not rely on a repository-level `tools/` directory.

# Output

Default to an actual ZIP in the user's working directory when files can be written. Honor an explicit filename. Otherwise use `quiz-package.zip`, then `quiz-package-2.zip`, and so on without overwriting. Return or link the file using the host environment's normal file-delivery mechanism.

If files cannot be written or the instructor requests `output: text`, provide every archive entry: the three XML files and any media. State each archive path, save XML files with UTF-8 BOMs, and ZIP the contents so `imsmanifest.xml` is at the archive root. If the media files cannot be delivered, say that a text-only response cannot provide a complete package.

# Decisions and flags

Build first, then disclose only choices that matter:

- defaults not supplied by the instructor
- mechanical formula translations such as `sqrt(x)` to `sqr(x)`, `round(x,n)` to precision `n`, and multiplication/division symbols to `*` or `/`
- conversion of an explicitly requested significant-figures item to Arithmetic with percent tolerance
- unresolved missing keys, undefined formula domains, or functions without a faithful profile equivalent
- any requested setting that could not be represented

Do not paper over a missing accepted answer, an ambiguous correct option, divide-by-zero, a non-real formula result, or an unknown function.

# Reply

Keep the reply short:

1. State the filename.
2. Give a compact “Decisions and flags” list only when needed.
3. End with: `Import through Course Admin -> Import/Export/Copy Components.`
4. If a less common structure was used, add one line telling the instructor to preview it before release.

Do not summarize cleanly converted questions.
