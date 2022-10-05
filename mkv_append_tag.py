from pathlib import Path
from subprocess import run

import argparse
import os
import xml.etree.ElementTree as ET

from pymediainfo import MediaInfo


TAGS_SUFFIX = "_tags.xml"
OUTPUT_SUFFIX = "_tags_edited.xml"


def get_args():
    parser = argparse.ArgumentParser(description="Append tags to MKV files")
    parser.add_argument('input', type=str, help="Path to input MKV file")
    parser.add_argument('--general-tags', '-g', type=str, nargs='+', metavar='TAG',
        help="One or more general tags to append, i.e. not associated with a specific track. Tags should follow the format 'key=value'."
    )
    parser.add_argument('--track-tags', '-t', type=str, nargs='+', metavar='TAG',
        help=("One or more track-specific tags to append. "
        "Tags should follow the format 'selector:key=value', where selector specifies the track type and number. "
        "The track type must be one of these characters: 'a' for an audio track, 's' for a subtitle track and 'v' for a video track. "
        "Track numbering starts at 1, similar to mkvmerge. Example: 'a1:Audio Source=5.1 Surround Mix from Blu-ray'")
    )

    return parser.parse_args()


def main():
    args = get_args()
    input_file = Path(args.input).resolve(strict=True)
    xml_filename = input_file.stem + TAGS_SUFFIX

    assert args.general_tags or args.track_tags, "No tags specified, specify at least one tag to append using either --general-tags or --track-tags."

    track_tags_to_append = {}
    if args.track_tags:
        # If track specific tags are passed in, parse them and map them to track UIDs
        media_info = MediaInfo.parse(input_file)

        for track_tag in args.track_tags:
            track_selector, track_tag = track_tag.split(':', 1)
            key, val = track_tag.split('=', 1)
            
            track_uid = get_track_uid_from_selector(media_info, track_selector)
            
            if track_tags_to_append.get(track_uid):
                track_tags_to_append[track_uid].append((key, val))
            else:
                track_tags_to_append[track_uid] = [(key, val)]

    run(["mkvextract", input_file, "tags", xml_filename])

    tree = ET.parse(xml_filename)
    root = tree.getroot()

    for tag in root.iter("Tag"):
        track_uid = tag.find("./Targets/TrackUID")
        if track_uid is not None:
            if track_uid.text in track_tags_to_append:
                for key, val in track_tags_to_append[track_uid.text]:
                    tag.append(generate_simple(key, val))
        else:
            for gen_tag in args.general_tags:
                key, val = gen_tag.split('=', 1)
                tag.append(generate_simple(key, val))

    
    xml_out_filename = input_file.stem + OUTPUT_SUFFIX
    with open(xml_out_filename, "w+") as f:
        tree.write(f, encoding='unicode')

    run(["mkvpropedit", input_file, "-t", f"all:{xml_out_filename}"])


def generate_simple(key, value):
    """
    Generate the tag structure to add a key value pair to the MKV.

    <Simple>
      <Name>key</Name>
      <String>value</String>
    </Simple>
    """
    tree = ET.TreeBuilder()
    tree.start("Simple", {})
    tree.start("Name", {})
    tree.data(key)
    tree.end("Name")
    tree.start("String", {})
    tree.data(value)
    tree.end("String")
    tree.end("Simple")
    return tree.close()


def get_track_uid_from_selector(media_info, track_selector):
    """
    Retrieve track UID from MediaInfo for the given selector string.
    """
    try:
        track_type = track_selector[0]
        track_num = int(track_selector[1:])

        if track_type == 'v':
            return media_info.video_tracks[track_num - 1].to_data()['unique_id']
        elif track_type == 'a':
            return media_info.audio_tracks[track_num - 1].to_data()['unique_id']
        elif track_type == 's':
            return media_info.text_tracks[track_num - 1].to_data()['unique_id']
        else:
            raise ValueError(f"Invalid track type '{track_type}'")
    except IndexError as e:
        raise Exception(f"Could not find track {track_selector}")


def cleanup():
    for suffix in [TAGS_SUFFIX, OUTPUT_SUFFIX]:
        for f in Path('.').glob(f"*{suffix}"):
            os.remove(f)


def entrypoint():
    try:
        main()
    except:
        raise
    finally:
        cleanup()
        

if __name__ == "__main__":
    entrypoint()
