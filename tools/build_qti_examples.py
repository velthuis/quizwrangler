#!/usr/bin/env python3
"""Rebuild the public synthetic QTI example package."""

import html
import pathlib
import uuid
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "examples" / "expected-output"
IMAGE_SOURCE = ROOT / "examples" / "input" / "sample-chart.png"
BOM = b"\xef\xbb\xbf"
NS = uuid.NAMESPACE_URL
ZIP_DATE = (2026, 1, 1, 0, 0, 0)


def uid(name):
    return str(uuid.uuid5(NS, name))


def esc_html(value):
    return html.escape(value, quote=True)


def metadata(key, qtype, points="1.000000000", computer="yes", ident=None):
    ident = ident or f"OBJ_{key}"
    return (
        f'<item ident="{ident}" label="QUES_{key}" d2l_2p0:page="1" title="{key}">'
        "<itemmetadata><qtimetadata>"
        "<qti_metadatafield><fieldlabel>qmd_computerscored</fieldlabel>"
        f"<fieldentry>{computer}</fieldentry></qti_metadatafield>"
        "<qti_metadatafield><fieldlabel>qmd_questiontype</fieldlabel>"
        f"<fieldentry>{qtype}</fieldentry></qti_metadatafield>"
        "<qti_metadatafield><fieldlabel>qmd_weighting</fieldlabel>"
        f"<fieldentry>{points}</fieldentry></qti_metadatafield>"
        "<qti_metadatafield><fieldlabel>qmd_globalid</fieldlabel>"
        f"<fieldentry>{uid('item-' + key)}</fieldentry></qti_metadatafield>"
        "</qtimetadata></itemmetadata><itemproc_extension>"
        "<d2l_2p0:difficulty>1</d2l_2p0:difficulty>"
        "<d2l_2p0:isbonus>no</d2l_2p0:isbonus>"
        "<d2l_2p0:ismandatory>no</d2l_2p0:ismandatory>"
        "</itemproc_extension>"
    )


def material(text):
    return f'<material><mattext texttype="text/html">{esc_html(text)}</mattext></material>'


def plain_material(text):
    return f'<material><mattext texttype="text/plain">{html.escape(text)}</mattext></material>'


def choice_item(
    key, qtype, stem, options, correct, multiple=False, ident=None, image=None, feedback=None
):
    cardinality = "Multiple" if multiple else "Single"
    labels = []
    for i, option in enumerate(options, 1):
        option_material = (
            plain_material(option)
            if qtype == "True/False"
            else material(option)
        )
        labels.append(
            f'<flow_label class="Block"><response_label ident="QUES_{key}_A{i}">'
            f"<flow_mat>{option_material}</flow_mat></response_label></flow_label>"
        )
    media = ""
    if image:
        image_filename = image.rsplit("/", 1)[-1]
        media = (
            '<material><matimage d2l_2p0:is_hidden="true" '
            f'uri="{image.replace("/", chr(92))}">'
            f"{image_filename}</matimage></material>"
        )
    presentation = (
        f"<presentation><flow>{media}{material(stem)}"
        "<response_extension><d2l_2p0:display_style>2</d2l_2p0:display_style>"
        f"<d2l_2p0:enumeration>"
        "6"
        f"</d2l_2p0:enumeration>"
        "<d2l_2p0:grading_type>0</d2l_2p0:grading_type>"
        "</response_extension>"
        f'<response_lid ident="QUES_{key}_LID" rcardinality="{cardinality}">'
        f'<render_choice shuffle="no">{"".join(labels)}</render_choice>'
        "</response_lid></flow></presentation>"
    )
    correct_set = set(correct if isinstance(correct, (list, tuple)) else [correct])
    conditions = []
    if multiple:
        outcomes = (
            "<outcomes>"
            '<decvar vartype="Integer" defaultval="0" varname="que_score" '
            'minvalue="0" maxvalue="100" />'
            '<decvar vartype="Integer" defaultval="0" varname="D2L_Correct" minvalue="0" />'
            '<decvar vartype="Integer" defaultval="0" varname="D2L_Incorrect" minvalue="0" />'
            "</outcomes>"
        )
        for i in range(1, len(options) + 1):
            target = "D2L_Correct" if i in correct_set else "D2L_Incorrect"
            conditions.append(
                '<respcondition title="Response Condition" continue="yes"><conditionvar>'
                f'<varequal respident="QUES_{key}_LID">QUES_{key}_A{i}</varequal>'
                f'</conditionvar><setvar varname="{target}" action="Add">1</setvar>'
                "</respcondition>"
            )
        conditions.append(
            '<respcondition><setvar varname="que_score" action="Set">'
            "D2L_Correct</setvar></respcondition>"
        )
    else:
        outcomes = ""
        for i in range(1, len(options) + 1):
            score = "100.000000000" if i in correct_set else "0.000000000"
            conditions.append(
                f'<respcondition title="Response Condition {i}"><conditionvar>'
                f'<varequal respident="QUES_{key}_LID">QUES_{key}_A{i}</varequal>'
                f'</conditionvar><setvar action="Set">{score}</setvar></respcondition>'
            )
    feedback_xml = (
        f'<itemfeedback ident="QUES_{key}">{material(feedback)}</itemfeedback>'
        if feedback else ""
    )
    return (
        metadata(key, qtype, ident=ident)
        + presentation
        + f'<resprocessing>{outcomes}{"".join(conditions)}</resprocessing>'
        + f"{feedback_xml}</item>"
    )


