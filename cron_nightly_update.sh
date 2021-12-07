#!/bin/bash -e

DATA_DIR="${DATA_DIR:-data}"
UPLOAD_HOST="${UPLOAD_HOST:-bebop.lcrc.anl.gov}"
UPLOAD_USER="${UPLOAD_USER:-svcwagglersync}"
UPLOAD_KEY="${UPLOAD_KEY:-~/.ssh/lcrc}"
UPLOAD_DIR="${UPLOAD_DIR:-/home/svcwagglersync/waggle/public_html/sagedata/}"

upload_files() {
    for filename in $*; do
        rsync \
            --verbose \
            --archive \
            --remove-source-files \
            --stats \
            -e "ssh -i ${UPLOAD_KEY} -o StrictHostKeyChecking=no" \
            "${filename}" \
            "${UPLOAD_USER}@${UPLOAD_ADDR}:${UPLOAD_DIR}/${filename}"
    done
}

cd $(dirname $0)

echo "starting job"
echo "DATA_DIR=${DATA_DIR}"
echo "UPLOAD_ADDR=${UPLOAD_ADDR}"
echo "UPLOAD_USER=${UPLOAD_USER}"
echo "UPLOAD_KEY=${UPLOAD_KEY}"
echo "UPLOAD_DIR=${UPLOAD_DIR}"

# ensure last few days of data chunks are exported
start=$(date -d '4 days ago' +'%Y-%m-%d')
# end only goes until the last *completed* day so we don't include partial data
end=$(date -d '1 day ago' +'%Y-%m-%d')

echo "exporting data"
time ./export_data_chunks.py --datadir="${DATA_DIR}" --exclude "^sys.*" "${start}" "${end}"

# compile SAGE-Data.tar
echo "compiling bundle"
time ./compile_bundle.py --datadir="${DATA_DIR}"

# upload to lcrc at:
# https://web.lcrc.anl.gov/public/waggle/sagedata/SAGE-Data.tar
echo "uploading bundle"

# NOTE this config is hardcoded for sage+lcrc. we can generalize this later.
time upload_files SAGE-Data.tar

# generate and upload prometheus job metrics to lcrc at:
# https://web.lcrc.anl.gov/public/waggle/sagedata/metrics.prom
echo "uploading metrics"
cat > metrics.prom <<EOF
# HELP job_last_success_unixtime UNIX epoch time when job passed.
# TYPE job_last_success_unixtime gauge
job_last_success_unixtime{job="sage_data_bundle"} $(date -u +%s)
# HELP job_duration_seconds Job run duration in seconds.
# TYPE job_duration_seconds gauge
job_duration_seconds{job="sage_data_bundle"} $SECONDS
EOF

time upload_files metrics.prom
