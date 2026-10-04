# Formatting, equations, hints, feedback, and media

Use these rules for every item type.

## HTML

Preserve meaningful source formatting with conservative HTML:

- `<p>`, `<br>`, `<strong>`, `<em>`, `<u>`
- `<ul>`, `<ol>`, `<li>`
- `<sub>`, `<sup>`
- `<span style="color: #RRGGBB;">` when color is instructional
- accessible links with descriptive text

Do not invent decoration. Strip formatting used only to mark the answer key.

Put the HTML inside `<mattext texttype="text/html">` after XML-escaping it. For example:

```xml
<mattext texttype="text/html">&lt;p&gt;Water is H&lt;sub&gt;2&lt;/sub&gt;O.&lt;/p&gt;</mattext>
```

## Equations

Use plain MathML inside the HTML:

```html
<math xmlns="http://www.w3.org/1998/Math/MathML"><mfrac><mn>1</mn><mn>2</mn></mfrac></math>
```

Then XML-escape the complete HTML payload. Do not emit raw LaTeX as student-visible equation markup. Do not claim the imported equation will be editable in a particular editor.

For Arithmetic items, keep `{variable}` placeholders outside MathML markup so braces cannot be confused with formula substitution.

## Hints

Place a hint after `</presentation>` and before `<resprocessing>`:

```xml
<hint><hintmaterial><flow_mat><material><mattext texttype="text/html">{ESCAPED_HINT_HTML}</mattext></material></flow_mat></hintmaterial></hint>
```

Set the assessment wrapper's `hintswitch` to `yes` when at least one hint is present.

## Feedback

Place question-level feedback after `</resprocessing>`:

```xml
<itemfeedback ident="QUES_{ITEM_KEY}"><material><mattext texttype="text/html">{ESCAPED_FEEDBACK_HTML}</mattext></material></itemfeedback>
```

For choice-specific feedback, give each choice a unique feedback identifier, link the scoring condition with `<displayfeedback feedbacktype="Response" linkrefid="{FEEDBACK_ID}" />`, and add the corresponding `<itemfeedback ident="{FEEDBACK_ID}">`.

Set the assessment wrapper's `feedbackswitch` to `yes` when feedback exists.

## Images

Package supported raster images directly. If an image needs conversion, package
a PNG and disclose the conversion. Do not package SVG directly in this profile.

Copy each supplied image into the archive as:

```text
quizzing/_{FRESH_IMAGE_UUID}.{extension}
```

Reference that exact file from item material:

```xml
<matimage d2l_2p0:is_hidden="true" uri="quizzing\_{FRESH_IMAGE_UUID}.{extension}">_{FRESH_IMAGE_UUID}.{extension}</matimage>
```

The element text must repeat the packaged filename without the `quizzing/`
directory. Do not emit an empty or self-closing `matimage`.

For an inline HTML image, use a forward-slash relative source:

```html
<img src="quizzing/_{FRESH_IMAGE_UUID}.{extension}" alt="{MEANINGFUL_ALT_TEXT}">
```

Do not declare image files as manifest resources. Write concise alt text that conveys the image's relevant visual information without naming a correct option, stating the answer, or adding interpretation beyond what is visible. If adequate alt text would reveal the answer, flag the image for instructor-provided accessible alternative text.

Confirm every referenced media path exists in the ZIP. Preserve the original bytes and extension unless conversion is necessary and explicitly disclosed.