def short_answer(key, stem, answer, ident=None):
    return (
        metadata(key, "Short Answer", ident=ident)
        + f"<presentation><flow>{material(stem)}"
        f'<response_str ident="QUES_{key}_STR" rcardinality="Single">'
        f'<render_fib rows="1" columns="40" prompt="Box" fibtype="String">'
        f'<response_label ident="QUES_{key}_ANS" /></render_fib></response_str>'
        "</flow></presentation><resprocessing><outcomes>"
        '<decvar vartype="Integer" minvalue="0" maxvalue="100" varname="Blank_1" />'
        "</outcomes><respcondition><conditionvar>"
        f'<varequal respident="QUES_{key}_ANS" case="no">{answer}</varequal>'
        "</conditionvar><setvar action=\"Set\">100.000000000</setvar>"
        "</respcondition></resprocessing></item>"
    )


def long_answer(key, stem):
    return (
        metadata(key, "Long Answer", computer="no")
        + f"<presentation><flow>{material(stem)}"
        "<response_extension><d2l_2p0:has_signed_comments>no"
        "</d2l_2p0:has_signed_comments><d2l_2p0:has_htmleditor>no"
        "</d2l_2p0:has_htmleditor><d2l_2p0:has_fileupload>no"
        "</d2l_2p0:has_fileupload></response_extension>"
        f'<response_str ident="QUES_{key}_STR" rcardinality="Multiple">'
        '<render_fib rows="10" columns="80" prompt="Box" fibtype="String">'
        f'<response_label ident="QUES_{key}_ANS">{material("")}</response_label>'
        "</render_fib></response_str></flow></presentation></item>"
    )


def matching(key):
    choices = (
        '<flow_label class="Block"><response_label ident="QUES_matching_A1">'
        f"<flow_mat>{material('water')}</flow_mat></response_label>"
        '<response_label ident="QUES_matching_A2">'
        f"<flow_mat>{material('carbon dioxide')}</flow_mat></response_label></flow_label>"
    )
    groups = (
        f'<response_grp respident="QUES_{key}_C1" rcardinality="Single">'
        f"{material('H<sub>2</sub>O')}<render_choice shuffle=\"yes\">{choices}"
        "</render_choice></response_grp>"
        f'<response_grp respident="QUES_{key}_C2" rcardinality="Single">'
        f"{material('CO<sub>2</sub>')}<render_choice shuffle=\"yes\">{choices}"
        "</render_choice></response_grp>"
    )
    conditions = (
        f'<respcondition><conditionvar><varequal respident="QUES_{key}_C1">'
        "QUES_matching_A1</varequal></conditionvar>"
        '<setvar varname="D2L_Correct" action="Add">1</setvar></respcondition>'
        f'<respcondition><conditionvar><varequal respident="QUES_{key}_C2">'
        "QUES_matching_A2</varequal></conditionvar>"
        '<setvar varname="D2L_Correct" action="Add">1</setvar></respcondition>'
    )
    return (
        metadata(key, "Matching")
        + f"<presentation><flow>{material('Match each formula from an aquatic-habitat lab to its name.')}"
        f"{groups}</flow></presentation><resprocessing><outcomes>"
        '<decvar vartype="Integer" defaultval="0" varname="D2L_Correct" minvalue="0" />'
        '<decvar vartype="Integer" defaultval="0" varname="D2L_Incorrect" minvalue="0" />'
        '<decvar vartype="Decimal" defaultval="0" varname="que_score" minvalue="0" />'
        f"</outcomes>{conditions}<respcondition><setvar varname=\"que_score\" "
        'action="Set">D2L_Correct</setvar></respcondition></resprocessing></item>'
    )


