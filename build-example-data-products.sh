#!/bin/bash

# export all data chunks in timeframe
./export_data_chunks.py 2023-01-01 2023-01-01

# export bundles
for project in SAGE DAWN; do
    ./compile_bundle.py --project "${project}" --include "^sys.*" "${project}-sys"
    ./compile_bundle.py --project "${project}" --exclude "^sys.*" "${project}-env"
done
