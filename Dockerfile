FROM python:3.8-alpine
RUN apk add --no-cache openssh-client rsync bash
WORKDIR /app
COPY . .
