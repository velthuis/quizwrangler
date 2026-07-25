# Tools

Two scripts.
Python 3.8+, standard library only, nothing to install.

```bash
python3 tools/validate_csv.py my-quiz.csv        # check a CSV before importing
python3 tools/build_skill_zips.py                # build upload-ready skill ZIPs
```

## build_skill_zips.py

Packages each folder in `skills/` into `dist/<skill-name>.zip`, shaped the way the skill uploaders expect: the skill folder at the ZIP root, named to match the `name:` in its frontmatter, with `SKILL.md` inside.

This exists because GitHub's "Download ZIP" produces the wrong shape — it wraps everything in a `<repo>-<branch>/` folder.

`--check` validates without writing anything: every skill folder has a `SKILL.md`, the frontmatter parses, and the folder name matches the declared skill name.

`dist/` is not shared on GitHub directly. Instead, the output is shared in the [GitHub Release](https://github.com/velthuis/quizwrangler/releases) area.

---

## Validator

A script that checks a generated CSV before you hand it to Brightspace.

Exit codes: `0` clean, `1` problems found, `2` file unreadable.
Add `--strict` to make warnings count as errors — useful in automated checks.

### Why validate

Brightspace's importer may not report what the issue is when a file fails to import. 
The checks below identify common mistakes that cause import failures.

### validate_csv.py

| Check | Why |
|---|---|
| Row parses to more than 5 fields with no quoting | A value containing a comma silently became an extra column. `Answer,100,7,000,,` is the classic. |
| Multi-select `Option` weighted `100` | MS scores **1/0**, not 100/0. The most common multi-select import failure. |
| More than one `Option,100` on an MC | Brightspace takes one correct answer per MC; use MS otherwise. |
| TF without exactly one `100` | Both marked correct, or neither. |
| Curly quotes, en/em dashes | Break the import. Straight ASCII only. |
| Missing required header rows | All five (`NewQuestion`, `Title`, `QuestionText`, `Points`, `Difficulty`) must be present. Position isn't fixed — an optional `ID` row may sit between `NewQuestion` and `Title`. |
| `Match` pointing at an undefined `Choice` | The pairing silently breaks. |
| Bad `Item` HTML flag, unknown `Scoring` mode, out-of-range weights | Malformed values the importer won't honor. |
| Difficulty outside 1-5 | *Warning only.* A range between 1-5 is suggested. |
| No `//FLAGS:` section | *Warning only.* A clean source legitimately produces no flags — but a silent drop of an unconvertible question looks identical to a clean run, which causes problems. |
| Empty lines used as block separators | *Warning only.* The file imports, but every empty-line separator leaves an empty junk folder in the Question Library. Separate blocks with a row of commas (`,,,,`) instead. |
| HTML tags in a field without the `HTML` marker in the next column | *Warning only.* The file imports, but the tags display to students as literal text like `<b>bold</b>`. |

Note that `//` is a comment anywhere in the file, not just in a trailing FLAGS block.

The validator accepts everything in D2L's official [template CSV](https://s.brightspace.com/apps/import-quiz-questions/1.39.1/sample/Sample_Question_Import_UTF8.csv).

### What it doesn't do

No import test against a live Brightspace instance.

Also note that **a clean validator run means the file is well-formed, not that the quiz is correct.**
Nothing here checks whether your answer keys are right.
