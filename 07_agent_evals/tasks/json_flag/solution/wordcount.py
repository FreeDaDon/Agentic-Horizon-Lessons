import argparse
import json
from pathlib import Path


def count(text):
    return {"lines": len(text.splitlines()), "words": len(text.split()), "chars": len(text)}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Count lines, words and characters in a file.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--json", action="store_true", help="print the counts as one JSON object")
    args = parser.parse_args(argv)
    c = count(args.path.read_text())
    if args.json:
        print(json.dumps(c))
    else:
        print(f"{c['lines']} {c['words']} {c['chars']} {args.path}")


if __name__ == "__main__":
    main()
