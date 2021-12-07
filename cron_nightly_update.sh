#!/bin/bash -e

cd $(dirname $0)

DATA_DIR="${DATA_DIR:-data}"
UPLOAD_HOST="${UPLOAD_HOST:-bebop.lcrc.anl.gov}"
UPLOAD_USER="${UPLOAD_USER:-svcwagglersync}"
UPLOAD_KEY="${UPLOAD_KEY:-~/.ssh/lcrc}"
UPLOAD_DIR="${UPLOAD_DIR:-/home/svcwagglersync/waggle/public_html/sagedata/}"

echo "DATA_DIR=${DATA_DIR}"
echo "UPLOAD_ADDR=${UPLOAD_ADDR}"
echo "UPLOAD_USER=${UPLOAD_USER}"
echo "UPLOAD_KEY=${UPLOAD_KEY}"
echo "UPLOAD_DIR=${UPLOAD_DIR}"

export_data_chunks() {
    echo "exporting data chunks"
    # ensure last few days of data chunks are exported in case new data has arrived
    start=$(date -d '4 days ago' +'%Y-%m-%d')
    # end only goes until the last *completed* day so we don't include partial data
    end=$(date -d '1 day ago' +'%Y-%m-%d')
    ./export_data_chunks.py --datadir="${DATA_DIR}" --exclude "^sys.*" "${start}" "${end}"
}

compile_data_bundle() {
    echo "compiling bundle"
    ./compile_bundle.py --datadir="${DATA_DIR}"
}

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

write_metrics() {
    cat > "${1}" <<EOF
# HELP job_last_success_unixtime UNIX epoch time when job passed.
# TYPE job_last_success_unixtime gauge
job_last_success_unixtime{job="sage_data_bundle"} $(date -u +%s)
# HELP job_duration_seconds Job run duration in seconds.
# TYPE job_duration_seconds gauge
job_duration_seconds{job="sage_data_bundle"} $SECONDS
EOF
}

upload_data_bundle() {
    echo "uploading bundle"
    upload_files SAGE-Data.tar

    write_metrics metrics.prom
    echo "uploading metrics"
    upload_files metrics.prom
}

time export_data_chunks
time compile_data_bundle
time upload_data_bundle
