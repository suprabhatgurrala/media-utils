import argparse
import subprocess
import shlex
from pathlib import Path


def main():
	parser = argparse.ArgumentParser(description='Generate a gif from a video file.')
	parser.add_argument('input', type=str, help="Input video file")
	parser.add_argument('--start', default=0, help='Start timestamp (in seconds) to generate the video. By default will start at the beginning of the video.')
	parser.add_argument('--length', default=30, help='Length of the gif in seconds.')

	args = parser.parse_args()

	input_path = Path(args.input).resolve()
	outpath = f'{input_path.parent / input_path.stem}.gif'

	cmd_split = ['ffmpeg', '-v', 'quiet', '-stats', '-ss', args.start, '-t', args.length, '-i', input_path,
			'-filter_complex', '[0:v] split [a][b];[a] palettegen [p];[b][p] paletteuse', outpath]

	subprocess.run(cmd_split, check=True)

if __name__ == "__main__":
    main()
