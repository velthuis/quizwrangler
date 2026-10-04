# QuizWrangler

**Turns messy questions into clean Brightspace imports.**

Instructors often keep questions in old notes, Word documents, PDFs, or spreadsheets, with answers marked inconsistently and numbering that drifts. QuizWrangler converts them into files that Brightspace (D2L) imports directly, and it flags potential issues such as contradictory answer keys, missing keys, and important notes left by the instructor.

## Skills

| Skill | Output | Use it for |
|---|---|---|
| `quizwrangler-csv` | A `.csv` file | An ordinary bank of multiple choice, true/false, written response, short answer, multi-select, matching, and ordering questions, ideal for adding questions directly to the Question Library |
| `quizwrangler-qti` | A QTI `.zip` package | A complete quiz, including random question pools, embedded images, and advanced question types CSV imports cannot handle: Arithmetic, Fill in the Blanks, and Multi-Short Answer |

Both skills preserve meaningful formatting, including HTML, color, subscripts, superscripts, and equations.

## How to use it

Paste your questions underneath a line like one of these:

> Use the quizwrangler-csv skill on the questions below.

> Use the quizwrangler-qti skill to turn these questions into a complete QTI quiz package.

You can also attach the questions as a file. Check every flagged question before importing: neither skill is designed to catch whether an answer key is factually incorrect.

To import the result, use **Question Library → Import → Upload a File** or **New Quiz → Add Existing → Upload a File** for a CSV, and **Course Admin → Import/Export/Copy Components** for a QTI package.

## What the plugin runs

Both skills are written instructions rather than programs: Claude reads your questions and creates the CSV or ZIP file itself, using its built-in file creation. The QTI skill also includes a Python validator script (standard library only) that Claude runs while building the package. It checks the finished ZIP file for common errors that could prevent Brightspace from importing it.

> **Privacy note.**
> Check your institution's policy on what information may be sent to which AI tools.

## Troubleshooting

- **A question is missing from the output.** Check the flags at the end of the reply or the file. Questions with a contradictory or missing answer key, or a type the format cannot carry, are left out on purpose. Fix the source question and convert it again.
- **The skill doesn't run, or no file is created.** In Cowork or the Claude apps, turn on **Code execution and file creation** in settings.
- **Brightspace rejects the file or imports fewer questions than expected.** Check that you used the correct import menu for your format, listed above. Then describe the error in the chat and ask for a corrected file.
- **Still stuck?** Open an issue on [GitHub](https://github.com/velthuis/quizwrangler/issues) with the error and a sample of the source questions. Leave out any private information.
