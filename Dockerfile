FROM alpine:latest

# Install Packages
RUN apk update && \
    apk upgrade && \
    apk add python py-requests py-pip && \
    pip install influxdb pytimeparse

# cleanup
RUN apk del --purge && \
    rm -rf /root/.cache

# add local files
COPY . /root/

# Run script
CMD python /root/sabnzbd_influxdb_export.py
