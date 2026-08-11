#!/usr/bin/env python3
"""Validate a QTI package against QuizWrangler's package profile.

The checks cover package layout, XML integrity, cross-file identifiers, media,
pool structure, item-type response shapes, and Arithmetic formulas. A clean
run means the package is structurally consistent; it cannot verify the quiz's
answer keys or guarantee behavior on every Brightspace instance.

Usage:
    python3 validate_qti.py package.zip
    python3 validate_qti.py package.zip --strict    # warnings become errors

Exit codes: 0 clean, 1 problems found, 2 could not read the file.
"""

import argparse
import ast
import itertools
import math
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

BOM = b"\xef\xbb\xbf"
MANIFEST = "imsmanifest.xml"

VALID_TOLERANCE = {"percent", "units"}

ARITHMETIC = "Arithmetic"
SUPPORTED_TYPES = {
    "True/False",
    "Multiple Choice",
    "Multi-Select",
    "Short Answer",
    "Long Answer",
    "Matching",
    "Ordering",
    "Arithmetic",
    "Fill in the Blanks",
    "Multi-Short Answer",
}

FUNCTION_CALL = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
ALLOWED_FUNCS = {
    "abs": abs,
    "cos": math.cos,
    "sin": math.sin,
    "tan": math.tan,
    "sqr": math.sqrt,
    "log": math.log10,
    "ln": math.log,
}
ALLOWED_CONSTANTS = {"pi": math.pi, "e": math.e}

# AST nodes permitted when evaluating a formula: numbers, + - * / ^ (as **),
# unary +/-, parentheses (no nodes), calls to the supported functions, and the
# supported constants. Anything else falls outside this validator's profile.
_ALLOWED_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.UAdd, ast.USub,
    ast.Call, ast.Name, ast.Load,
)


def _evaluate_node(node, env):
    """Evaluate a validated arithmetic AST without dynamic code execution."""
    if isinstance(node, ast.Expression):
        return _evaluate_node(node.body, env)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return env[node.id]
    if isinstance(node, ast.UnaryOp):
        value = _evaluate_node(node.operand, env)
        if isinstance(node.op, ast.UAdd):
            return +value
        return -value
    if isinstance(node, ast.BinOp):
        left = _evaluate_node(node.left, env)
        right = _evaluate_node(node.right, env)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        return left ** right
    if isinstance(node, ast.Call):
        function = env[node.func.id]
        arguments = [_evaluate_node(arg, env) for arg in node.args]
        return function(*arguments)
    raise TypeError(f"unsupported arithmetic node: {type(node).__name__}")


def eval_formula(formula, values):
    """Evaluate a profile Arithmetic formula at one variable assignment.

    Returns (result, None) or (None, reason). D2L's `^` is exponentiation;
    the supported functions (abs, cos, sin, tan, sqr, log, ln) and constants
    (pi, e) are supported.
    """
    expr = formula
    for name, val in values.items():
        expr = expr.replace("{%s}" % name, "(%s)" % repr(val))
    expr = expr.replace("^", "**")
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        return None, f"does not parse as arithmetic ({exc.msg})"
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            return None, f"contains unsupported syntax ({type(node).__name__})"
        if (
            isinstance(node, ast.Constant)
            and (
                isinstance(node.value, bool)
                or not isinstance(node.value, (int, float))
            )
        ):
            return None, "contains a non-numeric constant"
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_FUNCS:
                return None, "calls an unsupported function"
        if isinstance(node, ast.Name):
            if node.id not in ALLOWED_FUNCS and node.id not in ALLOWED_CONSTANTS:
                return None, f"references unknown name '{node.id}'"
    env = dict(ALLOWED_FUNCS)
    env.update(ALLOWED_CONSTANTS)
    try:
        result = _evaluate_node(tree, env)
    except ZeroDivisionError:
        return None, "divides by zero"
    except OverflowError:
        return None, "overflows"
    except ValueError:
        return None, "hits a math domain error (sqr/log/ln of a non-positive value)"
    except TypeError:
        return None, "uses a function with an invalid number or type of argument"
    if isinstance(result, complex):
        return None, "produces a non-real result (negative base to fractional power)"
    return result, None


