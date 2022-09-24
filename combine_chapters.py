import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Combine two MKV chapters files by taking timestamps from one file and names from the other.")
    parser.add_argument("times", help="A simple text representation of MKV chapters with the desired timestamps")
    parser.add_argument("names", help="A simple text representation of MKV chapters with the desired names")

    args = parser.parse_args()

    chapter_times = args.times
    chapter_names = args.names


    names = []
    times = []

    with open(chapter_names) as f:
        for line in f:
            if "NAME" in line:
                names.append(line.split("=")[1].strip())

    with open(chapter_times) as f:
        for line in f:
            if "NAME" not in line:
            	times.append(line.split("=")[1].strip())

    output_name = os.path.basename(chapter_times)

    with open(output_name + "_combined.chapters.txt", "w") as f:
        for i in range(len(times)):
            f.write("CHAPTER{:02}={}\n".format(i + 1, times[i]))
            f.write("CHAPTER{:02}NAME={}\n".format(i + 1, names[i]))


if __name__ == "__main__":
    main()
