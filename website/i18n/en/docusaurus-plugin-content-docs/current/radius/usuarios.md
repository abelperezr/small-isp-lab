---
sidebar_position: 2
---

# RADIUS User Configuration

## Configured Users

### ONT1 - WAN1 (IPv6-only)

```text
00:d0:f6:01:01:01   Cleartext-Password := "testlab123"
                    Framed-IPv6-Pool = "IPv6",
                    Alc-Delegated-IPv6-Pool = "IPv6",
                    Alc-SLA-Prof-str = "100M",
                    Alc-Subsc-Prof-str = "subprofile",
                    Alc-Subsc-ID-Str = "ONT-001",
                    Alc-MSAP-Interface= "ipv6-only"
```

### ONT1 - WAN2 (Dual-Stack)

```text
00:d0:f6:01:01:02   Cleartext-Password := "testlab123"
                    Framed-Pool = "cgnat",
                    Framed-IPv6-Pool = "IPv6-dual-stack",
                    Alc-Delegated-IPv6-Pool = "IPv6-dual-stack",
                    Alc-SLA-Prof-str = "100M",
                    Alc-Subsc-Prof-str = "subprofile",
                    Alc-Subsc-ID-Str = "ONT-001",
                    Alc-MSAP-Interface= "dual-stack"
```

### ONT1 - WAN3 (VIP)

```text
00:d0:f6:01:01:03   Cleartext-Password := "testlab123"
                    Framed-Pool = "one-to-one",
                    Alc-Subsc-ID-Str = "ONT-001",
                    Alc-Subsc-Prof-Str = "subprofile",
                    Alc-SLA-Prof-Str = "100M",
                    Alc-MSAP-Interface= "vip"
```

### ONT2 - WAN1 (PPPoE IPv6-only)

```text
"test@test.com"     Cleartext-Password := "testlab123"
                    Framed-Pool = "cgnat",
                    Framed-IPv6-Pool = "IPv6",
                    Alc-Delegated-IPv6-Pool = "IPv6",
                    Alc-SLA-Prof-str = "100M",
                    Alc-Subsc-Prof-str = "subprofile",
                    Alc-Subsc-ID-Str = "ONT-002-PPPOE",
                    Alc-MSAP-Interface= "ipv6-only"
```

## Nokia VSA attributes

| Attribute | Function |
|----------|---------|
| Alc-SLA-Prof-str | SLA Profile (QoS) |
| Alc-Subsc-Prof-str | Subscriber profile |
| Alc-Subsc-ID-Str | Subscriber ID |
| Alc-MSAP-Interface | Group Interface destination |
| Alc-Delegated-IPv6-Pool | Pool for Prefix Delegation |
| Framed Pool | DHCPv4 Pool |
| Framed-IPv6-Pool | Pool DHCPv6 WAN |
