# QuizWrangler

**Turns messy questions into clean Brightspace imports.**

| Skill | Input | Output |
|---|---|---|
| **`quizwrangler-csv`** | Questions in a Word document, PDF, spreadsheet, or pasted text | A Brightspace-ready `.csv` with support for: multiple choice, true/false, written response, short answer, multi-select, matching, ordering |

Question types the CSV format cannot carry (i.e., algorithmic/calculated, fill-in-the-blanks, multi-short-answer) are flagged with a spec you can enter in Brightspace's question editor by hand.

---

## What it does

Importing quizzes into Brightspace requires precisely formatted files.
However, instructors may have accumulated questions in different formats, such as notes from a previous term, with answers marked inconsistently, or with inconsistent numbering.
Additionally, the skill can accommodate formatting preferences, such as font size, font color, or embedding equations, which can be a tedious manual process.

This repo contains a prompt that you run with your preferred AI assistant. `quizwrangler-csv` readies the questions for import, and flags the cases the CSV importer cannot represent (algorithmic questions with randomized values per student, fill-in-the-blanks, and multi-short-answer questions) with instructions for manual entry.

The skill also flags potential issues in the questions such as contradictory answer keys, missing keys, and important notes left by the instructor.

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

The skill converts questions, but it doesn't write them. If you need questions too, you can first ask your AI assistant to write them for you, which you can then check. For example, you can ask: 
> "Draft 10 multiple-choice questions on photosynthesis for an intro biology course, four options each, mark the correct answer."

While you could also combine both steps in one prompt ("write the questions, then convert them for Brightspace"), the two-step approach is the better habit as it puts a checkpoint between writing the questions and importing the file.

---

## Install

The skill is a plain Markdown file.
How you load it depends on your assistant; pick the one you use.