def ordering(key, ident=None):
    labels = "".join(
        f'<response_label ident="QUES_{key}_O{i}"><flow_mat>{material(text)}</flow_mat>'
        "</response_label>"
        for i, text in enumerate(("Egg", "Hatchling", "Adult"), 1)
    )
    conditions = "".join(
        '<respcondition title="Correct Condition"><conditionvar>'
        f'<varequal respident="QUES_{key}_O{i}">{i}</varequal></conditionvar>'
        '<setvar varname="D2L_Correct" action="Add">1</setvar></respcondition>'
        '<respcondition title="Incorrect Condition"><conditionvar><not>'
        f'<varequal respident="QUES_{key}_O{i}">{i}</varequal></not></conditionvar>'
        '<setvar varname="D2L_Incorrect" action="Add">1</setvar></respcondition>'
        for i in range(1, 4)
    )
    return (
        metadata(key, "Ordering", ident=ident)
        + f"<presentation><flow>{material('Put these basic dinosaur life stages in order.')}"
        f'<response_grp respident="QUES_{key}_O" rcardinality="Ordered">'
        f'<render_choice shuffle="yes"><flow_label class="Block">{labels}</flow_label>'
        "</render_choice></response_grp></flow></presentation>"
        "<resprocessing><outcomes>"
        '<decvar vartype="Integer" defaultval="0" varname="D2L_Correct" minvalue="0" />'
        '<decvar vartype="Integer" defaultval="0" varname="D2L_Incorrect" minvalue="0" />'
        '<decvar vartype="Integer" defaultval="0" varname="que_score" minvalue="0" />'
        f"</outcomes>{conditions}<respcondition><conditionvar>"
        '<varequal respident="D2L_Incorrect">0</varequal></conditionvar>'
        '<setvar varname="que_score" action="Set">1</setvar>'
        "</respcondition></resprocessing></item>"
    )


def arithmetic(key, stem, formula="({n}*2)", ident=None, hint=None):
    variable = (
        '<variable name="n"><minvalue>2</minvalue><maxvalue>10</maxvalue>'
        "<decimalplaces>0</decimalplaces><step>1</step></variable>"
    )
    hint_xml = (
        f"<hint><hintmaterial><flow_mat>{material(hint)}</flow_mat></hintmaterial></hint>"
        if hint else ""
    )
    return (
        metadata(key, "Arithmetic", ident=ident)
        + f"<presentation><flow>{material(stem)[:-11]}"
        f"<mat_extension>{variable}<formula>{formula}</formula></mat_extension>"
        "</material>"
        f'<response_num ident="QUES_{key}_NUM" rcardinality="Single" rtiming="no">'
        f'<render_fib fibtype="Decimal" prompt="Box"><response_label '
        f'ident="QUES_{key}_A1" /></render_fib></response_num>'
        f'<response_str ident="QUES_{key}_STR" rcardinality="Single" rtiming="no">'
        f'<render_fib fibtype="String" prompt="Box"><response_label '
        f'ident="QUES_{key}_A2" /></render_fib></response_str></flow></presentation>'
        f"{hint_xml}<resprocessing><respcondition><respcond_extension>"
        f"<formula>{formula}</formula>"
        '<precision type="decimalplaces" d2l_2p0:precision_enforced="no">0</precision>'
        '<tolerance type="units">0</tolerance>'
        '<units d2l_2p0:worth="0" casesensitive="no" />'
        "</respcond_extension><conditionvar><other /></conditionvar>"
        '<setvar action="Set">100</setvar></respcondition></resprocessing></item>'
    )


