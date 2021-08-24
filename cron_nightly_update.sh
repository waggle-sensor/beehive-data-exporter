#!/bin/bash -ex

cd $(dirname $0)

# ensure last few days of data chunks are exported
start=$(date -d '4 days ago' +'%Y-%m-%d')
# end only goes until the last *completed* day so we don't include partial data
end=$(date -d '1 day ago' +'%Y-%m-%d')

echo "exporting data"
time ./export_data_chunks.py -m 'iio.*|env.*' "$start" "$end"

# compile SAGE-Data.tar
echo "compiling bundle"
time ./compile_bundle.py

# upload to lcrc
echo "uploading bundle to lcrc"
# NOTE this config is hardcoded for sage+lcrc. we can generalize this later.
time rsync -av --remove-source-files --stats SAGE-Data.tar svcwagglersync:/home/svcwagglersync/waggle/public_html/sagedata/SAGE-Data.tar
