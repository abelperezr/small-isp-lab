FROM freeradius/freeradius-server:latest

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends openssh-server sudo \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash admin \
    && echo 'admin:admin' | chpasswd \
    && usermod -aG sudo admin \
    && echo 'admin ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/admin \
    && chmod 0440 /etc/sudoers.d/admin \
    && mkdir -p /run/sshd /etc/ssh/sshd_config.d

RUN printf '%s\n' \
    'PasswordAuthentication yes' \
    'KbdInteractiveAuthentication no' \
    'UsePAM no' \
    'X11Forwarding no' \
    'PermitRootLogin no' \
    > /etc/ssh/sshd_config.d/lab.conf

COPY entrypoint.sh /usr/local/bin/radius-lab-entrypoint.sh
RUN chmod 0755 /usr/local/bin/radius-lab-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/radius-lab-entrypoint.sh"]
CMD ["freeradius"]
