# Test file and worked example

This section describes an application of the skill over a **deliberately broken** test file.
It is useful for checking that the skill is loaded and behaves as expected before you point it at real course material. 
The skill should convert a messy list of questions into **an importable CSV file** and **flag any problems** it finds instead of quietly guessing at them.

## Files

```
input/sample-questions-messy.txt    11 questions, deliberately messy
expected-output/sample-quiz.csv     8 CSV question blocks + a 5-entry FLAGS section
```

## Run it

With the skill [installed](../README.md#install), ask your assistant to use the `quizwrangler-csv` skill:

> Use the quizwrangler-csv skill on the questions below.

and paste the contents of `input/sample-questions-messy.txt` underneath.
(In some environments, you can also type `/quizwrangler-csv` and paste the questions after it.)

See [the test file](#the-test-file-what-each-planted-problem-tests) section for details on what each one of the 11 proposed quiz questions tests.

### Expected output

You should get **8 question blocks and a `//FLAGS:` section** (covering Q1, Q5, Q7, Q10, and Q11).
Q5 and Q10 are converted but still flagged: Q5's answer expires in Fall 2026, and Q10's bonus label is not a CSV field.
Q1, Q7, and Q11 are left out of the CSV entirely: two contradicting answer keys, a missing answer key, and a question type CSV cannot represent.
Q11's flag carries a full spec the instructor can enter by hand in Brightspace's question editor.

Compare your result against `expected-output/sample-quiz.csv`.

## (Optional) Validate output

Save the assistant's output to a file, then check that it is well-formed. Run this from the repo root, using the name you saved it under:

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
| 7 | "I think I lost the answer key for this one", plus a request to color the answer text | Will it invent a plausible answer? And does the formatting request distract it from the missing key? | **Flag.** Exclude; never guess. Carry the colored-text request in the flag for when the question is re-created. |
| 8 | Roman-numeral options `i.–iv.`, answer marked `→ ii` | Unusual numbering; also a type-preservation test | Import as `MC`; see the warning below |
| 9 | Checkbox notation `☑`/`☐`, "select all that apply" | Multi-select detection, and the 1/0 scoring rule | Import as `MS` with `Option,1`, **not** `100` |
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

`--permission-mode acceptEdits` is required to allow a headless run to save the output without access to an interactive "allow write?" prompt.