def fill_blanks(
    key,
    before="An adult axolotl retains its external ",
    answer="gills",
    after=".",
    ident=None,
):
    return (
        metadata(key, "Fill in the Blanks", ident=ident)
        + f"<presentation><flow>{material(before)}"
        f'<response_str ident="QUES_{key}_B1_STR" rcardinality="Single">'
        f'<render_fib rows="1" columns="30" prompt="Box" fibtype="String">'
        f'<response_label ident="QUES_{key}_B1_ANS" /></render_fib></response_str>'
        f"{material(after)}</flow></presentation><resprocessing><outcomes>"
        '<decvar vartype="Integer" minvalue="0" maxvalue="100" varname="Blank_1" />'
        "</outcomes><respcondition><conditionvar>"
        f'<varequal respident="QUES_{key}_B1_ANS" case="no">{html.escape(answer)}</varequal>'
        "</conditionvar><setvar action=\"Set\">100.000000000</setvar>"
        "</respcondition></resprocessing></item>"
    )


def multi_short(key):
    return (
        metadata(key, "Multi-Short Answer")
        + f"<presentation><flow>{material('Name the two kinds of living monotremes.')}"
        f'<response_str ident="QUES_{key}_STR" rcardinality="Single">'
        '<render_fib d2l_2p0:input_boxes="2" rows="1" columns="40" '
        f'prompt="Box" fibtype="String"><response_label ident="QUES_{key}_ANS" />'
        "</render_fib></response_str></flow></presentation><resprocessing>"
        + "".join(
            f'<respcondition><conditionvar><varequal respident="QUES_{key}_ANS" '
            f'case="no">{answer}</varequal></conditionvar>'
            '<setvar action="Set">50.000000000</setvar></respcondition>'
            for answer in ("platypus", "echidna")
        )
        + "</resprocessing></item>"
    )


def wrapper(content, title):
    hint_switch = "yes" if "<hint>" in content else "no"
    feedback_switch = "yes" if "<itemfeedback" in content else "no"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<questestinterop xmlns:d2l_2p0="http://desire2learn.com/xsd/d2lcp_v2p0">'
        f'<assessment d2l_2p0:id="1" title="{title}" ident="res_quiz">'
        f'<assessmentcontrol hintswitch="{hint_switch}" '
        f'feedbackswitch="{feedback_switch}" />'
        f'<section ident="CONTAINER_SECTION">{content}</section>'
        "</assessment></questestinterop>"
    )


def manifest(title, orgunit):
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<manifest identifier="D2L_quizwrangler_sample" '
        'xmlns:d2l_2p0="http://desire2learn.com/xsd/d2lcp_v2p0" '
        'xmlns="http://www.imsglobal.org/xsd/imscp_v1p1"><resources>'
        f'<resource identifier="{orgunit}" type="webcontent" '
        'd2l_2p0:material_type="orgunitconfig" '
        'href="orgunitconfig\\orgunitconfig.xml" title="" />'
        '<resource identifier="res_quiz" type="webcontent" '
        f'd2l_2p0:material_type="d2lquiz" href="quiz.xml" title="{title}" />'
        "</resources></manifest>"
    )


