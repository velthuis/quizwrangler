# QTI package profile

Use this profile for every package. Treat it as a deliberately narrow, minimal interoperability profile, not a complete description of every QTI package.

## Contents

1. [Archive layout](#archive-layout)
2. [Manifest (`imsmanifest.xml`)](#manifest-imsmanifestxml)
3. [Org unit configuration (`orgunitconfig/orgunitconfig.xml`)](#org-unit-configuration-orgunitconfigorgunitconfigxml)
4. [Quiz definition (`quiz.xml`)](#quiz-definition-quiz-xml)
5. [Common item metadata](#common-item-metadata)
6. [Identifiers and escaping](#identifiers-and-escaping)
7. [Final checks](#final-checks)

## Archive layout

Put these entries at the archive root:

```text
imsmanifest.xml
quiz.xml
orgunitconfig/orgunitconfig.xml
```

Add `quizzing/` files only when the quiz embeds media. Write every XML file as UTF-8 with BOM bytes `EF BB BF`. Do not wrap the entries in a parent directory.

## Manifest (`imsmanifest.xml`)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="D2L_{MANIFEST_KEY}" xmlns:d2l_2p0="http://desire2learn.com/xsd/d2lcp_v2p0" xmlns:imsmd="http://www.imsglobal.org/xsd/imsmd_rootv1p2p1" xmlns="http://www.imsglobal.org/xsd/imscp_v1p1">
  <metadata><imsmd:lom><imsmd:general><imsmd:title><imsmd:langstring xml:lang="en-us">{QUIZ_TITLE}</imsmd:langstring></imsmd:title><imsmd:language>en-us</imsmd:language></imsmd:general></imsmd:lom></metadata>
  <resources>
    <resource identifier="{ORGUNIT_UUID}" type="webcontent" d2l_2p0:material_type="orgunitconfig" href="orgunitconfig\orgunitconfig.xml" title="" />
    <resource identifier="res_quiz" type="webcontent" d2l_2p0:material_type="d2lquiz" href="quiz.xml" title="{QUIZ_TITLE}" />
  </resources>
</manifest>
```

Keep the backslash in the orgunit `href`. Keep the quiz filename and resource identifier consistent across the manifest and wrapper.

## Org unit configuration (`orgunitconfig/orgunitconfig.xml`)

Save this as `orgunitconfig/orgunitconfig.xml`. Use the same `{ORGUNIT_UUID}` as the manifest resource:

```xml
<?xml version="1.0" encoding="utf-8"?>
<orgunit identifier="{ORGUNIT_UUID}" />
```

## Quiz definition (`quiz.xml`)

Use this minimal quiz definition and insert all fixed items and pool sections at `{CONTENT}`:

```xml
<?xml version="1.0" encoding="UTF-8"?><questestinterop xmlns:d2l_2p0="http://desire2learn.com/xsd/d2lcp_v2p0"><assessment d2l_2p0:id="1" title="{QUIZ_TITLE}" ident="res_quiz"><assessmentcontrol hintswitch="{HINT_SWITCH}" feedbackswitch="{FEEDBACK_SWITCH}" /><section ident="CONTAINER_SECTION">{CONTENT}</section></assessment></questestinterop>
```

Set `hintswitch="yes"` when any item has a hint and `feedbackswitch="yes"` when any item has feedback.

## Common item metadata

Start every item with:

```xml
<item ident="OBJ_{ITEM_KEY}" label="QUES_{ITEM_KEY}" d2l_2p0:page="1" title="{SHORT_TITLE}">
  <itemmetadata><qtimetadata>
    <qti_metadatafield><fieldlabel>qmd_computerscored</fieldlabel><fieldentry>{COMPUTER_SCORED}</fieldentry></qti_metadatafield>
    <qti_metadatafield><fieldlabel>qmd_questiontype</fieldlabel><fieldentry>{QUESTION_TYPE}</fieldentry></qti_metadatafield>
    <qti_metadatafield><fieldlabel>qmd_weighting</fieldlabel><fieldentry>{POINTS_9DP}</fieldentry></qti_metadatafield>
    <qti_metadatafield><fieldlabel>qmd_globalid</fieldlabel><fieldentry>{QUESTION_UUID}</fieldentry></qti_metadatafield>
  </qtimetadata></itemmetadata>
  <itemproc_extension><d2l_2p0:difficulty>{DIFFICULTY}</d2l_2p0:difficulty><d2l_2p0:isbonus>{BONUS}</d2l_2p0:isbonus><d2l_2p0:ismandatory>{MANDATORY}</d2l_2p0:ismandatory></itemproc_extension>
  {TYPE_BODY}
</item>
```

Set `qmd_computerscored` to `yes` for automatically scored items and to `no` for Long Answer. Format points to nine decimal places. Default difficulty to `1`; set `isbonus` and `ismandatory` to `no`.

Inside a random pool, give every candidate item the pool's shared `OBJ_{POOL_KEY}` as its `ident`. Keep each candidate's label, response identifiers, and UUID unique.

## Identifiers and escaping

- Generate a UUID for every org unit and question. Keep identifiers unique within the package.
- Use unique ASCII keys for question labels and response identifiers.
- Keep quiz and short titles ASCII. Student-visible HTML may contain UTF-8.
- Put HTML inside `mattext texttype="text/html"` and XML-escape the complete HTML payload exactly once.
- Keep `quiz.xml`, `res_quiz`, and the resource `href` consistent.
- Preserve element order: metadata, item settings, presentation, optional hint, resprocessing, optional feedback.

## Final checks

- Parse every XML entry.
- Confirm all XML entries begin with the BOM.
- Confirm both orgunit identifiers match.
- Confirm every response reference names an identifier in the same item.
- Confirm every question UUID and non-pool label is unique.
- Confirm every pool draw count is positive and no greater than its candidate count.
- Confirm media references resolve to archive entries.
