FROM alpine

# Install Docker in Alpine
RUN apk add docker

# Copy script
COPY send_server_probe.sh /usr/local/bin/

# Change script permission
RUN chmod +x /usr/local/bin/send_server_probe.sh

# Execute Alpine script
ENTRYPOINT [ "/usr/local/bin/send_server_probe.sh" ]