from datetime import datetime
from pathlib import Path
import argparse
import json
import shutil
import sys

from plexapi.server import PlexServer
from pythumb import Thumbnail
from tqdm import tqdm


CONFIG_PATH = Path(__file__).parent / "config.json"


def main():
	with open(CONFIG_PATH, 'r') as f:
		config = json.load(f)
	
	plex_media_path = Path(config['PLEX_HOME']) / "Library/Application Support/Plex Media Server/Media"
	
	parser = argparse.ArgumentParser(description="Replace the thumbnail of an Extra in a Plex library.")
	parser.add_argument('library', type=str, help="Name of the Plex library which the Extra is in")
	parser.add_argument('title', type=str, help="Title of the movie/show of the Extra")
	parser.add_argument('extra_name', type=str, help="Name of the Extra")
	parser.add_argument('thumbnail', type=str, help="Path to the new thumbnail image or a YouTube link")

	args = parser.parse_args()

	plex = PlexServer(config['PLEX_SERVER_URL'], config['PLEX_TOKEN'])
	library = plex.library.section(args.library)
	titles = library.search(title=args.title)

	yt = False
	if args.thumbnail[0:4] == "http":
		t = Thumbnail(args.thumbnail)
		t.fetch()
		thumb_path = Path(t.save('.', overwrite=True))
		yt = True
	else:
		thumb_path = Path(args.thumbnail)
		if not thumb_path.exists():
			print(f"{thumb_path} does not exist.")
			sys.exit()

	if len(titles) == 0:
		print(f"No results found for {args.title} in {args.library}")
		sys.exit()
	elif len(titles) > 1:
		print(f"{len(titles)} results found for {args.title} in {args.library}, choosing the first result.")

	title = titles[0]
	print(f"Found title {title.title} ({title.year})")

	target_time = None
	extra_path = None
	for extra in title.extras():
		if extra.title == args.extra_name:
			extra_path = Path(extra.locations[0])
			target_time = datetime.fromtimestamp(extra_path.stat().st_mtime)
			print(f'Found Extra file "{extra_path.name}", created on {target_time.isoformat()}')

	if extra_path is None or target_time is None:
		print(f"Could not find an Extra matching {args.extra_name}")
		sys.exit()

	print("Searching for matching thumbnail path...")
	thumb_paths = []
	closest_thumb = None
	min_delta = float('inf')
	for thumb in tqdm(plex_media_path.rglob("thumb1.jpg")):
		thumb_time = datetime.fromtimestamp(thumb.stat().st_mtime)

		delta = abs(thumb_time - target_time).total_seconds()

		if delta < 120:
			thumb_paths.append(thumb)
		if delta < min_delta:
			closest_thumb = thumb_time, thumb
			min_delta = delta

	if len(thumb_paths) == 0:
		print("\nCould not find matching thumbnail path.")
		print(f"Closest thumbnail to edit time is: {closest_thumb[0]}\n{closest_thumb[1]}")
		sys.exit()
	elif len(thumb_paths) > 1:
		print("There are multiple possible matching thumbnail paths:")
		for path in thumb_paths:
			print(path)
		sys.exit()
	else:
		print(f"Found matching thumbnail path: {thumb_paths[0]}")

	thumb_paths[0].unlink()
	shutil.copy2(thumb_path, thumb_paths[0])
	print("Successfully replaced thumbnail.")

	if yt:
		thumb_path.unlink()

	# TODO: Removing and re-adding the file will force Plex to use the new thumbnail
	# shutil.move(extra_path, "..")
	# library.update()
	# shutil.move(extra_path, "..")
	# library.update()


if __name__ == "__main__":
    main()
