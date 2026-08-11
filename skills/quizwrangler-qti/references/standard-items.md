# Standard question item patterns

Combine each type body with the common item wrapper in `package-profile.md`. Keep Multiple Choice, Multi-Select, and match text as escaped HTML. True/False labels are the plain-text exception described below.

## Contents

1. [True/False and Multiple Choice](#truefalse-and-multiple-choice)
2. [Multi-Select](#multi-select)
3. [Short Answer](#short-answer)
4. [Long Answer](#long-answer)
5. [Matching](#matching)
6. [Ordering](#ordering)

## True/False and Multiple Choice

Use `qmd_questiontype` `True/False` or `Multiple Choice`. Present one `response_lid` and one unique `response_label` per choice:

```xml
<presentation><flow><material><mattext texttype="text/html">{ESCAPED_STEM_HTML}</mattext></material><response_extension><d2l_2p0:display_style>2</d2l_2p0:display_style><d2l_2p0:enumeration>{ENUMERATION}</d2l_2p0:enumeration><d2l_2p0:grading_type>0</d2l_2p0:grading_type></response_extension><response_lid ident="QUES_{KEY}_LID" rcardinality="Single"><render_choice shuffle="{YES_OR_NO}">{CHOICE_LABELS}</render_choice></response_lid></flow></presentation>
<resprocessing>{ONE_CONDITION_PER_CHOICE}</resprocessing>
```

For Multiple Choice, Multi-Select, and True/False, honor the instructor's explicit enumeration request:

| Enumeration | Value |
| --- | --- |
| `1, 2, 3, ...` | `1` |
| `i, ii, iii, ...` | `2` |
| `I, II, III, ...` | `3` |
| `a, b, c, ...` | `4` |
| `A, B, C, ...` | `5` |
| No enumeration | `6` |

When no style is specified, use `6` for every choice question. Each Multiple Choice option uses HTML:

```xml
<flow_label class="Block"><response_label ident="QUES_{KEY}_A{N}"><flow_mat><material><mattext texttype="text/html">{ESCAPED_CHOICE_HTML}</mattext></material></flow_mat></response_label></flow_label>
```

For True/False, use exactly these two plain-text labels in this order. Do not wrap them in HTML:

```xml
<flow_label class="Block"><response_label ident="QUES_{KEY}_A1"><flow_mat><material><mattext texttype="text/plain">True</mattext></material></flow_mat></response_label></flow_label>
<flow_label class="Block"><response_label ident="QUES_{KEY}_A2"><flow_mat><material><mattext texttype="text/plain">False</mattext></material></flow_mat></response_label></flow_label>
```

Add one response condition per choice. Set the keyed choice to `100.000000000` and every distractor to `0.000000000`. Preserve the instructor's option order for Multiple Choice. Keep True before False for True/False; scoring, not order, marks the key. Use `shuffle="yes"` only when requested for Multiple Choice and `shuffle="no"` for True/False.

For explicitly requested partial credit, add one response condition per credited choice and set its percentage. Otherwise exactly one choice receives 100.

## Multi-Select

Use `qmd_questiontype` `Multi-Select`, `rcardinality="Multiple"`, and the same choice-label structure as Multiple Choice. Use the selected enumeration value from the table above.

```xml
<presentation><flow><material><mattext texttype="text/html">{ESCAPED_STEM_HTML}</mattext></material><response_extension><d2l_2p0:display_style>2</d2l_2p0:display_style><d2l_2p0:enumeration>{ENUMERATION}</d2l_2p0:enumeration><d2l_2p0:grading_type>{GRADING_TYPE}</d2l_2p0:grading_type></response_extension><response_lid ident="QUES_{KEY}_LID" rcardinality="Multiple"><render_choice shuffle="{YES_OR_NO}">{CHOICE_LABELS}</render_choice></response_lid></flow></presentation>
<resprocessing><outcomes><decvar vartype="Integer" defaultval="0" varname="que_score" minvalue="0" maxvalue="100" /><decvar vartype="Integer" defaultval="0" varname="D2L_Correct" minvalue="0" /><decvar vartype="Integer" defaultval="0" varname="D2L_Incorrect" minvalue="0" /></outcomes>{CHOICE_CONDITIONS}{FINAL_SCORE_CONDITIONS}</resprocessing>
```

Set `d2l_2p0:grading_type` to the requested mode: `0` All or Nothing, `1` Right Minus Wrong Selections, `2` Correct Selections, or `3` Correct Answers, Limited Selections. Right Minus Wrong Selections gives credit for correct selections and deducts a corresponding amount for incorrect selections. Correct Answers, Limited Selections awards the full question point value for each correct selection and limits learners to the number of correct answers.

For each correct choice, add to `D2L_Correct`; for each distractor, add to `D2L_Incorrect`. Select the complete final-score structure that corresponds to the requested mode. Do not improvise a new accumulator formula. Default to all-or-nothing; use Correct Selections, Correct Answers, Limited Selections, or right-minus-wrong only when requested.

## Short Answer

Use `qmd_questiontype` `Short Answer`:

```xml
<presentation><flow><material><mattext texttype="text/html">{ESCAPED_STEM_HTML}</mattext></material><response_str ident="QUES_{KEY}_STR" rcardinality="Single"><render_fib rows="1" columns="40" prompt="Box" fibtype="String"><response_label ident="QUES_{KEY}_ANS" /></render_fib></response_str></flow></presentation>
<resprocessing><outcomes><decvar vartype="Integer" minvalue="0" maxvalue="100" varname="Blank_1" /></outcomes>{ANSWER_CONDITIONS}</resprocessing>
```

Each accepted answer uses:

```xml
<respcondition><conditionvar><varequal respident="QUES_{KEY}_ANS" case="{YES_OR_NO}">{ESCAPED_ANSWER}</varequal></conditionvar><setvar action="Set">{PERCENT_9DP}</setvar></respcondition>
```

Default to case-insensitive matching. Use the regex extension from `advanced-items.md` only when requested.

## Long Answer

Use `qmd_questiontype` `Long Answer` and `qmd_computerscored` `no`:

```xml
<presentation><flow><material><mattext texttype="text/html">{ESCAPED_STEM_HTML}</mattext></material><response_extension><d2l_2p0:has_signed_comments>no</d2l_2p0:has_signed_comments><d2l_2p0:has_htmleditor>no</d2l_2p0:has_htmleditor><d2l_2p0:has_fileupload>no</d2l_2p0:has_fileupload></response_extension><response_str ident="QUES_{KEY}_STR" rcardinality="Multiple"><render_fib rows="{ROWS}" columns="80" prompt="Box" fibtype="String"><response_label ident="QUES_{KEY}_ANS"><material><mattext texttype="text/plain" /></material></response_label></render_fib></response_str></flow></presentation>
```

Default to 10 rows. Put a supplied model answer in question-level feedback only when the instructor wants it visible under the quiz's feedback settings; otherwise do not expose it to students.

## Matching

Use `qmd_questiontype` `Matching`. Present one `response_grp rcardinality="Single"` per prompt. Each `render_choice` repeats the same choice set, with unique prompt response identifiers. Score by comparing each prompt response to its correct choice identifier and use the profile's accumulator structure for the requested mode.

Required invariants:

- every prompt has one correct choice
- every referenced choice identifier exists
- choice identifiers are stable across all prompt dropdowns
- prompt and choice HTML is XML-escaped
- default to all-or-nothing; use equally weighted or right-minus-wrong only when requested

## Ordering

Use `qmd_questiontype` `Ordering`:

```xml
<presentation><flow><material><mattext texttype="text/html">{ESCAPED_STEM_HTML}</mattext></material><response_extension><d2l_2p0:grading_type>{GRADING_TYPE}</d2l_2p0:grading_type></response_extension><response_grp respident="QUES_{KEY}_O" rcardinality="Ordered"><render_choice shuffle="yes"><flow_label class="Block">{ORDERED_LABELS}</flow_label></render_choice></response_grp></flow></presentation>
```

List labels in the correct order. Give each label a unique identifier. The scoring conditions compare the first item to position 1, the second to position 2, and so on, then apply the profile's accumulator structure for the requested mode. Default to all-or-nothing.
