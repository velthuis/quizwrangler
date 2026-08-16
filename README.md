# QuizWrangler

**Turns messy questions into clean Brightspace imports.**

| Skill | Input | Output |
|---|---|---|
| **`quizwrangler-csv`** | Questions in a Word document, PDF, spreadsheet, or pasted text | A Brightspace-ready `.csv` with support for: multiple choice, true/false, written response, short answer, multi-select, matching, ordering |
| **`quizwrangler-qti`** | A complete quiz, mixed question set, or pool in the same source formats | A QTI `.zip` containing standard and advanced types, mixed pools, HTML, MathML, and embedded images |

Use CSV for an ordinary standard-question bank, especially when the questions should land in the Question Library. Use QTI for a complete quiz package, a pool, an embedded image, or a mix of standard and advanced types.

---

## What it does

Importing quizzes into Brightspace requires precisely formatted files.
However, instructors may have accumulated questions in different formats, such as notes from a previous term, with answers marked inconsistently, or with inconsistent numbering.
The skills also preserve meaningful formatting, including HTML, color, subscripts, superscripts, and equations.

This repo contains two reusable prompts. `quizwrangler-csv` readies standard questions for direct upload. `quizwrangler-qti` builds a complete ZIP and handles the same standard types plus Arithmetic, Fill in the Blanks, Multi-Short Answer, and random pools.

Both skills flag potential issues such as contradictory answer keys, missing keys, and important notes left by the instructor.

### Example

Messy input from a set of notes:

```
4) Villanova's motto "Veritas, Unitas, Caritas" translates to:
1) Faith, Hope, Love
2) Truth, Unity, Love
3) Peace, Justice, Mercy
4) Wisdom, Knowledge, Understanding
(answer = #2)
```

Importable output, with the comma-bearing fields correctly quoted:

```
NewQuestion,MC,,,
Title,Villanova Motto Translation,,,
QuestionText,"Villanova's motto ""Veritas, Unitas, Caritas"" translates to:",,,
Points,1,,,
Difficulty,1,,,
Option,0,"Faith, Hope, Love",,
Option,100,"Truth, Unity, Love",,
Option,0,"Peace, Justice, Mercy",,
Option,0,"Wisdom, Knowledge, Understanding",,
,,,,
```

When a question cannot be converted reliably, the skill flags it instead of guessing:

```
//Q1 (Villanova founding year) - Contradictory answer key. The option list marks "*c. 1859" but the
//  instructor note below it reads "Correct answer: B" (1842). Two different answers; not guessed.
//  Instructor must confirm which is intended before this question can be imported.
```

This refusal is deliberate to avoid problems and allow the instructor to fix the question in time.

### If you don't have questions yet

The skills convert questions, but they don't write them. If you need questions too, you can first ask your AI assistant to write them for you, which you can then check. For example, you can ask:
> "Draft 10 multiple-choice questions on photosynthesis for an intro biology course, four options each, mark the correct answer."

While you could also combine both steps in one prompt ("write the questions, then convert them for Brightspace"), the two-step approach is the better habit as it puts a checkpoint between writing the questions and importing the file.

---

## Install

Each skill is a folder containing Markdown instructions and, where needed, bundled references.
How you load it depends on your assistant; pick the one you use.

