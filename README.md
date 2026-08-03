# Evaluación de seguridad — burmancoffee.com

Revisión de seguridad **pasiva / no intrusiva** de `burmancoffee.com`, realizada a partir del
informe *Web‑Check* aportado por el propietario del dominio (`jburman@burmancoffee.com`) y
enriquecida con análisis experto de los datos crudos (cabeceras HTTP, DNS, TLS, DKIM, subdominios).

## Contenido

| Archivo | Descripción |
|---------|-------------|
| [`security-assessment.md`](security-assessment.md) | **Informe principal**: resumen ejecutivo, hallazgos priorizados, remediación y contexto de infraestructura. |
| [`remediation/remediation-guide.md`](remediation/remediation-guide.md) | Guía paso a paso con configuraciones exactas (Cloudflare / Register.com / DNS). |
| [`.well-known/security.txt`](.well-known/security.txt) | Archivo `security.txt` listo para desplegar (RFC 9116). |

## TL;DR

La postura base es **buena** (TLS 1.3, WAF de Cloudflare, SPF/DKIM, sin CVEs ni listas de bloqueo).
Las 13 incidencias son de **endurecimiento**, no brechas explotables directas. Prioridades:

1. 🔴 **`dev.burmancoffee.com` expuesto** — investigar posible fuga de IP de origen / entorno sin endurecer.
2. 🟠 **HSTS** ausente — activar en Cloudflare.
3. 🟠 **DMARC** en `p=none` — endurecer a `quarantine` → `reject`.
4. 🟠 **DNSSEC** desactivado — habilitar.
5. 🟡 SPF `~all`, clave DKIM de 1024 bits, sin `security.txt`, OCSP stapling.

> 🧩 **Nota clave:** el escaneo original recibió una **página de challenge de Cloudflare**
> (`cf-mitigated: challenge`), por lo que varios «aprobados» de cabeceras HTTP podrían no reflejar
> la aplicación real. Verificar cabeceras contra una respuesta real (ver §5 del informe).

## Alcance y limitaciones

- Evaluación **no intrusiva**: sin explotación activa ni escaneo intrusivo contra la tienda en producción.
- El entorno de generación **no tenía salida a Internet**, por lo que **no** se hizo un escaneo en vivo nuevo;
  cada hallazgo incluye comandos para que lo **verifiques tú mismo** (ver §6 del informe).
- Para un **pentest activo** (fuzzing, inyección, revisión del checkout) o una **revisión de código**
  de la aplicación, ver §7 del informe principal.
