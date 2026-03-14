---
sidebar_position: 2.2
sidebar_label: 3. Validación base de OLT
---

# 3. Validación Base de OLT

## Objetivo

Validar que la OLT SR Linux tenga correctamente operativas las subinterfaces bridged, sus asociaciones a MAC-VRF y el aprendizaje MAC esperado.

## Alcance

- Estado de interfaces/subinterfaces.
- Asociación de subinterfaces a `bd-50`, `bd-51`, `bd-52` y `bd-srrp`.
- Estado de tablas MAC por instancia.

## 3.1 Verificación de interfaces

Comandos:

- `show interface all`
- `show network-instance bd-50 interfaces`

Ejemplo:

```text
A:admin@olt# show interface all
ethernet-1/1.50 is up  -> bd-50
ethernet-1/1.51 is up  -> bd-51
ethernet-1/1.52 is up  -> bd-52
ethernet-1/1.4094 is up -> bd-srrp
...
ethernet-1/6.150 is up -> bd-50
```

Resultado esperado:

- Enlaces hacia BNG (`ethernet-1/1`, `ethernet-1/2`) en `up`.
- Subinterfaces de acceso (`ethernet-1/3.150`, `ethernet-1/4.200`, `ethernet-1/5.300`, `ethernet-1/6.150`) en `up`.
- Asociación correcta de subinterfaces a sus MAC-VRF.

## 3.2 Verificación de MAC-VRF y tabla MAC

Comandos:

- `macsum bd-50`
- `macsum bd-srrp`
- `show network-instance bd-50 summary`

Nota operativa:

- Si la prueba se realiza mucho tiempo después del despliegue, pueden haber expirado entradas por aging.
- En ese caso, genera tráfico (por ejemplo, `ping` desde ONTs a BNGs) y vuelve a consultar `macsum`.

Ejemplo:

```text
A:admin@olt# macsum bd-50
Total Learnt Macs : 2 Total 2 Active

A:admin@olt# macsum bd-srrp
Total Learnt Macs : 3 Total 3 Active
```

Resultado esperado:

- Aprendizaje MAC activo en `bd-50`, `bd-51`, `bd-52` y `bd-srrp` según tráfico del lab.
- Instancias MAC-VRF en estado `up`.

## 3.3 Checklist final

- Interfaces y subinterfaces críticas en `up`.
- Asociaciones a MAC-VRF correctas.
- Aprendizaje MAC coherente con servicios activos y estado del laboratorio.
