ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install Python, MQTT client, and system monitoring tools
RUN apk add --no-cache \
    bash \
    curl \
    jq \
    python3 \
    py3-psutil \
    py3-paho-mqtt

# Copy the sensor publisher
COPY rootfs /

# Copy the entrypoint
COPY run.sh /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
