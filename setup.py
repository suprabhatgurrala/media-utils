from setuptools import setup

setup(
    name='media_utils',
    version='0.1',
    description='A collection of scripts and utilities to manipulate meda files.',
    scripts=[],
    entry_points = {
        'console_scripts': [
            'mkv_append_tag=mkv_append_tag:entrypoint',
            'extract_timecodes=extract_timecodes.extract_sup_timecodes:main'
        ],
    }
)