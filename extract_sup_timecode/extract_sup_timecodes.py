import argparse
from itertools import pairwise
from pathlib import Path

from pgsreader import PGSReader


OUT_FORMAT = "timecodes-{path_stem}.srt"


def main():
    parser = argparse.ArgumentParser(description="Extract timecodes from a .sup file and output into a .srt file.")
    parser.add_argument("path", type=str, help="Path to .sup file or directory containing .sup files.")

    args = parser.parse_args()

    filepath = Path(args.path).resolve()

    assert filepath.exists(), f"{filepath} does not exist."

    if filepath.is_file():
        outpath = filepath.parent / OUT_FORMAT.format(path_stem=filepath.stem)
        extract_timecodes(filepath, outpath)
    elif filepath.is_dir():
        sup_paths = list(filepath.glob("*.sup"))
        sup_paths.sort()
        print(f"Batch processing {len(sup_paths)} files")
        for i, sup_path in enumerate(sup_paths):
            print(f"Extracting time codes for file {i + 1} of {len(sup_paths)}: {sup_path.name}")
            extract_timecodes(sup_path, sup_path.parent / OUT_FORMAT.format(path_stem=sup_path.stem))
    else:
        raise ValueError(f"{filepath} is not a directory or file.")


def extract_timecodes(sup_filepath, outpath):
    """
    Extracts timecodes from provided .sup file and outputs a .srt file
    """
    pgs = PGSReader(sup_filepath)
    ds_iter = pgs.iter_displaysets()

    out_lines = []

    j = 1

    for ds, next_ds in pairwise(ds_iter):
        if len(ds.ods) > 0:
            start_ms = ds.ods[0].presentation_timestamp
            end_ms = next_ds.wds[0].presentation_timestamp
            out_lines.append(f"{j + 1}\n{ms_to_srt_format(start_ms)} --> {ms_to_srt_format(end_ms)}\n\n")
            j += 1
    
    with open(outpath, "w+") as out:
        out.writelines(out_lines)

    print("Successfully extracted timecodes.")


def ms_to_srt_format(ms):
    """
    Helper method to convert a float representing milliseconds to SRT timecode format: HH:MM:SS.sss
    """
    hours, ms = divmod(ms, 1000 * 60 * 60)
    minutes, ms = divmod(ms, 1000 * 60)
    seconds, ms = divmod(ms, 1000)
    return f"{hours:02.0f}:{minutes:02.0f}:{seconds:02.0f},{ms:03.0f}"


if __name__ == "__main__":
    main()
