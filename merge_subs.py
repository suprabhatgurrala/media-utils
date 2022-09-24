import argparse
import os
import sys

from pymediainfo import MediaInfo

def main():
    parser = argparse.ArgumentParser(description="Intelligently merge MKV files with corresponding subtitle files.")
    parser.add_argument('outpath', type=str, help="Output path for merged files.")
    # TODO
    # parser.add_argument('--no-subs', action='store_true',
    #     help="Flag to signal to simply process the existing tracks without an external subtitle file.")

    args = parser.parse_args()

    outpath = os.path.realpath(args.outpath)

    if not os.path.exists(outpath):
        print("Output path does not exist.")
        sys.exit()

    files = [s for s in os.listdir(os.getcwd()) if os.path.splitext(s)[1] == ".mkv" or os.path.splitext(s)[1] == ".mp4"]
    files.sort()

    for i, file in enumerate(files):
        print("File {} of {}".format(i + 1, len(files)))
        print("Merging {}".format(file))
        name, ext = os.path.splitext(file)

        if os.path.exists(name + ".srt"):
            subtitle_file = name + ".srt"
        elif os.path.exists(name + ".eng.srt"):
            subtitle_file = name + ".eng.srt"
        elif os.path.exists(name + ".en.srt"):
            subtitle_file = name + ".en.srt"
        elif os.path.exists(name + ".sup"):
            subtitle_file = name + ".sup"
        else:
            print("No matching subtitle file found, skipping file.")
            continue
        
        media_info = MediaInfo.parse(file)
        
        audio_tracks = []
        subtitle_tracks = []

        track_order = []

        for track in media_info.tracks:
            if track.track_type == "Video":
                # Video tracks are passed through and will be first in track order
                # TODO: track_id - 1 is not guaranteed to be the correct track id in mkvmerge
                # See this link for info https://gitlab.com/mbunkus/mkvtoolnix/-/wikis/About-track-UIDs,-track-numbers-and-track-IDs
                track_order.append("0:{}".format(track.track_id - 1))

            if track.track_type == "Audio":
                audio_tracks.append(track)

            if track.track_type == "Text":
                subtitle_tracks.append(track)

        # Handle audio tracks
        main_audio_tracks = []
        commentary_audio_tracks = []

        if len(audio_tracks) > 1:
            # Determine which audio tracks to keep
            for track in audio_tracks:
                if ('lossless' in track.compression_mode.lower()):
                    main_audio_tracks.append(track)
                elif (track.title) and ("commentary" in track.title.lower()):
                    print(f"Commentary audio track found. Track {track.track_id} - {track.title}")
                    commentary_audio_tracks.append(track)
        elif len(audio_tracks) == 1:
            # There's only one audio track, it must be the main track
            main_audio_tracks.append(audio_tracks[0])
        else:
            print("No audio tracks found, skipping file.")
            continue

        # Set track order and flags for audio tracks

        audio_track_ids = []
        audio_track_params = []

        for track in main_audio_tracks:
            print(f"Lossless audio track found. Track {track.track_id} - {track.language} - {track.title}")
            track_id = str(track.track_id - 1)
            audio_track_ids.append(track_id)
            audio_track_params.append("--forced-track {}:no".format(track_id))
            audio_track_params.append("--default-track {}:yes".format(track_id))
            audio_track_params.append("--compression '{}:none'".format(track_id))
            track_order.append("0:{}".format(track_id))
            if len(main_audio_tracks) > 1 and track.language.lower() == "en":
                # Should handle cases where an English dub is wanted as a secondary audio track
                print("Found English main track, dropping remaining lossless tracks.")
                break
        
        if commentary_audio_tracks:
            for track in commentary_audio_tracks:
                track_id = str(track.track_id - 1)
                audio_track_ids.append(track_id)
                audio_track_params.append("--default-track {}:no".format(track_id))
                audio_track_params.append("--compression '{}:none'".format(track_id))
                track_order.append("0:{}".format(track_id))

        audio_flags = "-a " + ",".join(audio_track_ids)
        audio_flags += " " + " ".join(audio_track_params)

        # Handle subtitle tracks
        commentary_sub_tracks = []
        forced_sub_tracks = []

        for track in subtitle_tracks:
            if track.language == "en":
                if track.forced == "Yes" or (
                    (track.title) and (
                        ("forced" in track.title.lower()) or ("foreign" in track.title.lower())
                        )
                    ):
                    forced_sub_tracks.append(track)
                    print("Forced subtitle track found. Track {} - {}".format(track.track_id, track.title))
                if (track.title) and ("commentary" in track.title.lower()):
                    commentary_sub_tracks.append(track)
                    print("Commentary subtitle track found. Track {} - {}".format(track.track_id, track.title))

        # Set track order and flags for subtitle tracks
        sub_tracks = []
        sub_params = []
        
        if len(forced_sub_tracks) > 0:
            for forced_track in forced_sub_tracks:
                track_id = forced_track.track_id - 1
                sub_tracks.append(str(track_id))
                sub_params.append("--forced-track {}:yes".format(track_id))
                sub_params.append("--default-track {}:no".format(track_id))
                sub_params.append("--track-name '{}:Forced'".format(track_id))
                sub_params.append("--compression '{}:none'".format(track_id))
                track_order.append("0:{}".format(track_id))

        track_order.append("1:0") # External subtitle comes after forced tracks, and before commentary tracks

        if len(commentary_sub_tracks) > 0: 
            for commentary_track in commentary_sub_tracks:
                track_id = commentary_track.track_id - 1
                sub_tracks.append(str(track_id))
                sub_params.append("--default-track {}:no".format(track_id))
                sub_params.append("--compression '{}:none'".format(track_id))
                track_order.append("0:{}".format(track_id))

        if len(sub_tracks) > 0:
            sub_flags = "-s " + ",".join(sub_tracks)
        else:
            sub_flags = "-S" # Do not copy any subtitles if none are of interest

        sub_flags += " " + " ".join(sub_params)

        track_order_flag = ",".join(track_order)

        output_name = os.path.join(outpath, name + '.mkv')
        
        merge_cmd = f"mkvmerge -o \"{output_name}\" --no-global-tags {audio_flags} {sub_flags} '(' \"{file}\" ')' --language 0:eng --default-track 0:no '(' \"{subtitle_file}\" ')' --title \"\" --track-order {track_order_flag}"
            
        remove_tags_cmd = f'mkvpropedit \"{output_name}\" --edit track:a1 --delete name --edit track:v1 --delete name'

        if os.path.exists(name + ".chapters.txt"):
            print("Chapters file found, integrating chapters...")
            remove_tags_cmd += f" --chapters '{name + '.chapters.txt'}'"

        os.system(merge_cmd)
        os.system(remove_tags_cmd)
        
        print()


if __name__ == "__main__":
    main()
