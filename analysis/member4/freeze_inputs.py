"""Compatibility entry point: verify reviewed inputs, never create/refresh locks.

Explicit package/lock authoring lives in scripts/build_portable_integrity.py.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    sys.path.insert(0, str(ROOT / 'scripts'))
    from remediation_state import verify
    result = verify(ROOT)
    print('Protected current inputs, immutable audit artifacts and portable original bytes:', result)
    return result


if __name__ == '__main__':
    main()
