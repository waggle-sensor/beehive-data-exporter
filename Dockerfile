FROM python:3.11
WORKDIR /app
RUN apt-get update && apt-get install -y \
    openssh-client \
    rsync \
    && rm -rf /var/lib/apt/lists/*
COPY . .
CMD ["/app/cron_nightly.py"]
