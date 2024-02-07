"""Trivial test to see if model import still succeeds."""

import sys

sys.path.append("../..")


def test_import():
    import paseos  # noqa: F401


if __name__ == "__main__":
    test_import()
