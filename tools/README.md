# Tools

Four scripts.
Python 3.8+, standard library only, nothing to install.

```bash
python3 tools/validate_csv.py my-quiz.csv        # check a CSV before importing
python3 tools/validate_qti.py my-quiz.zip        # check a QTI package
python3 tools/build_skill_zips.py                # build upload-ready skill ZIPs
python3 tools/build_qti_examples.py              # rebuild the QTI example
```

## build_skill_zips.py

Packages each folder in `skills/` into `dist/<skill-name>.zip`, shaped the way the skill uploaders expect: the skill folder at the ZIP root, named to match the `name:` in its frontmatter, with `SKILL.md` inside.

This exists because GitHub's "Download ZIP" produces the wrong shape: it wraps everything in a `<repo>-<branch>/` folder.

`--check` validates without writing anything: every skill folder has a `SKILL.md`, the frontmatter parses, and the folder name matches the declared skill name.

`dist/` is not shared on GitHub directly. Instead, the output is shared in the [GitHub Release](https://github.com/velthuis/quizwrangler/releases) area.


## build_qti_examples.py

Rebuilds the public synthetic QTI package in `examples/expected-output/`.
UUIDv5 values keep the package stable. The script uses no export identifiers
or external content.

---

## Validators

The validators check generated files before you hand them to Brightspace.

Exit codes: `0` clean, `1` problems found, `2` file unreadable.
Add `--strict` to make warnings count as errors for automated checks.

### Why validate

Brightspace's importer may not report what the issue is when a file fails to import. 
The checks below identify common mistakes that cause import failures.

### validate_csv.py

| Check | Why |
|---|---|
| Row parses to more than 5 fields with no quoting | A value containing a comma silently became an extra column. For example: `Answer,100,7,000,,`. |
| Multi-select `Option` weighted `100` | MS scores **1/0**, not 100/0. |
| More than one `Option,100` on an MC | Multiple Choice has one fully correct option. If more than one option is correct, use Multi-Select instead. |
| TF without exactly one `100` | Both marked correct, or neither. |
| Curly quotes, en/em dashes | Break the import. Straight ASCII only. |
| Missing required header rows | All five (`NewQuestion`, `Title`, `QuestionText`, `Points`, `Difficulty`) must be present. Position is not fixed; an optional `ID` row may sit between `NewQuestion` and `Title`. |
| `Match` pointing at an undefined `Choice` | The pairing silently breaks. |
| Bad `Item` HTML flag, unknown `Scoring` mode, out-of-range weights | Malformed values the importer won't honor. |
| Difficulty outside 1-5 | *Warning only.* A range between 1-5 is suggested. |
| No `//FLAGS:` section | *Warning only.* A clean source can legitimately produce no flags, but a silently omitted unconvertible question looks the same. |
| Empty lines used as block separators | *Warning only.* The file imports, but every empty-line separator leaves an empty junk folder in the Question Library. Separate blocks with a row of commas (`,,,,`) instead. |
| HTML tags in a field without the `HTML` marker in the next column | *Warning only.* The file imports, but the tags display to students as literal text like `<b>bold</b>`. |

Note that `//` is a comment anywhere in the file, not just in a trailing FLAGS block.

### validate_qti.py

Runs the validator bundled inside `quizwrangler-qti`, so the repository command and the validator shipped to Codex, Claude Code, Claude chat, and Cowork stay identical. The bundled validator checks a ZIP against QuizWrangler's deliberately narrow QTI package profile.

| Check | Why |
|---|---|
| Manifest at archive root | A nested package cannot be found through the expected import workflow. |
| UTF-8 BOM on every XML file | The profile requires the same encoding marker on every XML entry. |
| XML parsing | Broken escaping or incomplete markup makes the package unreadable. |
| Orgunit identifier equality | The manifest resource and `orgunitconfig.xml` must name the same identifier. |
| Unique item labels and UUIDs | Reused question identities make cross-references ambiguous. |
| Media references | Every local `quizzing/` path must resolve to an archive entry. |
| Pool draw count and shared candidate ident | A random section must draw a valid number and use its pool identity consistently. |
| Type-specific response shape | Each supported item type needs the response container used by its profile template. |
| Arithmetic formula copies and variables | Display and grading formulas must match and reference declared variables. |
| Arithmetic domain sampling | Sampled ranges catch division by zero, non-real results, overflow, and invalid logarithm or square-root inputs. |

The supported formula subset is intentionally conservative. Significant-figure intent is represented as Arithmetic with percent tolerance, not as a separate item type.

### What the validators do not check

The validator checks file structure only; it does not import the file into Brightspace.

Also note that **a clean validator run means the file is well-formed, not that the quiz is correct.**
Nothing here checks whether your answer keys are right.
