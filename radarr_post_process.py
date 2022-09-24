#!/usr/bin/env python3

import os
import logging
from pathlib import Path
import subprocess

log_file = Path(__file__).parent / "radarr_post_process.log"

logging.basicConfig(filename=log_file, encoding='utf-8', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

event_type = os.environ.get('radarr_eventtype')

if event_type == 'Test':
    logger.info("Received Test Event from Radarr")

if event_type == 'Download':
    full_path = Path(os.environ.get('radarr_moviefile_path')).absolute()

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
