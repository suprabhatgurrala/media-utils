from datetime import datetime
from pathlib import Path
import argparse
import json
import shutil
import sys

from plexapi.server import PlexServer
import tqdm


config_file = Path(__file__) / "config.json"

with open(config_file, 'r') as f:
	config = json.load()

PLEX_MEDIA_PATH = Path(config['PLEX_HOME']) / "Library/Application Support/Plex Media Server/Media"

parser = argparse.ArgumentParser(description="Replace the thumbnail of an Extra in a Plex library.")
parser.add_argument('library', type=str, help="Name of the Plex library which the Extra is in")
parser.add_argument('title', type=str, help="Title of the movie/show of the Extra")
parser.add_argument('extra_name', type=str, help="Name of the Extra")
parser.add_argument('thumbnail', type=str, help="Path to the new thumbnail image") # TODO: Accept a YouTube link and automatically pull the thumbnail

args = parser.parse_args()

plex = PlexServer(config['PLEX_SERVER_URL'], config['PLEX_TOKEN'])
library = plex.library.section(args.library)
titles = library.search(title=args.title)

if len(titles) == 0:
	print(f"No results found for {args.title} in {args.library}")
	sys.exit()
elif len(titles) > 1:
	print(f"{len(titles)} results found for {args.title} in {args.library}, choosing the first result.")

title = titles[0]
print(f"Found title {title.title} ({title.year})")

target_time = None
for extra in title.extras:
	if extra.title == args.extra_name:
		extra_path = Path(extra.locations[0])
		print(f"Found Extra file {extra_path.name}")
		target_time = extra_path.stat().st_ctime

thumb_path = None

for thumb in tqdm(PLEX_MEDIA_PATH.rglob("thumb1.jpg")):
	thumb_time = thumb.stat().st_ctime

	if thumb_time - target_time < 60 * 1000:
		print(f"Found thumbnail directory {thumb}")
		thumb_path = thumb

if thumb_path is None:
	print("Could not find matching thumbnail path.")
	sys.exit()


