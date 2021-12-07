FROM python:3.8
WORKDIR /app
RUN apt-get update && apt-get install -y \
    openssh-client \
    rsync \
    && rm -rf /var/lib/apt/lists/*
COPY . .
CMD ["/app/cron_nightly_update.sh"]
