# Creating Dolby Vision HDR10 Hybrids from a Profile 5 and HDR10 files
Metadata from a Dolby Vision profile 5 video stream can be extracted and injected into an HDR10 video stream.
Assuming both files are mastered from the same source, this allows you to get backwards compatibility with HDR10 in addition to the dynamic metadata from Dolby Vision in a single video stream.

## Prerequisites
- [`dovi_tool`](https://github.com/quietvoid/dovi_tool) by quiet_void - to manipulate Dolby Vision metadata
- [`ffmpeg`](https://ffmpeg.org/) - to extract video streams
- [MediaInfo](https://mediaarea.net/en/MediaInfo) - verify video metadata
- [MKVToolnix](https://mkvtoolnix.download/) - to mux into MKV containers (optional)

## Script
The script [`dv_hybrid.py`](dv_hybrid.py) can automate the following steps and create a hybrid video stream for you.
The only dependency is the package [`pymediainfo`](https://pypi.org/project/pymediainfo/).

```console
$ python dv_hybrid.py --help
usage: dv_hybrid.py [-h] ffmpeg dovi_tool dv hdr10

Inject Dolby Vision metadata from a profile 5 file into an HDR10 file to create a profile 8 video stream.

positional arguments:
  ffmpeg      Path to ffmpeg executable
  dovi_tool   Path to dovi_tool executable
  dv          Path to Dolby Vision profile 5 video file (or directory of files)
  hdr10       Path to HDR10 base video file (or directory of files)

options:
  -h, --help  show this help message and exit
```

## Steps
Assume that we have the Dolby Vision and HDR10 files in an MKV container as `dv.mkv` and `hdr10.mkv` respectively.

1. Confirm that both video files have the same frame count and frame rate.
    ```console
    $ mediainfo "--Output=Video;Frame Count: %FrameCount% frames, Frame Rate: %FrameRate% fps dv.mkv"
    Frame Count: 160754 frames, Frame Rate: 23.976 fps
    $ mediainfo "--Output=Video;Frame Count: %FrameCount% frames, Frame Rate: %FrameRate% fps hdr10.mkv"
    Frame Count: 160754 frames, Frame Rate: 23.976 fps
    ```

    If the frame counts differ, then the files are likely from different sources and the Dolby Vision metadata might need to be edited to be in sync with the HDR10 file. This is beyond the scope of this document but is possible using `dovi_tool`.

2. Extract the HEVC video streams from both videos.
    ```console
    ffmpeg -i dv.mkv -c copy -vbsf hevc_mp4toannexb dovi.hevc
    ```
    ```console
    ffmpeg -i hdr10.mkv -c copy -vbsf hevc_metadata=tick_rate=24000/1001:num_ticks_poc_diff_one=1 hdr10.hevc
    ```
    Note that sometimes extracting the HEVC stream can sometimes lose frame rate information, which is why we are manually inputting the framerate in the second line.
    Most video files will be 23.976 (24000/1001) fps, but some may be 24.000 fps, 25.000 fps, or something else.
    Make sure to use the correct frame rate.

3. Extract the Dolby Vision metadata and convert it to Profile 8, which allows for HDR10 fallback.
    ```console
    dovi_tool -m 3 extract-rpu dovi.hevc
    ```
    This will output the metadata to a file named `RPU.bin`

    This line may return an error looking something like this:

    ```
    Error: Condition failed: `self.max_display_mastering_luminance <= MAX_PQ_LUMINANCE` (38528 vs 10000)
    ```

    If this is the case, the RPU needs to be edited to get the correct HDR10 metadata.
    Extract the RPU without any conversion by dropping the `-m` flag:

    ```
    dovi_tool extract-rpu dovi.hevc
    ```

    Create a JSON file named `edit.json` with the following and fill in the metadata based on the HDR10 file:

    ```json
    {
        "mode": 3,
        "level6": {
            "max_display_mastering_luminance": 10000,
            "min_display_mastering_luminance": <int metadata here>,
            "max_content_light_level": <int metadata here>,
            "max_frame_average_light_level": <int metadata here>
        }
    }
    ```
    Metadata from the HDR10 file can be read using mediainfo.

    ```console
    $ mediainfo hdr10.hevc
    General
    Complete name                            : hdr10.hevc
    Format                                   : HEVC
    Format/Info                              : High Efficiency Video Coding
    File size                                : 18.6 GiB

    Video
    Format                                   : HEVC
    Format/Info                              : High Efficiency Video Coding
    Format profile                           : Main 10@L5@High
    HDR format                               : SMPTE ST 2086, HDR10 compatible
    Width                                    : 3 840 pixels
    Height                                   : 2 076 pixels
    Display aspect ratio                     : 1.85:1
    Frame rate                               : 23.976 (24000/1001) FPS
    Color space                              : YUV
    Chroma subsampling                       : 4:2:0 (Type 2)
    Bit depth                                : 10 bits
    Color range                              : Limited
    Color primaries                          : BT.2020
    Transfer characteristics                 : PQ
    Matrix coefficients                      : BT.2020 non-constant
    Mastering display color primaries        : Display P3
    Mastering display luminance              : min: 0.0050 cd/m2, max: 1000 cd/m2
    Maximum Content Light Level              : 1438 cd/m2
    Maximum Frame-Average Light Level        : 133 cd/m2
    ```

    We are interested in the last 3 lines, Mastering display luminance, Maximum Content Light Level, and Maximum Frame-Average Light Level.
    
    Note that all of the values must be integers. `min_display_mastering_luminance` is commonly a fractional number such as `0.005`, so enter the value multiplied by 10000. This only applies to the field with the fractional value, enter the other fields as usual.

    Once you've created the JSON, we can now edit the RPU using the correct metadata. Note that the `"mode": 3` line in our JSON is telling `dovi_tool` to convert from profile 5 to profile 8.

    ```
    dovi_tool editor -i RPU.bin -j edit.json -o RPU_edited.bin
    ```

4. Inject the converted RPU into the HDR10 stream.
    ```console
    dovi_tool inject-rpu -i hdr10.hevc --rpu-in RPU.bin -o injected.hevc
    ```
5. Use `mkvmerge` or MKVToolnixGUI to put the HEVC stream back into an MKV container along with the audio from the 
