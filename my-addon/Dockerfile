ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install Python and system tools
RUN apk add --no-cache \
    bash \
    curl \
    jq \
    python3 \
    py3-pip \
    py3-psutil \
    lm-sensors \
    procps \
    sysstat

# Copy the web application
COPY rootfs /

# Copy the entrypoint
COPY run.sh /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
