---
sidebar_position: 10
---

# DNS64 - BIND9

## General Information

| Parameter | Value |
|-----------|-------|
| **Hostname** | dns |
| **Image** | ghcr.io/srl-labs/network-multitool + BIND9 |
| **Management IP** | 10.99.1.13 |
| **SSH port** | 56621 |

## Function in Topology

The DNS64 server runs BIND9 with the `dns64` directive which synthesizes AAAA records for domains that only have A records. This allows IPv6-only clients (connected to Group Interface `ipv6-only`) to access IPv4 services over NAT64.

The flow is: IPv6 Client → DNS64 (synthesizes AAAA with prefix 64:ff9b::/96) → Client sends traffic to 64:ff9b::x.x.x.x → BNG NAT64 translates to IPv4.

---

## 1. INTERFACES

```text
# eth1: hacia BNG MASTER (VPRN 9998)
ip -6 addr add 2001:db8:aaaa::2/126 dev eth1
ip -6 route replace default via 2001:db8:aaaa::1 dev eth1

# eth2: hacia BNG SLAVE (VPRN 9998)
ip -6 addr add 2001:db8:aaab::2/126 dev eth2
ip -6 route replace default via 2001:db8:aaab::1 dev eth2
```

---

## 2. BIND CONFIGURATION (named.conf)

```text
////////////////////////////////////////////////////////////////////////////////
// DNS64 Server Configuration for NAT64 Lab
// NAT64 Prefix: 64:ff9b::/96 (Well-Known Prefix RFC 6052)
////////////////////////////////////////////////////////////////////////////////

options {
    directory "/var/cache/bind";

    listen-on-v6 { any; };
    listen-on { any; };

    allow-query { any; };
    allow-recursion { any; };

    forward only;
    forwarders {
        8.8.8.8;
        8.8.4.4;
    };

    // DNS64 Configuration
    dns64 64:ff9b::/96 {
        clients { any; };
        mapped { any; };
        exclude { any; };
        recursive-only yes;
        break-dnssec yes;
        suffix ::;
    };

    dnssec-validation no;
    querylog yes;
    version "DNS64 Server";
};

// Logging - SIN categoría 'dns64' (no existe en BIND 9)
logging {
    channel stderr_log {
        stderr;
        severity info;
        print-time yes;
    };
    category default { stderr_log; };
    category queries { stderr_log; };
};



zone "localhost" {
    type master;
    file "/etc/bind/db.local";
};

zone "127.in-addr.arpa" {
    type master;
    file "/etc/bind/db.127";
};

zone "0.in-addr.arpa" {
    type master;
    file "/etc/bind/db.0";
};

zone "255.in-addr.arpa" {
    type master;
    file "/etc/bind/db.255";
};

```

---

## 3. INSTALLATION IN CONTAINER

```text
apk add --no-cache bind bind-tools
mkdir -p /var/cache/bind /var/log/bind
chown -R named:named /var/cache/bind /var/log/bind
named-checkconf /etc/bind/named.conf
named -c /etc/bind/named.conf -u named
```
