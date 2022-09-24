#!/usr/bin/env python3

import os
import logging
from pathlib import Path
import subprocess

from pymediainfo import MediaInfo

HDR_REPLACE_STR = "{HDR}"


log_file = Path(__file__).parent / "radarr_post_process.log"

logging.basicConfig(filename=log_file, encoding='utf-8', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

event_type = os.environ.get('radarr_eventtype')

if event_type == 'Test':
    logger.info("Received Test Event from Radarr")

if event_type == 'Download':
    full_path = Path(os.environ.get('radarr_moviefile_path')).absolute()

    if HDR_REPLACE_STR in full_path.name:
        media_info = MediaInfo.parse(full_path)
        video_data = media_info.video_tracks[0].to_data()
        hdr_format = video_data.get('other_hdr_format')[0]
        hdr_str = []
        if "Dolby Vision" in hdr_format:
            hdr_str.append("DV")
        if "HDR10+" in hdr_format:
            hdr_str.append("HDR10+")
        elif "HDR10" in hdr_format:
            hdr_str.append("HDR10")

        new_name = str(full_path.name).replace(HDR_REPLACE_STR, ' '.join(hdr_str))

        renamed_path = full_path.rename(full_path.with_name(new_name))

        logger.info(f"Renamed file with detailed HDR info: {new_name}")


    release_group = os.environ.get('radarr_moviefile_releasegroup')
    if release_group:
        with open(log_file, "a") as f:
            subprocess.run(
                ["mkv_append_tag", full_path, "-g", f"Release Group={release_group}"],
                stdout=f, stderr=f
            )
        logger.info("Added release group tag.")

    with open(log_file, "a") as f:
        process = subprocess.run(
                ["mkvmerge", "-o", (full_path.parent / f"{full_path.stem}.mks").absolute(), "-A", "-D", "-B", "-T", "-M", "-s", "eng", full_path],
                stdout=f, stderr=f
        )
        logger.info("Extracted subtitles.")
