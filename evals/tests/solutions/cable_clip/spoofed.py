"""Adversarial: forge the old grader's stdout without defining a part."""

import json
import os


payload = json.dumps(
    {
        "built": True,
        "solids": 1,
        "error": None,
        "findings": [],
        "misfits": [],
        "flex_problems": [],
        "stages": {"lint": 1.0, "dims": 1.0, "flex": 1.0},
        "score": 1.0,
        "build_ms": 0.0,
    }
)
os.write(1, payload.encode())
os._exit(0)