- On **Claude Desktop, Cowork, claude.ai, or ChatGPT** you only need the ready-made Release ZIPs, nothing from the repo.
Download `quizwrangler-csv.zip` and `quizwrangler-qti.zip` from [Releases](https://github.com/velthuis/quizwrangler/releases), which are already in the structure the uploader expects.
You can then add the skill to your assistant by uploading the ZIP in the app's skill settings; the exact steps for each app follow below.

> ⚠️ **Don't use GitHub's green "Code → Download ZIP" button for this.**
> That wraps the whole repository in a `quizwrangler-main/` folder, which the skill uploader will reject.
> Use the Release file instead.


- For every other path, you will need to obtain the skill folder inside `skills/` by one of two methods:

1. Clone the repo
```bash
git clone https://github.com/velthuis/quizwrangler.git
```
2. Click **Code → Download ZIP** on GitHub and unzip it

### Platform-specific instructions

<details>
<summary><b>Claude Desktop, Cowork, or claude.ai (no command line)</b></summary>

1. Turn on **Settings → Capabilities → Code execution and file creation**; skills won't run without it.
   *(On Team or Enterprise plans an owner enables this in Organization settings.)*
2. In settings, navigate to **Skills** (under Customize), click **Add**, then **Upload a skill**.
3. Pick `quizwrangler-csv.zip`.
4. Repeat for `quizwrangler-qti.zip`.

Uploaded skills are private to your account and can be toggled on and off in the skills list.
The same uploaded skill is available in Claude chat and Cowork. The QTI ZIP includes its own standard-library validator, so it does not depend on a checkout of this repository.

</details>

<details>
<summary><b>ChatGPT</b></summary>

ChatGPT can upload the QuizWrangler Release ZIPs without modification.

1. Open [Skills in ChatGPT](https://chatgpt.com/skills). If that link does not open the Skills page, use **Plugins → Skills** in the sidebar instead.
   Select **Create**, then **Upload**.
2. Pick `quizwrangler-csv.zip`, then repeat for `quizwrangler-qti.zip`.
3. ChatGPT scans an uploaded skill before enabling it; most become available as soon as the scan finishes.

On Business or Enterprise workspaces an admin may need to enable them first; if you don't see a Skills option, check with your IT group.


</details>

<details>
<summary><b>Claude Code</b></summary>

Copy both folders inside `skills/` into your skills directory. Two locations work:

- **User-level**: `~/.claude/skills` in your home folder makes skills available in every folder you run Claude Code from. Use this if you expect to use the skill broadly.
- **Project-level**: `.claude/skills` inside any one folder makes them available only when Claude Code runs in that folder. This is useful if you keep teaching material in one place and prefer a narrower scope.

User-level install, macOS or Linux (Terminal):

```bash
mkdir -p ~/.claude/skills
cp -r quizwrangler/skills/* ~/.claude/skills/
```

User-level install, Windows (PowerShell):

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.claude\skills"
Copy-Item -Recurse -Force .\quizwrangler\skills\* "$HOME\.claude\skills\"
```

For a project-level install, use `<your folder>/.claude/skills` as the destination instead.

Without a terminal, copy the skill folder by hand into `.claude\skills` in your home folder (`C:\Users\<you>\.claude\skills` on Windows, `/Users/<you>/.claude/skills` on macOS), creating it if it doesn't exist.
Note that File Explorer or Finder may hide folders starting with a dot. 
Keep each complete skill folder together. In particular, `quizwrangler-qti/references/` and `quizwrangler-qti/scripts/` are required parts of the QTI skill.

</details>

<details>
<summary><b>Codex CLI</b></summary>

OpenAI's Codex CLI loads QuizWrangler skill folders from its own directories: `~/.codex/skills` (user-level, available everywhere) or `.codex/skills` inside a project folder (that folder only). Copy both skill folders there.

User-level install, macOS or Linux (Terminal):

```bash
mkdir -p ~/.codex/skills
cp -r quizwrangler/skills/* ~/.codex/skills/
```

User-level install, Windows (PowerShell):

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.codex\skills"
Copy-Item -Recurse -Force .\quizwrangler\skills\* "$HOME\.codex\skills\"
```

When a skill includes `agents/openai.yaml`, it supplies OpenAI-facing display metadata and a default prompt. `SKILL.md`, references, and scripts define the skill's behavior.

</details>

<details>
<summary><b>Microsoft 365 Copilot</b></summary>

These instructions target the standard Microsoft 365 Copilot configuration available at many universities. It uses saved agents rather than skill folders. Create separate CSV and QTI agents with concise instructions that fit your institution's needs. Agent Builder limits instructions to 8,000 characters, so the complete QuizWrangler skill files are not intended to be pasted in directly. Copilot Studio and premium plans may provide additional options.

For either agent, under **Configure → Capabilities**, turn on **Create documents, charts, and code**. This lets the CSV agent create a downloadable `.csv` file and lets the QTI agent create a ZIP and run Python checks.

For a CSV agent, add D2L's [Import questions into the Question Library guide](https://community.d2l.com/brightspace/kb/articles/5039-import-questions-into-the-question-library) as a web knowledge source. Instruct the agent to create a downloadable `.csv` file, flag ambiguity rather than guessing, and follow the Brightspace CSV format.

For a QTI agent:

1. In Copilot Agent Builder, create a new agent and give it concise package-generation instructions.
2. Add these four public QuizWrangler knowledge pages as web knowledge sources:
   - [QTI package profile](https://velthuis.github.io/quizwrangler/qti-package-profile/)
   - [QTI standard item patterns](https://velthuis.github.io/quizwrangler/qti-standard-items/)
   - [QTI advanced item patterns](https://velthuis.github.io/quizwrangler/qti-advanced-items/)
   - [QTI formatting and media](https://velthuis.github.io/quizwrangler/qti-formatting-media/)
3. Keep the instructions focused on the agent's role and workflow. Use the knowledge pages for QTI format details and item patterns, not as a substitute for the agent's instructions.

Agent creation and web knowledge sources may require a Copilot license or administrator approval. If you cannot create an agent or add the pages, ask your IT group.

</details>

<details>
<summary><b>Any other assistant</b></summary>

The CSV skill can be pasted as a standalone system prompt after removing its YAML frontmatter. The QTI skill uses bundled reference files, so use its complete folder or Release ZIP in an environment that supports skill bundles.

</details>


> **Privacy note.**
> Check your institution's policy on what information may be sent to which AI tools, and use an enterprise-protected tier when in doubt.

---

## Try it

For a first test, once the skill is installed, paste this prompt into your assistant as one message:

```
Use the quizwrangler-csv skill on the questions below.

Which planet is closest to the sun?
a. Venus
b. Mercury *
c. Mars

T/F: Water boils at 100 degrees Celsius at sea level. (true)

Name the process by which plants convert sunlight into chemical energy.
Answer: photosynthesis
```

You should get back a small CSV with three question blocks (multiple choice, true/false, short answer), ready to save and upload to Brightspace.

To test the complete-package path, use the following prompt:

```text
Use the quizwrangler-qti skill to build one QTI ZIP containing a pool consisting of these questions, which draws one at random:

1. T/F: Water freezes at 0 degrees Celsius. (true)
2. Arithmetic: Double {n}; n is an integer from 2 through 10; formula n*2.
3. Arithmetic: Add 5 to {n}; n is an integer from 2 through 10; formula n+5.
```

The result should be a ZIP with a pool containing the three questions and drawing one of them, ready for the Course Admin import path below.

### The full test file

The [`examples/`](examples/) directory holds more extensive runs for both skills:

- `input/sample-questions-messy.txt`: a deliberately messy question document
- `expected-output/sample-quiz.csv`: what the skill should produce from it
- `input/sample-qti-messy.txt`: a complete mixed quiz with all supported types and a mixed pool
- `expected-output/sample-qti-package.zip`: the corresponding synthetic QTI package
- [`README.md`](examples/README.md): how to run it, plus what each planted problem is testing

The CSV input includes several deliberate traps: a question with two contradicting answer keys, an answer that expires in Fall 2026, a lost answer key, a bonus label CSV cannot encode, and an algorithmic question CSV can't express. A correct CSV run produces eight question blocks and five flags. See the [examples README](examples/README.md) for the individual traps and expected handling.

---

## Importing to Brightspace

Use the menu that matches the generated format:

| Format | Import through | Result |
|---|---|---|
| CSV | **New Quiz → Add Existing → Upload a File** | Questions in the quiz being built |
| CSV | **Question Library → Import → Upload a File** | Reusable Question Library questions |
| QTI ZIP | **Course Admin → Import/Export/Copy Components** | A complete quiz containing fixed questions and pools |

For immediate reuse across quizzes, import questions directly into the Question Library. Questions first imported into a quiz can also be added to the Question Library later.

---

## Features & Limitations

**QTI covers the complete supported set:** True/False, Multiple Choice, Multi-Select, Short Answer, Long Answer, Matching, Ordering, Arithmetic, Fill in the Blanks, and Multi-Short Answer. A random pool can mix these types in one ZIP. Requests for significant-figure grading are represented as Arithmetic with percent tolerance rather than a separate item type.

**Formatting in your source is read, not discarded.**
Bold or highlighting that marks the correct answer sets the answer key and is then dropped, while formatting that belongs to the question itself is carried through into the CSV.
This works whether the questions arrive as a Word document, a PDF, a spreadsheet, or text pasted straight into the chat.

Everything else the CSV format does support is covered: 
- seven question types,
- per-question and per-option feedback,
- hints,
- HTML formatting (bold, lists, sub- and superscripts) in question text, options, hints, and feedback,
- equations, written as MathML, in any of those same fields,
- partial credit,
- various scoring modes,
- regular-expression answer matching.

### Limitations

**Correctness:** Neither the skill nor the validator can tell whether an answer key is *factually correct*, only whether the file is well-formed.

**CSV import cannot represent** Arithmetic, Fill in the Blanks, or Multi-Short Answer. The CSV skill flags them with a structured spec that `quizwrangler-qti` can package.

**Arithmetic formulas are limited to the following operations:** `+ - * / ^`, parentheses, `abs`, `cos`, `sin`, `tan`, `sqr`, `log`, `ln`, `pi`, and `e`. Rounding is represented by the precision setting rather than a formula function.

**Brightspace instances may differ.** There is no guarantee that all features will work on every institution's D2L implementation.

---

## Bonus: validate before you upload

A pair of Python scripts checks generated CSV and QTI files before you hand them to Brightspace.
It is optional but useful: Brightspace reports import problems vaguely or not at all, and a malformed CSV can import "successfully" with questions missing or mis-scored, which can then go unnoticed.

[`tools/validate_csv.py`](tools/validate_csv.py) catches unquoted commas, multi-select rows scored 100/0 instead of 1/0, multiple correct answers on a single-answer question, smart quotes, and malformed block structure.

[`tools/validate_qti.py`](tools/validate_qti.py) checks archive layout, BOMs, XML, cross-file orgunit identifiers, media references, pool structure, item response shapes, and Arithmetic formulas.

macOS or Linux:

```bash
python3 tools/validate_csv.py my-quiz.csv
python3 tools/validate_qti.py my-quiz.zip
```

Windows (PowerShell or Command Prompt), where the interpreter is usually `python`:

```powershell
python tools\validate_csv.py my-quiz.csv
python tools\validate_qti.py my-quiz.zip
```

Python 3.8+, standard library only, nothing to install.
If Windows opens the Microsoft Store when you type `python`, install Python from [python.org](https://www.python.org/downloads/) and tick **Add python.exe to PATH** during setup.

Exit code 0 means clean; `--strict` turns warnings into errors.

---

## External references

- [Brightspace Quiz developer reference](https://docs.valence.desire2learn.com/res/quiz.html): quiz fields, question types, enumerations, and grading options.
- [Creating Question Library questions](https://community.d2l.com/brightspace/kb/articles/2800-creating-question-library-questions): authoring choices for Brightspace question types.
- [Import questions into the Question Library](https://community.d2l.com/brightspace/kb/articles/5039-import-questions-into-the-question-library): CSV format and upload workflow.
- [Import, export, or copy course components](https://community.d2l.com/brightspace/kb/articles/16788-import-export-or-copy-course-components): package import workflow.
- [1EdTech QTI 1.2 information model](https://www.imsglobal.org/question/qtiv1p2/imsqti_asi_infov1p2.html): the assessment, section, item, and response model behind QTI 1.2.
- [Brightspace Quiz Question Converter](https://community.d2l.com/brightspace/kb/articles/4161-quiz-question-converter): D2L's CSV question-bank conversion tool.

## Background

QuizWrangler grew out of **Beyond Prompts: Reusable AI Workflows for Teaching**, a session I presented at the VITAL Teaching & Learning Strategies Program at Villanova University in May 2026.

For a broader discussion on leveraging AI tools, particularly in academia, I recommend checking out Ethan Mollick's article <a href="https://www.oneusefulthing.org/p/real-ai-agents-and-real-work" target="_blank">*Real AI Agents and Real Work*</a>.

## License

[MIT](LICENSE).
Use it, fork it, adapt it for your institution.
If you cite it, see [CITATION.cff](CITATION.cff).

## Trademark notice

QuizWrangler is an independent project. It is not affiliated with, sponsored,
endorsed, or approved by D2L Corporation.

All D2L marks are trademarks of D2L Corporation. Please visit
[D2L.com/trademarks](https://www.d2l.com/trademarks/) for a list of D2L marks.
