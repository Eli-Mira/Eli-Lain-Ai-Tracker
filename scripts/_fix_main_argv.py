from pathlib import Path

path = Path("main.py")
text = path.read_text(encoding="utf-8")
pairs = [
    ("def main():\n    import argparse\n", "def main(argv: list[str] | None = None) -> int:\n    import argparse\n"),
    ("    args = parser.parse_args()\n", "    args = parser.parse_args(argv)\n"),
    ('''                main_export = main(["export-public", "--data-dir", args.data_dir,
                                    "--public-dir", args.public_dir, "--theme", args.theme])
            if main_export:
                return main_export''',
     '''                if main(["export-public", "--data-dir", args.data_dir,
                         "--public-dir", args.public_dir, "--theme", args.theme]):
                    return 1'''),
]
for old, new in pairs:
    assert text.count(old) == 1, old
    text = text.replace(old, new)
path.write_text(text, encoding="utf-8")
compile(text, str(path), "exec")
print("main() now accepts argv and returns an exit code")