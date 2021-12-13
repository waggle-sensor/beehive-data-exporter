#!/bin/bash -e

cd $(dirname $0)

DATA_DIR="${DATA_DIR:-data}"
DATA_START_DATE="${DATA_START_DATE:-2021-06-01}"
UPLOAD_ADDR="${UPLOAD_ADDR:-bebop.lcrc.anl.gov}"
UPLOAD_USER="${UPLOAD_USER:-svcwagglersync}"
UPLOAD_KEY="${UPLOAD_KEY:-~/.ssh/lcrc}"
UPLOAD_DIR="${UPLOAD_DIR:-/home/svcwagglersync/waggle/public_html/sagedata/}"

echo "DATA_DIR=${DATA_DIR}"
echo "UPLOAD_ADDR=${UPLOAD_ADDR}"
echo "UPLOAD_USER=${UPLOAD_USER}"
echo "UPLOAD_KEY=${UPLOAD_KEY}"
echo "UPLOAD_DIR=${UPLOAD_DIR}"

date_n_days_ago() {
    date -d "${1} days ago" +"%Y-%m-%d"
}

export_data_chunks() {
    echo "exporting data chunks"

    # clear date.done flags for last few days to ensure that delayed data is included
    for n in $(seq 1 3); do
        d=$(date_n_days_ago "${n}")
        rm "${DATA_DIR}/${d}.done" &> /dev/null || true
    done

    ./export_data_chunks.py --datadir="${DATA_DIR}" --exclude "^sys.*" "${DATA_START_DATE}" "$(date_n_days_ago 1)"
}

compile_data_bundle() {
    echo "compiling bundle"
    ./compile_bundle.py --datadir="${DATA_DIR}" --exclude 'sys.*' --project=SAGE SAGE-Data
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
