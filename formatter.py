"""Formats Python code in Votr's custom idiosyncratic code style. (The Votr
author is a stubborn curmudgeon who dislikes the default Black/Ruff code style
a bit too much.)

Summary of differences:

- Bin-pack call arguments
- Reduce indentation of a call whose only argument is another call
- Don't indent `foo = "str"`
- Allow unlimited line length for imports

Exit status: 0 if OK, 1 with --diff/--check if different, 2 on error.
"""

import argparse
import ast
import difflib
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ruff import find_ruff_bin  # pyright: ignore [reportMissingTypeStubs]

LINE_LENGTH = 80


def tweak_chunk(content: str) -> str:
    """Tweaks a piece of code after it's been reformatted by Ruff."""
    #
    # Reduce indentation of a call whose only argument is another call.

    pattern = (
        r"^( *)[^#\s][^#\n]*\(\n"  #  |foo(        => |
        r"\1    [^#\s][^#\n]*\(\n"  # |    bar(    => |foo(bar(
        r"(\1        [^\n]*\n)+"  #   |        ... => |    ...
        r"\1    \),?\n"  #            |    ),      => |))
        r"\1\),?\n"  #                |)           => |
    )

    def replacer1(matchobj: re.Match[str]) -> str:
        original = matchobj.group(0)
        lines = original.splitlines()
        if '"""' in original or "'''" in original:
            return original
        new = [
            lines[0] + lines[1].lstrip(),
            *(line[4:] for line in lines[2:-2]),
            lines[-2][4:].rstrip(",") + lines[-1].lstrip(),
        ]
        if len(new[0]) > LINE_LENGTH:
            return original
        return "".join(line + "\n" for line in new)

    content = re.sub(pattern, replacer1, content, flags=re.MULTILINE)

    # Always write `foo = "str"` on one line. Ruff breaks it into three lines if
    # doing so allows it to stay under the line length limit; it uses one line
    # if the string is short enough to fit, or long enough that it'd exceed the
    # limit anyway. We don't care that much about the limit, and slightly prefer
    # to make the formatting more consistent.

    pattern = (
        r"^( *)([^#\s][^#\n]* )\(\n"
        r"\1    (\w*\"(\\\"|[^\"#\n])*\"|\w*'(\\'|[^'#\n])*')\n"
        r"\1\)\n"
    )

    content = re.sub(pattern, r"\1\2\3\n", content, flags=re.MULTILINE)

    # Bin-pack call arguments, and put the closing `)` on the same line as the
    # last argument. Inspired by ClangFormat's BinPack options.

    pattern = (
        # `[\w\]]\(` matches calls: `foo(` or `foo[bar](`, but not `foo = (`,
        # `foo((`, or `foo[(`.
        # Keep Ruff's style for parentheses used as tuple literals and grouping
        # operators, because bin packing is not consistently nicer there.
        r"^( *)[^\s][^\n]*[\w\]]\(\n"
        # `[^\s]` to give up if the call contains nested indentation.
        r"(\1    [^\s][^\n]*\n)+"
        r"\1\)+,?( +#[^\n]+)?\n"
    )

    def replacer2(matchobj: re.Match[str]) -> str:
        original = matchobj.group(0)
        lines = original.splitlines()

        # Give up if the call contains multiline strings.
        # (Known issue: We can't tell if the whole call is inside one.)
        if '"""' in original or "'''" in original:
            return original

        # Give up if the call contains comments, except on the last line.
        # Half-heartedly allow "#" in strings, unless surrounded by spaces.
        if any(" # " in line for line in lines[0:-1]):
            return original

        # Keep Ruff's style for kwargs-only constructor calls. Things like
        # dict(), TypedDicts, and Fladgejt structures tend to look nicer in
        # Ruff's longer, more vertical style.
        #
        # This heuristic is hacky, but it works pretty well. We do want to pack
        # the closing `)` in errors like `raise ValueError(f"...")`, despite its
        # CamelCase name, and in method calls like `foo.click(return_ops=True)`
        # or `foo.perform(hint=SomeType)`, despite being kwargs-only.
        classlike_name = re.search(r"\b(\w*[A-Z]\w+|dict)\($", lines[0])
        only_kwargs = re.search(r"^ *\w+=", lines[1])
        if classlike_name and only_kwargs:
            return original

        # Short args (those that fit a single line) are packed together.
        # Long args (on multiple lines) are kept as-is; not merged with short
        # args, nor with each other, nor within themselves. (Merging lines
        # within a long arg can sometimes look nicer, but not consistently.)
        new = [lines[0]]
        state: str = "BREAK"
        for line in lines[1:-1]:
            if (
                state == "SHORT_ARG"
                and line.endswith(",")
                and len(merged := f"{new[-1]} {line.strip()}") <= LINE_LENGTH
            ):
                new[-1] = merged
            else:
                new.append(line)
            state = (
                ("BREAK" if state == "LONG_ARG" else "SHORT_ARG")
                if line.endswith(",")
                else "LONG_ARG"
            )

        # Move the closing parenthesis and trailing comment (if any) to the
        # previous line. (This can sometimes bring it over the length limit, but
        # that's OK. It's nicer to apply the rule consistently.)
        new[-1] = new[-1].rstrip(",") + lines[-1].strip()

        return "".join(line + "\n" for line in new)

    content = re.sub(pattern, replacer2, content, flags=re.MULTILINE)

    return content


