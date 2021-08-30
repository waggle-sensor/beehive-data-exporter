#!/bin/bash -e

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

# upload to lcrc at:
# https://web.lcrc.anl.gov/public/waggle/sagedata/SAGE-Data.tar
echo "uploading bundle to lcrc"
# NOTE this config is hardcoded for sage+lcrc. we can generalize this later.
time rsync -av --remove-source-files --stats SAGE-Data.tar svcwagglersync:/home/svcwagglersync/waggle/public_html/sagedata/SAGE-Data.tar

# generate and upload prometheus job metrics to lcrc at:
# https://web.lcrc.anl.gov/public/waggle/sagedata/metrics.prom
echo "uploading metrics to lcrc"
cat > metrics.prom <<EOF
# HELP job_last_success_unixtime UNIX epoch time when job passed.
# TYPE job_last_success_unixtime gauge
job_last_success_unixtime{job="sage_data_bundle"} $(date -u +%s)
# HELP job_duration_seconds Job run duration in seconds.
# TYPE job_duration_seconds gauge
job_duration_seconds{job="sage_data_bundle"} $SECONDS
EOF

time rsync -av --remove-source-files --stats metrics.prom svcwagglersync:/home/svcwagglersync/waggle/public_html/sagedata/metrics.prom
