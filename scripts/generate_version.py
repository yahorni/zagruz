from pathlib import Path

import toml


def main():
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path) as f:
        data = toml.load(f)
    version = data["project"]["version"]

    # Use absolute path with consistent case
    version_file = Path(__file__).parent.parent / "src" / "zagruz" / "_version.py"
    version_file.write_text(f'__version__ = "{version}"\n')


if __name__ == "__main__":
    main()