- On **Claude Desktop, claude.ai, or ChatGPT** you only need the ready-made Release ZIP, nothing from the repo. 
Download `quizwrangler-csv.zip` from [Releases](https://github.com/velthuis/quizwrangler/releases), which is already in the structure the uploader expects.
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
<summary><b>Claude Desktop or claude.ai (no command line)</b></summary>

1. Turn on **Settings → Capabilities → Code execution and file creation**; skills won't run without it.
   *(On Team or Enterprise plans an owner enables this in Organization settings.)*
2. In settings, navigate to **Skills** (under Customize), click **Add**, then **Upload a skill**.
3. Pick `quizwrangler-csv.zip`. (Selecting [`SKILL.md`](https://github.com/velthuis/quizwrangler/blob/main/skills/quizwrangler-csv/SKILL.md) from the quizwrangler-csv folder instead can work as well).

Uploaded skills are private to your account and can be toggled on and off in the skills list.

</details>

<details>
<summary><b>ChatGPT</b></summary>

ChatGPT supports the same skill format, so the Release ZIP above works unchanged.

1. Go to [https://chatgpt.com/skills](https://chatgpt.com/skills), click **+**, then **Create skill → Upload a skill**.
2. Pick `quizwrangler-csv.zip`.
3. ChatGPT scans an uploaded skill before enabling it; most become available as soon as the scan finishes.

On Business or Enterprise workspaces an admin may need to enable them first; if you don't see a Skills option, check with your IT group.


</details>

<details>
<summary><b>Claude Code</b></summary>

Copy the skill folder named `quizwrangler-csv` into your skills directory. Two locations work:

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

</details>

<details>
<summary><b>Codex CLI</b></summary>

OpenAI's Codex CLI reads the same skill format from its own directories: `~/.codex/skills` (user-level, available everywhere) or `.codex/skills` inside a project folder (that folder only). Copy the skill folder named `quizwrangler-csv` there.

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

</details>

<details>
<summary><b>Microsoft 365 Copilot</b></summary>

Copilot Chat (Basic) has no skills folder; each skill becomes a saved **agent** you can reuse.

1. Sign in to your institution's Microsoft 365 portal.
2. Open **Copilot** in **Work** mode (look for **Copilot with internal data protection** badge).
3. In the Copilot sidebar, hover over **Agents** and click **+ New agent**.
   Open [`skills/quizwrangler-csv/SKILL.md`](https://github.com/velthuis/quizwrangler/blob/main/skills/quizwrangler-csv/SKILL.md), copy everything *below* the closing `---` of the frontmatter block, and paste it as the agent's instructions.
   (The frontmatter is specific to Code and Cowork environments; Copilot has no use for it.)
4. Name the agent, save it, then upload or paste your questions.

Agent creation may require a Copilot license tier your institution has to enable; if you can't find it, ask your IT group.

</details>

<details>
<summary><b>Any other assistant</b></summary>

The skill is a portable system prompt with nothing platform-specific in the body.
Paste its text as a system prompt, custom instruction, or project instruction anywhere and it will work; delete the YAML frontmatter, which exists only so Claude Code and Codex can find the skill by name or description.

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

### The full test file

The [`examples/`](examples/) directory holds a more extensive run to test the skill:

- `input/sample-questions-messy.txt`: a deliberately messy question document
- `expected-output/sample-quiz.csv`: what the skill should produce from it
- [`README.md`](examples/README.md): how to run it, plus what each planted problem is testing

The input plants five traps: a question with two contradicting answer keys, an answer that expires in Fall 2026, a lost answer key, a bonus label CSV cannot encode, and an algorithmic question CSV can't express.
A correct run produces eight question blocks and five flags: three questions excluded outright, plus two converted but flagged (the expiring answer, and the bonus question with a post-import to-do).
Eleven clean questions with no flags means the skill guessed, which is exactly what the test file exists to detect.
See the [examples README](examples/README.md) for step-by-step instructions and the full trap key.

---

## Importing to Brightspace

The generated CSV can be uploaded through either of two menus, depending on where you want the questions to land:

| Import through | Questions land in |
|---|---|
|  **New Quiz → Add Existing → Upload a File** | The quiz you're building |
|  **Question Library → Import → Upload a File** | The Question Library |

Import into the Question Library if you want the questions reusable across quizzes; questions imported into a single quiz are not in the Question Library automatically.

Do not upload the CSV through **Course Admin → Import/Export/Copy Components**: that importer only accepts course packages, and the CSV upload would fail.

---

## Features & Limitations

**Correctness:** Neither the skill nor the validator can tell whether an answer key is *true*, only whether the file is well-formed.

**CSV import cannot represent** algorithmic/calculated, fill-in-the-blanks, or multi-short-answer questions.
Brightspace's own editor supports all three; they just can't be batch-imported through CSV.
The skill flags them with a spec you can enter in the editor by hand.

**Formatting in your source is read, not discarded.**
Bold or highlighting that marks the correct answer sets the answer key and is then dropped, while formatting that belongs to the question itself is carried through into the CSV.
This works whether the questions arrive as a Word document, a PDF, a spreadsheet, or text pasted straight into the chat.

Everything else the CSV format does support is covered: 
- seven question types,
- per-question and per-option feedback,
- hints,
- HTML formatting (bold, lists, sub- and superscripts) in question text, options, hints, and feedback,
- equations, written as MathML, in any of those same fields,
- images,
- partial credit,
- regular-expression answer matching,
- `EquallyWeighted`, `AllOrNothing`, and `RightMinusWrong` scoring modes.

**Formulas in flagged algorithmic specs use only what D2L's question editor accepts:** `+ - * / ^`, parentheses, and the documented functions `abs`, `cos`, `sin`, `tan`, `sqr` (not `sqrt`!), `log` (base 10), `ln`, and the constants `pi`/`e`.
Anything else fails in the editor, including any rounding function; rounding is the precision setting's job instead.

**Brightspace instances may differ.**
There is no guarantee that all features will work on every institution's D2L implementation.

---

## Bonus: validate before you upload

A small Python script checks a generated CSV before you hand it to Brightspace.
It is optional but useful: Brightspace reports import problems vaguely or not at all, and a malformed CSV can import "successfully" with questions missing or mis-scored, which can then go unnoticed.

[`tools/validate_csv.py`](tools/validate_csv.py) catches unquoted commas, multi-select rows scored 100/0 instead of 1/0 (the most common import failure), multiple correct answers on a single-answer question, smart quotes, and malformed block structure.

macOS or Linux:

```bash
python3 tools/validate_csv.py my-quiz.csv
```

Windows (PowerShell or Command Prompt), where the interpreter is usually `python`:

```powershell
python tools\validate_csv.py my-quiz.csv
```

Python 3.8+, standard library only, nothing to install.
If Windows opens the Microsoft Store when you type `python`, install Python from [python.org](https://www.python.org/downloads/) and tick **Add python.exe to PATH** during setup.

Exit code 0 means clean; `--strict` turns warnings into errors.


---

## Background

QuizWrangler grew out of **Beyond Prompts: Reusable AI Workflows for Teaching**, a session I presented at the VITAL Teaching & Learning Strategies Program at Villanova University in May 2026.

Further reading: Ethan Mollick, [*Real AI Agents and Real Work*](https://www.oneusefulthing.org/p/real-ai-agents-and-real-work).

## License

[MIT](LICENSE).
Use it, fork it, adapt it for your institution.
If you cite it, see [CITATION.cff](CITATION.cff).
