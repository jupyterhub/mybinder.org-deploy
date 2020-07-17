#!/usr/bin/env python3
"""obfuscate a yaml file containing secret values

for use in testing/linting with secrets without revealing
secret values in linting errors

Creates a new yaml file with the same structure
(dict keys, lists, item types),
but all scalars (ints, floats, strings) replaced with placeholders
to avoid leaking secrets on errors.

Assumes:

- input file is valid yaml
- defined fields are not sensitive info
- keys of dictionaries are not sensitive info

If input file or output file is unspecified, stdin/stdout are used,
allowing for piped usage.

usage:

    cat secret.yaml | obfuscate-yaml.py > obfuscated.yaml
    obfuscate-yaml.py secret.yaml > obfuscated.yaml
    obfuscate-yaml.py secret.yaml obfuscated.yaml
"""
import argparse
import sys
from contextlib import contextmanager

import yaml


def obfuscate(field):
    """Return an object with the same structure

    obfuscating any scalars (int, float, str)
    """

    if isinstance(field, int):
        return 0
    elif isinstance(field, float):
        return 0.0
    elif isinstance(field, str):
        return "xyz"
    if isinstance(field, dict):
        return {key: obfuscate(value) for key, value in field.items()}
    elif isinstance(field, list):
        return [obfuscate(item) for item in field]
    else:
        raise TypeError(f"Unrecognized type: {type(field)}")


def main(in_file, out_file):
    """obfuscate in_file and store in out_file

    in_file / out_file should be open file-like objects
    """
    config = yaml.safe_load(in_file)
    obfuscated = obfuscate(config)
    yaml.safe_dump(obfuscated, out_file)


@contextmanager
def stream_context(stream):
    """Wrap an existing stream in a context manager

    so it behaves the same as `open`
    """
    yield stream


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input_file",
        nargs="?",
        help="secret yaml file to obfuscate. If not set, use stdin.",
    )
    parser.add_argument(
        "output_file",
        nargs="?",
        help="destination yaml file to store obfuscated result. If not set, use stdout.",
    )
    opts = parser.parse_args()

    if opts.input_file:
        input_file = open(opts.input_file)
    else:
        input_file = stream_context(sys.stdin)

    if opts.output_file:
        print(f"Writing output to {opts.output_file}", file=sys.stderr)
        output_file = open(opts.output_file, "w")
    else:
        output_file = stream_context(sys.stdout)

    if opts.input_file and opts.output_file:
        # store origin in comment if reading from and writing to files
        output_file.write(f"# generated from {opts.input_file}\n")

    with input_file as in_f, output_file as out_f:
        main(in_f, out_f)
