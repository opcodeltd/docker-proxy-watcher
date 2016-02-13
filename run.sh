#!/bin/bash

ROOT=$(cd $(dirname $0); pwd)

echo "Using root: $ROOT"

cd "$ROOT"
. bin/activate
./docker-gen --watch --notify="$ROOT/generate.py" json.tmpl info.json
