#!/bin/sh
set -eu

expected_digest=${VGG19_SHA256:-}
case "$expected_digest" in
    ''|*[!0123456789abcdefABCDEF]*)
        expected_digest=
        ;;
esac
if [ "${#expected_digest}" -ne 64 ]; then
    echo "Set VGG19_SHA256 to an independently verified SHA-256 for the Oxford VGG-19 Caffe weights." >&2
    exit 1
fi
expected_digest=$(printf '%s' "$expected_digest" | tr 'ABCDEF' 'abcdef')

models_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../models" && pwd)
model=VGG_ILSVRC_19_layers.caffemodel
destination="$models_dir/$model"
temporary=$(mktemp -- "$models_dir/.VGG19-XXXXXXXX.caffemodel")
trap 'rm -f -- "$temporary"' EXIT
trap 'exit 1' HUP INT TERM

curl -q --fail --silent --show-error --proto '=https' \
    --connect-timeout 15 --max-time 600 --max-filesize 629145600 \
    --output "$temporary" \
    "https://www.robots.ox.ac.uk/~vgg/software/very_deep/caffe/$model"

actual_digest=$(sha256sum < "$temporary")
if [ "${actual_digest%% *}" != "$expected_digest" ]; then
    echo "VGG-19 checksum verification failed." >&2
    exit 1
fi

mv -fT -- "$temporary" "$destination"
printf 'Installed verified VGG-19 weights at %s\n' "$destination"