FMT_OFF = re.compile(
    r"(^ *# fmt: off\n.*?(?:^ *# fmt: on\n|\Z))", re.MULTILINE | re.DOTALL)


def tweak_file_content(content: str) -> str:
    """Tweaks a file after it's been reformatted by Ruff, but only the parts
    that are not excluded from formatting.
    """
    parts = FMT_OFF.split(content)  # odd items are the "fmt off" regions
    return "".join(
        part if i % 2 else tweak_chunk(part) for i, part in enumerate(parts))


class FormatError(Exception):
    pass


def udiff(old: str, new: str, name: str) -> str:
    return "".join(difflib.unified_diff(
        old.splitlines(True), new.splitlines(True), f"a/{name}", f"b/{name}"))


def run_ruff(src: str, filename: str, args: list[str]) -> tuple[str, str]:
    command = [find_ruff_bin(), *args, "--stdin-filename", filename, "-"]
    proc = subprocess.run(command, input=src, capture_output=True, text=True)
    if proc.returncode:
        raise FormatError(proc.stderr.strip().removeprefix("error: "))
    return (proc.stdout, proc.stderr)


def format_file_content(src: str, filename: str) -> tuple[str, str]:
    """The whole pipeline: ruff format, then the tweaks (AST-checked)."""
    # 1. Run Ruff format
    src, warnings1 = run_ruff(src, filename, ["format"])

    # 2. Run our regex tweaks + check AST equivalence
    base = src
    src = tweak_file_content(src)
    try:
        same = ast.dump(ast.parse(base)) == ast.dump(ast.parse(src))
    except SyntaxError as e:
        raise FormatError(f"tweaks produced invalid code: {e}")
    if not same:
        raise FormatError(
            "tweaks changed the AST, refusing to write:\n"
            + udiff(base, src, filename))

    # 3. Sort imports (this can modify AST)
    #
    # Allow unlimited line length for import statements. Don't split them into
    # multiple lines with (\n...\n). They're easier to grep this way.
    src, warnings2 = run_ruff(
        src, filename,
        ["check", "--select", "I", "--fix", "--quiet", "--line-length", "9000"])

    return (src, warnings1 + warnings2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "files", nargs="*", help="files to format, or '-' for stdin")
    parser.add_argument(
        "--check", action="store_true",
        help="don't write files, exit 1 if changes")
    parser.add_argument(
        "--diff", action="store_true", help="don't write files, print diff")
    parser.add_argument("--stdin-filename", default="stdin.py")
    options = parser.parse_args(argv)

    if not options.files:
        command = [
            "git", "ls-files",
            "-z", "--cached", "--others", "--exclude-standard", "--", "*.py",
        ]  # fmt: skip
        proc = subprocess.run(
            command, input=b"", stdout=subprocess.PIPE, check=True)
        for file in proc.stdout.decode("utf-8").split("\0"):
            if file and Path(file).exists():
                options.files.append(file)

    def format_file(name: str) -> tuple[int, str, str]:
        if name == "-":
            name = options.stdin_filename
            old = sys.stdin.read()
            write = sys.stdout.write
        else:
            path = Path(name)
            old = path.read_text()
            write = path.write_text

        try:
            new, warnings = format_file_content(old, name)
        except FormatError as e:
            return (2, f"error: {name}: {e}\n", "")

        if new == old:
            return (0, warnings, "")

        if options.diff:
            return (1, warnings, udiff(old, new, name))
        elif options.check:
            return (1, warnings + f"would reformat {name}\n", "")
        else:
            write(new)
            return (0, warnings, "")

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(format_file, options.files))

    status = 0

    for file_status, file_err, file_out in results:
        status = max(status, file_status)
        sys.stderr.write(file_err)
        sys.stdout.write(file_out)

    sys.exit(status)


if __name__ == "__main__":
    main()