def write_package(path, title, content, media=None):
    orgunit = uid(path.stem + "-orgunit")
    entries = {
        "imsmanifest.xml": manifest(title, orgunit),
        "quiz.xml": wrapper(content, title),
        "orgunitconfig/orgunitconfig.xml": (
            '<?xml version="1.0" encoding="utf-8"?>'
            f'<orgunit identifier="{orgunit}" />'
        ),
    }
    def add_entry(archive, name, data):
        info = zipfile.ZipInfo(name, ZIP_DATE)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, data)

    with zipfile.ZipFile(path, "w") as archive:
        for name, text in entries.items():
            add_entry(archive, name, BOM + text.encode("utf-8"))
        if media:
            add_entry(archive, media, IMAGE_SOURCE.read_bytes())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    image_name = f"quizzing/_{uid('sample-image')}.png"
    fixed = [
        choice_item(
            "tf",
            "True/False",
            "A platypus is a mammal that lays eggs.",
            ["True", "False"],
            1,
        ),
        choice_item(
            "mc_image",
            "Multiple Choice",
            "The chart shows dinosaur footprints recorded at three field sites. Which sequence of footprint counts matches it?",
            [
                "2, 4, and 6 footprints",
                "1, 3, and 5 footprints",
                "3, 6, and 9 footprints",
            ],
            1,
            image=image_name,
        ),
        choice_item(
            "ms",
            "Multi-Select",
            "<p>Select every trait that applies to an <strong>axolotl</strong>.</p>",
            [
                "It retains external gills as an adult",
                "It can regenerate lost limbs",
                "It has feathers",
            ],
            [1, 2],
            multiple=True,
            feedback=(
                "<p>Axolotls retain external gills and can regenerate limbs; "
                "they do not have feathers.</p>"
            ),
        ),
        short_answer(
            "sa",
            '<p>A museum display contains 2 real fossils and 2 replica fossils. Evaluate '
            '<math xmlns="http://www.w3.org/1998/Math/MathML">'
            "<mrow><mn>2</mn><mo>+</mo><mn>2</mn></mrow></math> to find how many "
            "objects are in the display.</p>",
            "4",
        ),
        long_answer(
            "la",
            "Explain how an axolotl's external gills help it live in an aquatic habitat.",
        ),
        matching("matching"),
        ordering("ordering"),
        arithmetic(
            "arithmetic",
            "Each display case contains two dinosaur eggs. If the museum prepares {n} display cases, how many eggs are displayed?",
            hint="<p>Each display case contains <em>two</em> eggs.</p>",
        ),
        fill_blanks("fib"),
        multi_short("msa"),
    ]
    pool_key = "mixed_pool"
    candidates = [
        choice_item(
            "pool_mc",
            "Multiple Choice",
            "Which animal is a monotreme?",
            ["River otter", "Platypus", "Beaver"],
            2,
            ident=f"OBJ_{pool_key}",
        ),
        choice_item(
            "pool_tf",
            "True/False",
            "An axolotl is an amphibian.",
            ["True", "False"],
            1,
            ident=f"OBJ_{pool_key}",
        ),
        arithmetic(
            "pool_arithmetic",
            "Each fossil case holds three dinosaur eggs. For {n} cases, how many eggs are there?",
            formula="({n}*3)",
            ident=f"OBJ_{pool_key}",
        ),
        fill_blanks(
            "pool_fib",
            before="Triceratops lived during the Late ",
            answer="Cretaceous",
            after=" Period.",
            ident=f"OBJ_{pool_key}",
        ),
    ]
    pool = (
        f'<section title="Animal Adaptations Check" d2l_2p0:page="1" ident="RAND_{pool_key}">'
        "<qtimetadata><qti_metadatafield><fieldlabel>qmd_numberofitems</fieldlabel>"
        "<fieldentry>2</fieldentry></qti_metadatafield><qti_metadatafield>"
        "<fieldlabel>qmd_weighting</fieldlabel><fieldentry>2.000000000</fieldentry>"
        "</qti_metadatafield></qtimetadata><sectionproc_extension>"
        "<d2l_2p0:display_section_name>no</d2l_2p0:display_section_name>"
        "<d2l_2p0:display_section_line>no</d2l_2p0:display_section_line>"
        "<d2l_2p0:type_display_section>0</d2l_2p0:type_display_section>"
        f'</sectionproc_extension>{"".join(candidates)}</section>'
    )
    write_package(
        OUT / "sample-qti-package.zip",
        "Remarkable Animals Field Quiz",
        "".join(fixed) + pool,
        media=image_name,
    )


if __name__ == "__main__":
    main()
