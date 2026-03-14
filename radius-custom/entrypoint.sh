#!/bin/sh
set -eu

if [ ! -e /etc/raddb ]; then
    ln -s /etc/freeradius /etc/raddb
fi

mkdir -p /var/log/freeradius /var/log/freeradius/radacct /run/sshd
chown -R freerad:freerad /var/log/freeradius

if [ ! -e /var/log/radius ]; then
    ln -s /var/log/freeradius /var/log/radius
fi

if [ -f /tmp/authorized_keys ]; then
    mkdir -p /home/admin/.ssh
    cp /tmp/authorized_keys /home/admin/.ssh/authorized_keys
    chown -R admin:admin /home/admin/.ssh
    chmod 700 /home/admin/.ssh
    chmod 600 /home/admin/.ssh/authorized_keys
fi

if [ ! -f /etc/ssh/ssh_host_rsa_key ]; then
    ssh-keygen -A
fi

/usr/sbin/sshd

exec /docker-entrypoint.sh "$@"
