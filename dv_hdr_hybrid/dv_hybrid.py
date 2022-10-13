import argparse
import os
import sys
import subprocess

from pymediainfo import MediaInfo

DV_STREAM_TEMP = "dovi.hevc"
BASE_STREAM_TEMP = "hdr10.hevc"
RPU_TEMP = "RPU.bin"

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

    dv_path = os.path.realpath(args.dv)
    assert os.path.exists(dv_path), f"Path to DV file does not exist: {dv_path}"

    base_path = os.path.realpath(args.hdr10)
    assert os.path.exists(base_path), f"Path to HDR10 base file does not exist: {base_path}"

    both_dirs = os.path.isdir(dv_path) and os.path.isdir(base_path)
    both_files = os.path.isfile(dv_path) and os.path.isfile(base_path)

    assert both_dirs or both_files, "Paths to DV and HDR10 file(s) must both be directories or both be files."

    if both_dirs:
        print("Batch processing files in directories...")
        dv_files = [s for s in os.listdir(dv_path) if os.path.splitext(s)[1] == ".mkv" or os.path.splitext(s)[1] == ".mp4"]
        base_files = [s for s in os.listdir(base_path) if os.path.splitext(s)[1] == ".mkv" or os.path.splitext(s)[1] == ".mp4"]

        dv_files.sort()
        base_files.sort()

        for i, (dv_file, base_file) in enumerate(zip(dv_files, base_files)):
            print(f"Processing file {i + 1} of {len(base_files)}")
            try:
                create_hybrid(args.ffmpeg, args.dovi_tool, os.path.join(dv_path, dv_file), os.path.join(base_path, base_file), args.mkvextract, args.dv_name)
            except subprocess.CalledProcessError as cpe:
                print(f"Error for file {i + 1}: {cpe}")
            finally:
                cleanup()
    else:
        create_hybrid(args.ffmpeg, args.dovi_tool, dv_path, base_path, args.mkvextract, args.dv_name)
        cleanup()


def cleanup():
    print("Cleaning up temp files...\n")
    for f in [DV_STREAM_TEMP, BASE_STREAM_TEMP, RPU_TEMP]:
        if os.path.exists(f):
            os.remove(f)


def create_hybrid(ffmpeg, dovi_tool, dv_path, base_path, mkvextract=False, dv_name=False):
    dv_info = MediaInfo.parse(dv_path)

    if len(dv_info.video_tracks) > 1:
        print("WARNING: Dolby Vision file has multiple video tracks, only using first track.")

    dv_track = dv_info.video_tracks[0].to_data()

    # Confirm that DV file is profile 5
    assert dv_track['hdr_format_profile'] == DV_P5_STR, f"Dolby Vision file is not profile 5, expected {DV_P5_STR}, but was actually {dv_track['hdr_format_profile']}"
    print(f"{os.path.basename(dv_path)} is a Profile 5 file.")

    base_info = MediaInfo.parse(base_path)

    if len(base_info.video_tracks) > 1:
        print("WARNING: Base HDR10 file has multiple video tracks, only using first track.")

    base_track = base_info.video_tracks[0].to_data()

    # Confirm that DV and Base have the same frame count and frame rate
    dv_framerate = dv_track['frame_rate']
    base_framerate = base_track['frame_rate']
    assert dv_framerate == base_framerate, f"Files do not have matching frame rates, DV file has frame rate {dv_framerate} and HDR10 base file has frame rate {base_framerate}."
    print(f"Both files have matching frame rates: {base_framerate}")

    dv_framecount = dv_track['frame_count']
    base_framecount = base_track['frame_count']
    assert dv_framecount == base_framecount, f"Files do not have matching frame counts, DV file has frame count {dv_framecount} and HDR10 base file has frame count {base_framecount}."
    print(f"Both files have matching frame counts: {base_framecount}")

    print(f"Extracting HEVC stream from {os.path.basename(dv_path)}...")
    if mkvextract:
        subprocess.run(["mkvextract", dv_path, "tracks", f"0:{DV_STREAM_TEMP}"], check=True)
    else:
        subprocess.run(
            [ffmpeg, "-loglevel", "warning", "-hide_banner", "-stats", "-i", dv_path, "-c", "copy" ,"-vbsf", "hevc_mp4toannexb", DV_STREAM_TEMP],
            check=True
        )

    if base_track.get('framerate_num') and base_track.get('framerate_den'):
        base_framerate_str = f"{base_track.get('framerate_num')}/{base_track.get('framerate_den')}"
    else:
        base_framerate_str = base_framerate

    print(f"Extracting HEVC stream from {os.path.basename(base_path)}...")
    if mkvextract:
        subprocess.run(["mkvextract", base_path, "tracks", f"0:{BASE_STREAM_TEMP}"], check=True)
    else:
        subprocess.run(
            [ffmpeg, "-loglevel", "warning", "-hide_banner", "-stats", "-i", base_path, "-c", "copy", "-vbsf", f"hevc_metadata=tick_rate={base_framerate_str}:num_ticks_poc_diff_one=1", BASE_STREAM_TEMP],
            check=True
        )

    print("Extracting Dolby Vision RPU...")
    # TODO: Handle cases where RPU conversion fails and metadata requires editing
    subprocess.run(
        [dovi_tool, "-m", "3", "extract-rpu", DV_STREAM_TEMP],
        check=True
    )

    print("Injecting DV metadata into HDR10 base...")
    if dv_name:
        out_name_base = dv_path
    else:
        out_name_base = base_path
    base_name = os.path.basename(out_name_base)
    name, ext = os.path.splitext(base_name)
    out_name = name + '_injected.hevc'
    subprocess.run(
        [dovi_tool, "inject-rpu", "-i", BASE_STREAM_TEMP, "--rpu-in", RPU_TEMP, "-o", out_name],
        check=True
    )
    print("Successfully created hybrid video stream!")
    

if __name__ == "__main__":
    main()
