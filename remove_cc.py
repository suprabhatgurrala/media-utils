import argparse
import subprocess

from pathlib import Path


OUT_SUFFIX = "_no_cc.mkv"


def main():
    parser = argparse.ArgumentParser(description="Use ffmpeg to remove EIA-608 embedded closed captions.")
    parser.add_argument('path', type=str, help="Path to MKV file or directory of MKV files.")

    args = parser.parse_args()

    target_path = Path(args.path)

    if target_path.is_dir():
        for file in target_path.glob("*.mkv"):
            remove_cc(file)
    else:
        remove_cc(target_path)


def remove_cc(path):
    out_name = path.stem + OUT_SUFFIX
    subprocess.run(
        ["ffmpeg", "-i", path, "-codec", "copy", "-bsf:v", "filter_units=remove_types=6", out_name],
        check=True
    )


if __name__ == "__main__":
    main()
