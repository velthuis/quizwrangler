#!/usr/bin/env python3
"""Expose the QTI validator bundled with the quizwrangler-qti skill."""

import importlib.util
import pathlib


VALIDATOR = (
    pathlib.Path(__file__).resolve().parent.parent
    / "skills"
    / "quizwrangler-qti"
    / "scripts"
    / "validate_qti.py"
)

_SPEC = importlib.util.spec_from_file_location("_quizwrangler_qti_validator", VALIDATOR)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

for _NAME in dir(_MODULE):
    if not _NAME.startswith("_"):
        globals()[_NAME] = getattr(_MODULE, _NAME)


if __name__ == "__main__":
    raise SystemExit(_MODULE.main())
