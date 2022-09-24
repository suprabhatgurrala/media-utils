import argparse
import subprocess

from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Use alass to synchronize a batch of subtitles.")
    parser.add_argument('sync_path', type=str, help="Path to in-sync subtitles")
    parser.add_argument('oos_path', type=str, help="Path to out-of-sync subtitles")
    parser.add_argument('-g', '--guess-framerate', default=False, type=bool, action=argparse.BooleanOptionalAction, help="enables guessing and correcting of framerate differences between reference file and input file")
    parser.add_argument('-s', '--split', default=True, type=bool, action=argparse.BooleanOptionalAction, help="synchronize subtitles by looking for splits/breaks")

    args = parser.parse_args()

    synced_path = Path(args.sync_path)
    oos_path = Path(args.oos_path)

    synced_files = sorted(list(synced_path.glob("*.srt")))
    oos_files = sorted(list(oos_path.glob("*.srt")))

    assert len(synced_files) == len(oos_files), f"Mismatched number of files, found {len(synced_files)} in-sync subtitles and {len(oos_files)} out-of-sync subtitles."

    for i, (synced_file, oos_file) in enumerate(zip(synced_files, oos_files)):
        print(f"Syncing {oos_file.name} to {synced_file.name},  {i + 1} of {len(synced_files)}")
        out_name = synced_file.stem + "-synced" + synced_file.suffix

        cmd = ["alass", synced_file, oos_file, out_name]

        if not args.guess_framerate:
            cmd.append("-g")
        if not args.split:
            cmd.append("-l")

        subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()
