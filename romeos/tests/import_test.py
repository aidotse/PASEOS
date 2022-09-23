import sys

sys.path.append("../..")


def test_import():
    import romeos  # noqa: F401


if __name__ == "__main__":
    test_import()
