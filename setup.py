from setuptools import setup

setup(
    name='media_utils',
    version='0.1',
    description='A collection of scripts and utilities to manipulate media files.',
    install_requires=[
        'pymediainfo',
        'plexapi',
        'pythumb',
        'tqdm'
    ],
    scripts=[],
    entry_points = {
        'console_scripts': [
            'mkv_append_tag=mkv_append_tag:entrypoint',
            'extract_timecodes=extract_timecodes.extract_sup_timecodes:main',
            'alass_batch=alass_batch:main',
            'combine_chapters=combine_chapters:main',
            'gifenc=gifenc:main',
            'merge_subs=merge_subs:main',
            'set_extra_thumbnail=plex_extras_thumbnail.set_extra_thumbnail:main'
        ],
    }
)