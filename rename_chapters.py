import argparse
import re
from subprocess import run
from pathlib import Path

ORIGINAL_CHAPTERS_FILE = "{}.chapters.txt"
RENAMED_CHAPTERS_FILE = "{}-renamed.chapters.txt"


def cleanup():
    for f in Path.cwd().glob("*.chapters.txt"):
        f.unlink()


def main():
    parser = argparse.ArgumentParser(description="Replace uninformative MKV chapter names with numbers.")
    parser.add_argument('input', type=str, help="Path to MKV file with chapters")

    args = parser.parse_args()

    filepath = Path(args.input)

    run(["mkvextract", filepath, "chapters", "-s", ORIGINAL_CHAPTERS_FILE.format(filepath.stem)], check=True)
    names = []
    times = []
    with open(ORIGINAL_CHAPTERS_FILE.format(filepath.stem)) as f:
        for line in f:
            if "NAME" in line:
                names.append(line.split("=")[1].strip())
            if "NAME" not in line:
                times.append(line.split("=")[1].strip())
                
    output = []
    for i, (name, time) in enumerate(zip(names, times)):
        if re.fullmatch("^[0-9|:|\.]+$", name):
            name = f"Chapter {i+1:02}"
        output.append(f"CHAPTER{i+1:02}={time}\n")
        output.append(f"CHAPTER{i+1:02}NAME={name}\n")

    with open(RENAMED_CHAPTERS_FILE.format(filepath.stem), "w+") as f:
        f.writelines(output)
    run(["mkvpropedit", filepath, "--chapters", RENAMED_CHAPTERS_FILE.format(filepath.stem)], check=True)


def entrypoint():
    try:
        main()
    except:
        raise
    finally:
        cleanup()


if __name__ == "__main__":
    main()
