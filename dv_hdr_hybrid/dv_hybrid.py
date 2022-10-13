import argparse
import sys
from pathlib import Path
from subprocess import run, CalledProcessError

from pymediainfo import MediaInfo


DV_STREAM_SUFFIX = "_dovi.hevc"
BASE_STREAM_SUFFIX = "_hdr10.hevc"
RPU_SUFFIX = "_RPU.bin"
OUT_SUFFIX = "_injected.hevc"

DV_P5_STR = "dvhe.05"


def main():
    parser = argparse.ArgumentParser(description="Inject Dolby Vision metadata from a profile 5 file into an HDR10 file to create a profile 8 video stream.")
    parser.add_argument('ffmpeg', type=str, help="Path to ffmpeg executable")
    parser.add_argument('dovi_tool', type=str, help="Path to dovi_tool executable")
    parser.add_argument('dv', type=str, help="Path to Dolby Vision profile 5 video file (or directory of files)")
    parser.add_argument('hdr10', type=str, help="Path to HDR10 base video file (or directory of files)")
    parser.add_argument('--mkvextract', default=False, type=bool, action=argparse.BooleanOptionalAction, 
        help="Use mkvextract to create raw HEVC stream instead of ffmpeg. In some cases the HEVC stream created by ffmpeg can cause errors, using mkvextract may help."
        )
    parser.add_argument('--dv-name', default=False, type=bool, action=argparse.BooleanOptionalAction, help="Name output files based on DV file instead of HDR10 file.")

    args = parser.parse_args()

    dv_path = Path(args.dv).resolve()
    assert dv_path.exists(), f"Path to DV file does not exist: {dv_path}"

    base_path = Path(args.hdr10).resolve()
    assert base_path.exists(), f"Path to HDR10 base file does not exist: {base_path}"

    both_dirs = dv_path.is_dir() and base_path.is_dir()
    both_files = dv_path.is_file() and base_path.is_file()

    assert both_dirs or both_files, "Paths to DV and HDR10 file(s) must both be directories or both be files."

    if both_dirs:
        print("Batch processing files in directories...")
        dv_files = list(dv_path.glob("*.mkv")).extend(dv_path.glob("*.mp4"))
        base_files = list(base_path.glob("*.mkv")).extend(base_path.glob("*.mp4"))

        dv_files.sort()
        base_files.sort()

        for i, (dv_file, base_file) in enumerate(zip(dv_files, base_files)):
            print(f"Processing file {i + 1} of {len(base_files)}")
            try:
                create_hybrid(args.ffmpeg, args.dovi_tool, dv_file, base_file, args.mkvextract, args.dv_name)
            except CalledProcessError as cpe:
                print(f"Error for file {i + 1}: {cpe}")
            finally:
                cleanup()
    else:
        try:
            create_hybrid(args.ffmpeg, args.dovi_tool, dv_path, base_path, args.mkvextract, args.dv_name)
        except:
            raise
        finally:
            cleanup()


def cleanup():
    print("Cleaning up temp files...\n")
    for suffix in [DV_STREAM_SUFFIX, BASE_STREAM_SUFFIX, RPU_SUFFIX]:
        for f in Path.cwd().glob(f"*{suffix}"):
            f.unlink(missing_ok=True)


def create_hybrid(ffmpeg, dovi_tool, dv_path, base_path, mkvextract=False, dv_name=False):
    dv_info = MediaInfo.parse(dv_path)

    if len(dv_info.video_tracks) > 1:
        print(f"WARNING: {dv_path.name} has multiple video tracks, only using first track.")

    dv_track = dv_info.video_tracks[0].to_data()

    # Confirm that DV file is profile 5
    assert dv_track['hdr_format_profile'] == DV_P5_STR, f"Dolby Vision file is not profile 5, expected {DV_P5_STR}, but was actually {dv_track['hdr_format_profile']}"
    print(f"{dv_path.name} is a Profile 5 file.")

    base_info = MediaInfo.parse(base_path)

    if len(base_info.video_tracks) > 1:
        print(f"WARNING: {base_path.name} has multiple video tracks, only using first track.")

    base_track = base_info.video_tracks[0].to_data()

    # Confirm that DV and Base have the same frame count and frame rate
    dv_framerate = dv_track['frame_rate']
    base_framerate = base_track['frame_rate']
    assert dv_framerate == base_framerate, f"Files do not have matching frame rates, {dv_path.name} has frame rate {dv_framerate} and {base_path.name} has frame rate {base_framerate}."
    print(f"Both files have matching frame rates: {base_framerate}")

    dv_framecount = dv_track['frame_count']
    base_framecount = base_track['frame_count']
    assert dv_framecount == base_framecount, f"Files do not have matching frame counts, {dv_path.name} has frame count {dv_framecount} and {base_path.name} has frame count {base_framecount}."
    print(f"Both files have matching frame counts: {base_framecount}")

    print(f"Extracting HEVC stream from {dv_path.name}...")
    dv_stream = dv_path.stem + DV_STREAM_SUFFIX
    if mkvextract:
        run(["mkvextract", dv_path, "tracks", f"0:{dv_stream}"], check=True)
    else:
        run(
            [ffmpeg, "-loglevel", "warning", "-hide_banner", "-stats", "-i", dv_path, "-c", "copy" ,"-vbsf", "hevc_mp4toannexb", dv_stream],
            check=True
        )

    if base_track.get('framerate_num') and base_track.get('framerate_den'):
        base_framerate_str = f"{base_track.get('framerate_num')}/{base_track.get('framerate_den')}"
    else:
        base_framerate_str = base_framerate

    print(f"Extracting HEVC stream from {base_path.name}...")
    base_stream = base_path.stem + BASE_STREAM_SUFFIX
    if mkvextract:
        run(["mkvextract", base_path, "tracks", f"0:{base_stream}"], check=True)
    else:
        run(
            [ffmpeg, "-loglevel", "warning", "-hide_banner", "-stats", "-i", base_path, "-c", "copy", "-vbsf", f"hevc_metadata=tick_rate={base_framerate_str}:num_ticks_poc_diff_one=1", base_stream],
            check=True
        )

    print("Extracting Dolby Vision RPU...")
    # TODO: Handle cases where RPU conversion fails and metadata requires editing
    run(
        [dovi_tool, "-m", "3", "extract-rpu", dv_stream, "-o", dv_path.stem + RPU_SUFFIX],
        check=True
    )

    print("Injecting DV metadata into HDR10 base...")
    if dv_name:
        out_name = dv_path.stem + OUT_SUFFIX
    else:
        out_name = base_path.stem + OUT_SUFFIX
    run(
        [dovi_tool, "inject-rpu", "-i", base_stream, "--rpu-in", RPU_TEMP, "-o", out_name],
        check=True
    )
    print("Successfully created hybrid video stream!")
    

if __name__ == "__main__":
    main()
