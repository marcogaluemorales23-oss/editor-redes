#!/usr/bin/env bash
# Revisa la entrega antes de decir "listo": formato, códec y sonido.
# Uso: bash nucleo/verificar.sh reels/<nombre>/salida/final.mp4
set -euo pipefail
video="$1"

v=$(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,r_frame_rate -of csv=p=0 "$video")
a=$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of csv=p=0 "$video")
ruido=$(ffmpeg -hide_banner -nostats -i "$video" -af loudnorm=print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
lufs=$(echo "$ruido" | python3 -c 'import json,sys; print(json.load(sys.stdin)["input_i"])')
pico=$(echo "$ruido" | python3 -c 'import json,sys; print(json.load(sys.stdin)["input_tp"])')

echo "Video: $v | Audio: $a | Sonoridad: $lufs LUFS | Pico: $pico dBTP"
ok=1
[[ "$v" == h264,1080,1920,* ]] || { echo "✗ Debe ser H.264 1080x1920"; ok=0; }
[[ "$a" == aac ]] || { echo "✗ El audio debe ser AAC"; ok=0; }
python3 -c "import sys; sys.exit(0 if abs($lufs + 14) <= 1 else 1)" || { echo "✗ Sonoridad fuera de -14 ±1 LUFS"; ok=0; }
python3 -c "import sys; sys.exit(0 if $pico <= -1 else 1)" || { echo "✗ Pico por encima de -1 dBTP"; ok=0; }
[[ $ok == 1 ]] && echo "✓ Entrega OK" || exit 1
