import argparse
from pathlib import Path


def count(text):
    return {"lines": len(text.splitlines()), "words": len(text.split()), "chars": len(text)}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Count lines, words and characters in a file.")
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    c = count(args.path.read_text())
    print(f"{c['lines']} {c['words']} {c['chars']} {args.path}")


if __name__ == "__main__":
    main()
