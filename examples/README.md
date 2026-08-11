# Test file and worked example

This directory contains deliberately imperfect test files and worked examples for QuizWrangler's two skills. Use them to check that a skill is loaded and behaving as expected before you use it with real course material.

The CSV example converts a messy list of standard questions into an importable CSV file and flags problems instead of guessing. The QTI example creates one complete ZIP package containing standard and advanced question types, a random pool, formatting, and an embedded image.

A result with flags can be correct: the skills should preserve uncertainty rather than invent missing information.

## CSV test file and expected output

```
input/sample-questions-messy.txt    11 questions, deliberately messy
expected-output/sample-quiz.csv     8 CSV question blocks + a FLAGS section with 5 entries
```

## Run it

With the skill [installed](../README.md#install), ask your assistant to use the `quizwrangler-csv` skill:

> Use the quizwrangler-csv skill on the questions below.

and paste the contents of `input/sample-questions-messy.txt` underneath.
(In some environments, you can also type `/quizwrangler-csv` or `$quizwrangler-csv` and paste the questions after it.)

See [the test file](#the-test-file-what-each-planted-problem-tests) section for details on what each one of the 11 proposed quiz questions tests.

### Expected output

You should get **8 question blocks and a `//FLAGS:` section** (covering Q1, Q5, Q7, Q10, and Q11).
Q5 and Q10 are converted but still flagged, because Q5's answer expires in Fall 2026, and Q10's bonus label is not a CSV-processable field.
Q1, Q7, and Q11 are left out of the CSV entirely, because of contradicting answer keys, a missing answer key, and a question type CSV cannot represent.
Q11's flag carries a full spec that `quizwrangler-qti` can process and package or the instructor can enter by hand.

Compare your result against `expected-output/sample-quiz.csv`.

## (Optional) Validate output

Save the assistant's output to a file, then check that it is well-formed. Run this script from the repo root, using the name you saved it under:

```bash
python3 tools/validate_csv.py your-saved-quiz.csv
```

The script will merely check against common structural pitfalls, not whether the questions are "correct" in any pedagogical sense.

## The test file: What each planted problem tests

| # | Planted problem | What it tests | Expected handling |
|---|---|---|---|
| 1 | Options mark `*c. 1859`; the note below says "Correct answer: B" (1842) | Does it notice two answer keys disagree, or take the first one it finds? | **Flag.** Exclude from CSV. |
| 2 | `(T/F)` marker, stem prefixed "True or False:", plus a request for blue underlined text | Does it strip the meta-prefix? And does it honor formatting with HTML plus the `HTML` marker? | Import as `TF`, stem without the prefix, `QuestionText` as HTML (blue, underlined "Villanova") with the `HTML` marker in column 3 |
| 3 | Correct answer buried in prose ("the right answer is Jay Wright"), distractors annotated with why they're wrong | Does instructor commentary leak into the question text? | Import as `MC`, stem clean, no commentary |
| 4 | Numbered options `1)–4)`, answer given as `(answer = #2)`; motto contains commas *and* quotes | Non-letter numbering, plus the CSV quoting rule | Import as `MC`, fields with commas wrapped in quotes |
| 5 | Note says the answer changes to Vic Maggitti Hall in Fall 2026 | Does it notice an answer with an expiry date? | **Flag** as time-dependent, encode the current answer |
| 6 | Bare `ESSAY` header, no options | Recognising a written-response item with no answer rows | Import as `WR`, block ends after `Difficulty` |
| 7 | "I think I lost the answer key for this one" | Will it invent a plausible answer? | **Flag.** Exclude; never guess. |
| 8 | Roman-numeral options `i.–iv.`, answer marked `→ ii` | Unusual numbering; also a type-preservation test | Import as `MC`; see the warning below |
| 9 | Checkbox notation `☑`/`☐`, "select all that apply", requested colors for each option, and Correct Selections scoring | Multi-select detection, 1/0 scoring, requested partial-credit scoring, and option-level HTML formatting | Import as `MS` with `Scoring,RightAnswers`, `Option,1` for correct choices, and each option as marked HTML |
| 10 | Numeric fill-in under a "BONUS QUESTION:" header, answer `3` with supporting detail | Short answer with multiple accepted forms, plus a setting CSV cannot encode | Import as `SA`, accept `3`, `three`, `Three`; **flag** a post-import to-do to enable Bonus (label stripped from the stem) |
| 11 | Algorithmic question; formula written as `round(n × p / 100)`, with a `×` and a banned `round()` | Two traps: a type CSV cannot represent at all, and a formula needing translation (`round()` belongs in the precision setting, `×` must become `*`) | **Flag** with a full spec for manual entry: formula `({n}*{p}/100)`, precision 0 decimal places not enforced, tolerance 1 units |

Also planted throughout, and not tied to any single question: inconsistent numbering across the document (`Question 1`, `#2`, `4)`, `5.`, `ESSAY`, `Q8`, `9 —`), and two pieces of instructor notes-to-self at the top and bottom ("Need to clean up for LMS upload before Friday", "still need to write 2 more multi-choice questions") that must not end up in any question.

### Two more issues to watch for

**Type drift on Q8.**
The source gives four ranges to pick from.
It is tempting to render it as short answer, since the answer is a number.
The skill should recognize not to do this, because `SA` turns it into a recall question, changing what the item measures and what students can score on it.
It also would force free-text variants (`7000`, `7,000`, `seven thousand`), with `7,000` containing a comma that breaks the import if it is not quoted.
The format is best kept as `MC`, despite the numerical answer choices.

**Silent omission.**
Three questions are left out of the CSV: Q7 and Q11 genuinely cannot be imported, and Q1 cannot be until the instructor says which of its two answer keys is the right one.
Leaving them out is correct; leaving them out *without saying so* is not.
The instructor ends up with a quiz that is three questions short and no indication why.
`tools/validate_csv.py` warns when a CSV has no FLAGS section for this reason.

## Automated run (Claude Code CLI)

This route also needs the skill [installed](../README.md#install) first: the CLI reads it from `.claude/skills`, not from this repo's `skills/` folder.

To run the whole thing without pasting anything, use the following commands from the **repo root**:

```bash
claude -p --permission-mode acceptEdits \
  "Use the quizwrangler-csv skill on examples/input/sample-questions-messy.txt \
   and write the result to test-run.csv"

diff test-run.csv examples/expected-output/sample-quiz.csv

python3 tools/validate_csv.py test-run.csv --strict
```

`--permission-mode acceptEdits` is needed to allow a headless run to save the output without access to an interactive "allow write?" prompt.

---

## QTI test file and expected output

The QTI example exercises the complete-package workflow:

```text
input/sample-qti-messy.txt             mixed source questions and a pool
input/sample-chart.png                 image used by one question
expected-output/sample-qti-package.zip expected complete package
```

Run it with a prompt along the lines of the following:

> Use the quizwrangler-qti skill to convert examples/input/sample-qti-messy.txt into one QTI ZIP. Keep all fixed questions and the mixed pool together, and include examples/input/sample-chart.png where requested.

The full expected package contains fixed examples of all ten supported item types and a pool that draws two candidates from four:

| Coverage | Expected handling |
|---|---|
| True/False and Multiple Choice | Preserve source order and key the stated answer |
| Multi-Select | Keep both correct selections and question feedback |
| Short Answer and Long Answer | Use a text box appropriate to each response |
| Matching and Ordering | Preserve the supplied relationships and correct sequence |
| Arithmetic | Copy the calculation formula into both the presentation field and the scoring rule; use `units` tolerance |
| Fill in the Blanks | Place the answer box inside the sentence |
| Multi-Short Answer | Use two boxes with any accepted answer allowed in either |
| Mixed pool | Keep Multiple Choice, True/False, Arithmetic, and Fill in the Blanks candidates in the same random section |
| Formatting and MathML | Carry meaningful formatting as escaped HTML; use plain MathML for equations |
| Embedded image | Copy the supplied PNG into `quizzing/` under a synthetic identifier and reference it from the item |
| Instructor note | Do not convert the final note-to-self into a question |

The committed packages are synthetic structural examples. They contain no course identifiers, export UUIDs, or platform submission prose.

## (Optional) Validate output

From the repository root, run the following script to check the ZIP for common errors that could prevent Brightspace from importing it:

```bash
python3 tools/validate_qti.py examples/expected-output/sample-qti-package.zip --strict
```