def formula_sample_points(variables):
    """Assignments to probe: min/mid/max per variable (plus 0 when the range
    crosses it to check division by zero), full cartesian product when
    small, corner+midpoint scheme when that would explode."""
    candidates = {}
    for name, (vmin, vmax) in variables.items():
        vals = {vmin, vmax, vmin + (vmax - vmin) / 2}
        if vmin <= 0 <= vmax:
            vals.add(0.0)
        candidates[name] = sorted(vals)

    names = sorted(candidates)
    total = 1
    for n in names:
        total *= len(candidates[n])
    if total <= 1024:
        for combo in itertools.product(*(candidates[n] for n in names)):
            yield dict(zip(names, combo))
        return

    mids = {n: candidates[n][len(candidates[n]) // 2] for n in names}
    yield {n: candidates[n][0] for n in names}
    yield {n: candidates[n][-1] for n in names}
    yield dict(mids)
    for n in names:
        for v in candidates[n]:
            point = dict(mids)
            point[n] = v
            yield point


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, where, msg):
        self.errors.append((where, msg))

    def warn(self, where, msg):
        self.warnings.append((where, msg))


def check_layout(zf, rep):
    names = zf.namelist()
    if MANIFEST not in names:
        nested = [n for n in names if n.endswith("/" + MANIFEST)]
        if nested:
            rep.error(
                MANIFEST,
                f"manifest is nested at '{nested[0]}' instead of the archive root. "
                f"QuizWrangler expects {MANIFEST} at the top level -- zip the folder's "
                f"contents, not the folder.",
            )
        else:
            rep.error(MANIFEST, f"no {MANIFEST} anywhere in the archive")
        return False
    return True


def check_boms(zf, rep):
    """Every XML file in this profile starts with EF BB BF."""
    for name in zf.namelist():
        if not name.lower().endswith(".xml"):
            continue
        head = zf.read(name)[:3]
        if head != BOM:
            rep.error(
                name,
                f"missing UTF-8 BOM (starts {head.hex() or 'empty'}, expected efbbbf). "
                "the QuizWrangler QTI profile requires a BOM on every XML file.",
            )


def parse_all(zf, rep):
    """Parse every XML file. Returns {name: root}, omitting any that fail."""
    roots = {}
    for name in zf.namelist():
        if not name.lower().endswith(".xml"):
            continue
        raw = zf.read(name)
        if raw.startswith(BOM):
            raw = raw[len(BOM):]
        try:
            roots[name] = ET.fromstring(raw)
        except ET.ParseError as exc:
            rep.error(name, f"is not well-formed XML: {exc}")
    return roots


def check_orgunit(zf, roots, rep):
    """The orgunit UUID must match between manifest and orgunitconfig."""
    manifest = roots.get(MANIFEST)
    if manifest is None:
        return

    ids = [
        r.get("identifier")
        for r in manifest.iter()
        if r.tag.endswith("resource")
        and (r.get("{http://desire2learn.com/xsd/d2lcp_v2p0}material_type") == "orgunitconfig")
    ]
    if not ids:
        rep.warn(MANIFEST, "no orgunitconfig resource declared")
        return

    cfg_name = next((n for n in zf.namelist() if n.endswith("orgunitconfig.xml")), None)
    if cfg_name is None:
        rep.error(MANIFEST, "manifest declares an orgunitconfig resource but the file is absent")
        return

    cfg = roots.get(cfg_name)
    if cfg is None:
        return
    cfg_id = cfg.get("identifier")
    if cfg_id != ids[0]:
        rep.error(
            cfg_name,
            f"orgunit UUID mismatch: manifest says '{ids[0]}', orgunitconfig says "
            f"'{cfg_id}'. The identifiers must match.",
        )


def item_question_type(item):
    """Read qmd_questiontype out of an item's metadata, or None if absent."""
    for field in item.iter():
        if not field.tag.endswith("qti_metadatafield"):
            continue
        label = value = None
        for child in field:
            tag = child.tag.split("}")[-1]
            if tag == "fieldlabel":
                label = (child.text or "").strip()
            elif tag == "fieldentry":
                value = (child.text or "").strip()
        if label == "qmd_questiontype":
            return value
    return None


def descendants(node, suffix):
    return [e for e in node.iter() if e.tag.endswith(suffix)]


def check_media(zf, roots, rep):
    """Every local quizzing reference must resolve to an archive entry."""
    names = set(zf.namelist())
    for xml_name, root in roots.items():
        for elem in root.iter():
            refs = []
            if elem.tag.endswith("matimage") and elem.get("uri"):
                matimage_ref = elem.get("uri").replace("\\", "/")
                refs.append(matimage_ref)
                expected_filename = matimage_ref.rsplit("/", 1)[-1]
                actual_filename = (elem.text or "").strip()
                if actual_filename != expected_filename:
                    rep.error(
                        xml_name,
                        f"matimage for '{matimage_ref}' must contain filename "
                        f"'{expected_filename}', found '{actual_filename}'",
                    )
            if elem.tag.endswith("mattext") and elem.text:
                refs.extend(
                    m.replace("\\", "/")
                    for m in re.findall(r'(?:src|href)=["\'](quizzing[/\\][^"\']+)', elem.text)
                )
            for ref in refs:
                if ref not in names:
                    rep.error(xml_name, f"media reference '{ref}' has no matching archive entry")


def check_pools(roots, rep):
    """Check random-section counts and the shared candidate ident."""
    for name, root in roots.items():
        for section in descendants(root, "section"):
            ident = section.get("ident") or ""
            if not ident.startswith("RAND_"):
                continue
            candidates = [c for c in list(section) if c.tag.endswith("item")]
            draw_values = []
            for field in descendants(section, "qti_metadatafield"):
                label = next((c for c in field if c.tag.endswith("fieldlabel")), None)
                value = next((c for c in field if c.tag.endswith("fieldentry")), None)
                if label is not None and (label.text or "").strip() == "qmd_numberofitems":
                    draw_values.append((value.text or "").strip() if value is not None else "")
            where = f"{name}:{ident}"
            if len(draw_values) != 1:
                rep.error(where, "random pool must declare one qmd_numberofitems value")
                continue
            try:
                draw = int(draw_values[0])
            except ValueError:
                rep.error(where, f"pool draw count '{draw_values[0]}' is not an integer")
                continue
            if draw < 1 or draw > len(candidates):
                rep.error(
                    where,
                    f"pool draws {draw} from {len(candidates)} candidate item(s)",
                )
            expected = "OBJ_" + ident[len("RAND_"):]
            for item in candidates:
                if item.get("ident") != expected:
                    rep.error(
                        where,
                        f"candidate label '{item.get('label')}' has ident "
                        f"'{item.get('ident')}', expected shared '{expected}'",
                    )


def check_shared_item_shape(item, qtype, where, rep):
    """Checks that apply before the type-specific scoring rules."""
    if qtype is None:
        rep.error(where, "has no qmd_questiontype metadata")
        return
    if qtype == "Significant Figures":
        rep.error(
            where,
            "uses Significant Figures; QuizWrangler emits Arithmetic with percent "
            "tolerance for this grading intent",
        )
        return
    if qtype not in SUPPORTED_TYPES:
        rep.warn(where, f"question type '{qtype}' is outside the QuizWrangler profile")

    labels = descendants(item, "response_label")
    label_ids = [e.get("ident") for e in labels if e.get("ident")]
    if qtype != "Matching" and len(label_ids) != len(set(label_ids)):
        rep.error(where, "contains duplicate response_label identifiers")

    if qtype in {"True/False", "Multiple Choice", "Multi-Select"}:
        enumerations = [
            (e.text or "").strip()
            for e in descendants(item, "enumeration")
        ]
        if len(enumerations) != 1 or enumerations[0] not in {"1", "2", "3", "4", "5", "6"}:
            rep.error(where, "must use one response enumeration value from 1 through 6")

    if qtype in {"True/False", "Multiple Choice"}:
        lids = [e for e in descendants(item, "response_lid") if e.get("rcardinality") == "Single"]
        if len(lids) != 1:
            rep.error(where, f"{qtype} must contain one Single response_lid")
        if qtype == "True/False" and len(labels) != 2:
            rep.error(where, f"True/False has {len(labels)} choices; expected 2")
        if qtype == "True/False":
            fixed_labels = []
            for label in labels:
                texts = descendants(label, "mattext")
                if len(texts) != 1:
                    fixed_labels.append((None, None))
                else:
                    fixed_labels.append(
                        (texts[0].get("texttype"), (texts[0].text or "").strip())
                    )
            expected_labels = [
                ("text/plain", "True"),
                ("text/plain", "False"),
            ]
            if fixed_labels != expected_labels:
                rep.error(
                    where,
                    "True/False choices must be plain-text True and False labels, "
                    "in that order",
                )
    elif qtype == "Multi-Select":
        lids = [e for e in descendants(item, "response_lid") if e.get("rcardinality") == "Multiple"]
        if len(lids) != 1:
            rep.error(where, "Multi-Select must contain one Multiple response_lid")
    elif qtype in {"Short Answer", "Long Answer"}:
        if len(descendants(item, "response_str")) != 1:
            rep.error(where, f"{qtype} must contain one response_str")
    elif qtype == "Matching":
        if not descendants(item, "response_lid") and not descendants(item, "response_grp"):
            rep.error(where, "Matching has no response prompt groups")
    elif qtype == "Ordering":
        groups = [
            e for e in descendants(item, "response_grp")
            if e.get("rcardinality") == "Ordered"
        ]
        if len(groups) != 1:
            rep.error(where, "Ordering must contain one Ordered response_grp")
    elif qtype == "Fill in the Blanks":
        blanks = descendants(item, "response_str")
        outcomes = descendants(item, "outcomes")
        if not blanks:
            rep.error(where, "Fill in the Blanks has no response_str blanks")
        if len(outcomes) != 1:
            rep.error(where, "Fill in the Blanks must contain one outcomes block")
        blank_vars = [
            e.get("varname") for e in descendants(item, "decvar")
            if (e.get("varname") or "").startswith("Blank_")
        ]
        if len(blank_vars) != len(blanks):
            rep.error(
                where,
                f"has {len(blanks)} blank response(s) but {len(blank_vars)} Blank_N outcome(s)",
            )
    elif qtype == "Multi-Short Answer":
        responses = descendants(item, "response_str")
        boxes = descendants(item, "render_fib")
        if len(responses) != 1:
            rep.error(where, "Multi-Short Answer must contain one response_str")
        if len(boxes) != 1 or not boxes[0].get(
            "{http://desire2learn.com/xsd/d2lcp_v2p0}input_boxes"
        ):
            rep.error(where, "Multi-Short Answer must declare d2l_2p0:input_boxes")
        if descendants(item, "outcomes"):
            rep.error(where, "Multi-Short Answer must not contain an outcomes block")


def check_items(roots, rep):
    """Per-question checks on the quiz XML.

    Arithmetic items get the full formula/variable/scoring treatment. Other
    question types are checked only for things that apply to them -- they use a
    completely different scoring structure and would fail arithmetic rules.
    """
    seen_labels = set()
    seen_globalids = set()
    for name, root in roots.items():
        if name == MANIFEST or name.endswith("orgunitconfig.xml"):
            continue

        items = [e for e in root.iter() if e.tag.endswith("item")]
        if not items:
            rep.warn(name, "no <item> elements found -- package contains no questions")

        for item in items:
            ident = item.get("ident") or "<unnamed item>"
            where = f"{name}:{ident}"

            qtype = item_question_type(item)
            label = item.get("label")
            if label:
                if label in seen_labels:
                    rep.error(where, f"duplicate item label '{label}'")
                seen_labels.add(label)
            for field in descendants(item, "qti_metadatafield"):
                field_label = next((c for c in field if c.tag.endswith("fieldlabel")), None)
                field_value = next((c for c in field if c.tag.endswith("fieldentry")), None)
                if (
                    field_label is not None
                    and (field_label.text or "").strip() == "qmd_globalid"
                    and field_value is not None
                ):
                    gid = (field_value.text or "").strip()
                    if gid in seen_globalids:
                        rep.error(where, f"duplicate qmd_globalid '{gid}'")
                    seen_globalids.add(gid)

            check_shared_item_shape(item, qtype, where, rep)

            valid_tol = VALID_TOLERANCE if qtype == ARITHMETIC else None
            for tol in item.iter():
                if not tol.tag.endswith("tolerance") or valid_tol is None:
                    continue
                ttype = tol.get("type")
                if ttype not in valid_tol:
                    rep.error(
                        where,
                        f"tolerance type '{ttype}' -- expected one of "
                        f"{', '.join(sorted(valid_tol))} for a {qtype} question",
                    )
            if qtype != ARITHMETIC:
                # Everything below is arithmetic-specific. Other types are scored
                # with <outcomes>/<decvar>/setvar varname= accumulators, which is
                # correct for them and must not be flagged.
                continue

            formulas = [e.text or "" for e in item.iter() if e.tag.endswith("formula")]
            if len(formulas) < 2:
                rep.error(
                    where,
                    f"has {len(formulas)} <formula> element(s); expected 2 -- one in "
                    f"<mat_extension> to drive randomisation, one in <respcond_extension> "
                    f"to drive grading.",
                )
            elif len(set(formulas)) > 1:
                rep.error(
                    where,
                    f"the two <formula> values differ ({formulas[0]!r} vs {formulas[1]!r}). "
                    f"They must be byte-identical, or students see one answer and the "
                    f"grader expects another.",
                )

            bad_call = False
            for f in formulas:
                for call in FUNCTION_CALL.findall(f):
                    if call in ALLOWED_FUNCS:
                        continue
                    bad_call = True
                    if call == "sqrt":
                        rep.error(
                            where,
                            "formula calls 'sqrt()'; the QuizWrangler profile uses "
                            "'sqr()' for square root",
                        )
                    else:
                        rep.error(
                            where,
                            f"formula calls '{call}()'. This profile supports only "
                            f"{', '.join(sorted(ALLOWED_FUNCS))} (plus + - * / ^ and "
                            f"parentheses); rounding is handled by the precision setting, "
                            f"not the formula.",
                        )

            declared = {
                v.get("name")
                for v in item.iter()
                if v.tag.endswith("variable") and v.get("name")
            }
            used = set()
            for f in formulas:
                used |= set(re.findall(r"\{(\w+)\}", f))
            for mt in item.iter():
                if mt.tag.endswith("mattext") and mt.text:
                    used |= set(re.findall(r"\{(\w+)\}", mt.text))

            for missing in sorted(used - declared):
                rep.error(where, f"uses {{{missing}}} but declares no <variable name=\"{missing}\">")
            for unused in sorted(declared - used):
                rep.warn(where, f"declares variable '{unused}' but never uses it")

            ranges = {}
            for var in item.iter():
                if not var.tag.endswith("variable"):
                    continue
                vname = var.get("name")
                fields = {}
                for child in var:
                    tag = child.tag.split("}")[-1]
                    if tag in {"minvalue", "maxvalue", "step", "decimalplaces"}:
                        try:
                            fields[tag] = float(child.text)
                        except (TypeError, ValueError):
                            rep.error(where, f"variable '{vname}' has non-numeric {tag}")
                for req in ("minvalue", "maxvalue", "decimalplaces", "step"):
                    if not any(c.tag.endswith(req) for c in var):
                        rep.error(where, f"variable '{vname}' is missing <{req}>")
                if "minvalue" in fields and "maxvalue" in fields:
                    if fields["minvalue"] > fields["maxvalue"]:
                        rep.error(
                            where,
                            f"variable '{vname}' has minvalue {fields['minvalue']} greater "
                            f"than maxvalue {fields['maxvalue']}",
                        )
                    elif vname:
                        ranges[vname] = (fields["minvalue"], fields["maxvalue"])
                step = fields.get("step")
                if step is not None and step <= 0:
                    rep.error(where, f"variable '{vname}' has step {step}; step must be positive")
                dec = fields.get("decimalplaces")
                if dec is not None:
                    if dec != int(dec) or dec < 0:
                        rep.error(
                            where,
                            f"variable '{vname}' has decimalplaces {dec}; must be a "
                            f"non-negative integer",
                        )
                    elif step is not None and step > 0 and round(step, int(dec)) != step:
                        rep.warn(
                            where,
                            f"variable '{vname}' has step {step} finer than its "
                            f"{int(dec)} decimalplaces -- generated values will be rounded "
                            f"onto a coarser grid than the step implies",
                        )

            # Evaluate the formula across the variable grid after the formula
            # passed the function-call check and every used variable has a
            # sane numeric range.
            if formulas and not bad_call and used <= set(ranges):
                probe = {n: ranges[n] for n in used}
                seen_reasons = set()
                for point in formula_sample_points(probe) if probe else [{}]:
                    result, reason = eval_formula(formulas[0], point)
                    if reason and reason not in seen_reasons:
                        seen_reasons.add(reason)
                        at = ", ".join(f"{k}={v:g}" for k, v in sorted(point.items()))
                        rep.error(
                            where,
                            f"formula {reason} at {at or 'evaluation'} -- every value "
                            "sampled variable combinations must produce real, finite answers",
                        )
                    elif result is not None and (
                        result != result or result in (float("inf"), float("-inf"))
                    ):
                        rep.error(
                            where,
                            "formula produces NaN or infinity within the variable ranges",
                        )
                        break

            # Removing response_str breaks the import even with no unit field.
            has_num = any(e.tag.endswith("response_num") for e in item.iter())
            has_str = any(e.tag.endswith("response_str") for e in item.iter())
            if has_num and not has_str:
                rep.error(
                    where,
                    "has <response_num> but no <response_str>; the Arithmetic profile "
                    "requires both response blocks",
                )

            # Standard QTI 1.2 scoring markup is outside the Arithmetic profile.
            if any(e.tag.endswith("outcomes") for e in item.iter()):
                rep.error(
                    where,
                    "contains an <outcomes> block; the Arithmetic profile uses a bare "
                    "percentage setvar instead",
                )
            for sv in item.iter():
                if sv.tag.endswith("setvar") and sv.get("varname"):
                    rep.error(
                        where,
                        f"<setvar> carries varname='{sv.get('varname')}'. Arithmetic expects a bare "
                        f"<setvar action=\"Set\">100</setvar>.",
                    )


def validate(path, rep):
    with zipfile.ZipFile(path) as zf:
        bad = zf.testzip()
        if bad:
            rep.error(bad, "corrupt entry in archive")
            return
        if not check_layout(zf, rep):
            return
        check_boms(zf, rep)
        roots = parse_all(zf, rep)
        check_orgunit(zf, roots, rep)
        check_media(zf, roots, rep)
        check_pools(roots, rep)
        check_items(roots, rep)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("zipfile", help="QTI package to check")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = ap.parse_args()

    rep = Report()
    try:
        validate(args.zipfile, rep)
    except FileNotFoundError:
        print(f"error: no such file: {args.zipfile}", file=sys.stderr)
        return 2
    except zipfile.BadZipFile:
        print(f"error: {args.zipfile} is not a valid zip archive", file=sys.stderr)
        return 2

    for where, msg in rep.errors:
        print(f"{where}: error: {msg}")
    for where, msg in rep.warnings:
        print(f"{where}: warning: {msg}")

    n_err, n_warn = len(rep.errors), len(rep.warnings)
    if n_err or n_warn:
        print(f"\n{n_err} error(s), {n_warn} warning(s)")
    if n_err or (args.strict and n_warn):
        return 1
    print(f"{args.zipfile}: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
