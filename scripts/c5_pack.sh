#!/usr/bin/env bash
# C5: pack a rendered set's frame sequences into lossless video, one file per shot, to fit the disk. A 4K PNG frame is
# about 7.8 MB (16:9) and the whole video would not fit; FFV1 (intra-only, bgr0) is about half that and bit-exact.
# Each shot's frames/<shot>/f_NNNN.png become frames/<shot>.mkv (its first frame number in frames/<shot>.start) and
# frames/<shot>.plate.json; the PNGs are removed only after every frame of the pack decodes to the same RGB as its
# PNG (framemd5). Alpha is dropped: every render is opaque. Unpack for random access with
#   ffmpeg -i frames/<shot>.mkv -start_number $(cat frames/<shot>.start) frames/<shot>/f_%04d.png
# Usage: scripts/c5_pack.sh SET
set -euo pipefail
cd "$(dirname "$0")/.."
fr="renders/c5/set_${1^^}/frames"
for d in "$fr"/*/; do
  sid=$(basename "$d")
  # frame numbers sorted as numbers: by name, f_10000 sorts before f_9999 (set G's S33 stopped the pack there)
  nums=$(ls "$d" | grep -o '^f_[0-9]*\.png$' | cut -c3- | cut -d. -f1 | sort -n)
  first=$(head -1 <<< "$nums")
  n=$(wc -l <<< "$nums")
  last=$(tail -1 <<< "$nums")
  [ $((10#$last - 10#$first + 1)) -eq "$n" ] || { echo "$sid: frames not contiguous ($first..$last, $n)"; exit 1; }
  ffmpeg -loglevel error -y -framerate 60 -start_number "$first" -i "$d/f_%04d.png" -c:v ffv1 -level 3 -g 1 \
    -slices 24 -slicecrc 1 -pix_fmt bgr0 "$fr/$sid.mkv"
  a=$(ffmpeg -loglevel error -i "$fr/$sid.mkv" -f framemd5 -pix_fmt rgb24 - | grep -v '^#' | cut -d, -f6 | md5sum)
  b=$(ffmpeg -loglevel error -framerate 60 -start_number "$first" -i "$d/f_%04d.png" -f framemd5 -pix_fmt rgb24 - \
      | grep -v '^#' | cut -d, -f6 | md5sum)
  m=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$fr/$sid.mkv")
  [ "$a" = "$b" ] && [ "$m" -eq "$n" ] || { echo "$sid: pack differs from its frames; PNGs kept"; exit 1; }
  echo "$first" > "$fr/$sid.start"
  [ -f "$d/plate.json" ] && mv "$d/plate.json" "$fr/$sid.plate.json"
  rm -r "$d"
  echo "$sid: $n frames from $first, bit-exact, $(du -h "$fr/$sid.mkv" | cut -f1)"
done
