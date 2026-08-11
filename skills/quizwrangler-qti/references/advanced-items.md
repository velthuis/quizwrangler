# Advanced items, regex answers, and pools

Combine each body with the common wrapper in `package-profile.md`.

## Contents

1. [Arithmetic](#arithmetic)
2. [Fill in the Blanks](#fill-in-the-blanks)
3. [Multi-Short Answer](#multi-short-answer)
4. [Regex answers](#regex-answers)
5. [Random pools](#random-pools)

## Arithmetic

Use `qmd_questiontype` `Arithmetic`:

```xml
<presentation><flow><material><mattext texttype="text/html">{ESCAPED_STEM_HTML}</mattext><mat_extension>{VARIABLES}<formula>{FORMULA}</formula></mat_extension></material><response_num ident="QUES_{KEY}_NUM" rcardinality="Single" rtiming="no"><render_fib fibtype="Decimal" prompt="Box"><response_label ident="QUES_{KEY}_A1" /></render_fib></response_num><response_str ident="QUES_{KEY}_STR" rcardinality="Single" rtiming="no"><render_fib fibtype="String" prompt="Box"><response_label ident="QUES_{KEY}_A2" /></render_fib></response_str></flow></presentation>
<resprocessing><respcondition title="Single Condition"><respcond_extension><formula>{FORMULA}</formula><precision type="decimalplaces" d2l_2p0:precision_enforced="{YES_OR_NO}">{DECIMALS}</precision><tolerance type="{units|percent}">{TOLERANCE}</tolerance><units d2l_2p0:worth="{UNIT_PERCENT}" casesensitive="{YES_OR_NO}">{OPTIONAL_UNIT}</units></respcond_extension><conditionvar><other /></conditionvar><setvar action="Set">100</setvar></respcondition></resprocessing>
```

Each variable:

```xml
<variable name="{NAME}"><minvalue>{MIN}</minvalue><maxvalue>{MAX}</maxvalue><decimalplaces>{DECIMALS}</decimalplaces><step>{STEP}</step></variable>
```

Rules:

- Keep both formula strings byte-identical.
- Keep both `response_num` and `response_str`.
- Do not add an Arithmetic `<outcomes>` block or `varname` to its `setvar`.
- Use only the working subset: `+ - * / ^`, parentheses, `abs`, `cos`, `sin`, `tan`, `sqr`, `log`, `ln`, `pi`, and `e`.
- Translate `sqrt(x)` to `sqr(x)`. Move `round(x,n)` into answer precision `n`. Translate multiplication and division glyphs to `*` and `/`. Disclose translations.
- Reject or flag unknown functions. Check every sampled variable combination for division by zero, non-real results, overflow, and `sqr`/`log`/`ln` domain errors.
- Use `units` for an absolute numeric tolerance and `percent` for a relative tolerance.
- If the instructor asks for significant figures, build an Arithmetic item with percent tolerance and disclose that choice. Do not emit a separate Significant Figures item type.

## Fill in the Blanks

Use `qmd_questiontype` `Fill in the Blanks`. Alternate HTML materials and response boxes inside one presentation flow:

```xml
<presentation><flow><material><mattext texttype="text/html">{SEGMENT_1}</mattext></material><response_str ident="QUES_{KEY}_B1_STR" rcardinality="Single"><render_fib rows="1" columns="30" prompt="Box" fibtype="String"><response_label ident="QUES_{KEY}_B1_ANS" /></render_fib></response_str><material><mattext texttype="text/html">{SEGMENT_2}</mattext></material>{MORE_BLANKS_AND_SEGMENTS}</flow></presentation>
<resprocessing><outcomes>{ONE_DECVAR_PER_BLANK}</outcomes>{ANSWER_CONDITIONS}</resprocessing>
```

Add `<decvar vartype="Integer" minvalue="0" maxvalue="100" varname="Blank_N" />` for every blank. Give every blank unique `_BN_STR` and `_BN_ANS` identifiers. Each accepted answer for a blank gets a condition referencing that blank's answer identifier and the full weight assigned to that blank. Default to an equal split and case-insensitive matching.

## Multi-Short Answer

Use `qmd_questiontype` `Multi-Short Answer`:

```xml
<presentation><flow><material><mattext texttype="text/html">{ESCAPED_STEM_HTML}</mattext></material><response_str ident="QUES_{KEY}_STR" rcardinality="Single"><render_fib d2l_2p0:input_boxes="{BOX_COUNT}" rows="1" columns="40" prompt="Box" fibtype="String"><response_label ident="QUES_{KEY}_ANS" /></render_fib></response_str></flow></presentation>
<resprocessing>{ANSWER_CONDITIONS}</resprocessing>
```

Use one response block for all boxes. Each accepted answer may go in any box. Add one answer condition per accepted answer, all referencing the same `_ANS` identifier. Do not add `<outcomes>`. For three equal shares, use `33.330000000` for each condition; otherwise format percentages to nine decimals.

## Regex answers

For Short Answer, Fill in the Blanks, or Multi-Short Answer, add the extension immediately after `varequal`:

```xml
<conditionvar><varequal respident="{ANSWER_IDENT}" case="no">{XML_ESCAPED_PATTERN}</varequal><var_extension><d2l_2p0:answer_is_regexp>yes</d2l_2p0:answer_is_regexp></var_extension></conditionvar>
```

Preserve the instructor's regex. XML-escape it without changing its logic.

## Random pools

Place a pool section inside `CONTAINER_SECTION`:

```xml
<section title="{POOL_TITLE}" d2l_2p0:page="1" ident="RAND_{POOL_KEY}"><qtimetadata><qti_metadatafield><fieldlabel>qmd_numberofitems</fieldlabel><fieldentry>{DRAW_COUNT}</fieldentry></qti_metadatafield><qti_metadatafield><fieldlabel>qmd_weighting</fieldlabel><fieldentry>{POINTS_9DP}</fieldentry></qti_metadatafield></qtimetadata><sectionproc_extension><d2l_2p0:display_section_name>no</d2l_2p0:display_section_name><d2l_2p0:display_section_line>no</d2l_2p0:display_section_line><d2l_2p0:type_display_section>0</d2l_2p0:type_display_section></sectionproc_extension>{CANDIDATE_ITEMS}</section>
```

Pools may contain any mix of supported types. Use `OBJ_{POOL_KEY}` as every candidate item's `ident`. Keep candidate labels, response identifiers, and UUIDs unique. The draw count must be between 1 and the number of candidates. The pool weighting is the point value for each drawn question.

Do not split standard candidates into CSV when they belong to a QTI pool.
