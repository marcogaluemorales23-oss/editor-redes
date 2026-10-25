#!/usr/bin/env bash
# Descarga los modelos que usa el núcleo (no van a git por tamaño).
set -euo pipefail
cd "$(dirname "$0")" && mkdir -p modelos && cd modelos
G=https://storage.googleapis.com/mediapipe-models
[ -f blaze_face_short_range.tflite ] || curl -sSL -o blaze_face_short_range.tflite $G/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite
[ -f face_landmarker.task ] || curl -sSL -o face_landmarker.task $G/face_landmarker/face_landmarker/float16/latest/face_landmarker.task
[ -f selfie_multiclass.tflite ] || curl -sSL -o selfie_multiclass.tflite $G/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite
[ -f rvm_mobilenetv3_fp32.onnx ] || curl -sSL -o rvm_mobilenetv3_fp32.onnx https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx
echo "modelos listos: $(ls)"
