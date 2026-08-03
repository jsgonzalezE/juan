# Toolkit de pruebas — `recon.sh`

Batería de comprobaciones de seguridad **no intrusivas** (solo lectura) para `burmancoffee.com`.
Equivale a lo que hace un navegador o una consulta DNS: **seguro de ejecutar contra producción**.
No hay fuzzing, inyección, fuerza bruta ni escaneo agresivo.

## Por qué existe

La evaluación de este repo se generó en un entorno **sin salida a Internet**, así que no se pudo
hacer un escaneo en vivo. Este script te permite obtener **resultados reales** ejecutándolo desde
cualquier máquina con conexión — o desde una sesión de Claude Code con red habilitada.

## Uso

```bash
# Instala dependencias recomendadas (Debian/Ubuntu):
sudo apt-get install -y dnsutils curl openssl python3

# Ejecuta contra el objetivo por defecto (burmancoffee.com):
./recon.sh

# Guarda la salida con fecha:
./recon.sh burmancoffee.com | tee recon-$(date +%F).txt
```

Luego **pégame la salida** y la interpreto, o la contrasto con los hallazgos del informe.

## Qué comprueba

| # | Bloque | Detecta |
|---|--------|---------|
| 1 | Registros DNS | A/AAAA/MX/NS/SOA/CAA; ausencia de CAA |
| 2 | DNSSEC | DNSKEY/DS/RRSIG presentes o no |
| 3 | Correo | SPF (`-all` vs `~all`), DMARC (`none`/`quarantine`/`reject`), selectores DKIM |
| 4 | TLS/SSL | Protocolos obsoletos (SSLv3/TLS1.0/1.1), certificado, OCSP stapling |
| 5 | Cabeceras HTTP | HSTS, CSP, X-CTO, X-Frame, Referrer/Permissions-Policy; **detecta la página de challenge de Cloudflare** |
| 6 | Redirección | HTTP → HTTPS |
| 7 | Cookies | flags `Secure` / `HttpOnly` / `SameSite` |
| 8 | security.txt | presencia (RFC 9116) |
| 9 | Rutas sensibles | `.git/HEAD`, `.env`, `server-status`, `.DS_Store`, backups (solo código HTTP) |
| 10 | Subdominios + **IP de origen** | enumera vía crt.sh y marca subdominios que **resuelven fuera de Cloudflare** (bypass del WAF) |

> El bloque 10 es el más valioso: detecta automáticamente el riesgo 🔴 **H‑01**
> (posible exposición de la IP de origen vía `dev.burmancoffee.com`).

## Nota de la página de challenge

Cloudflare suele devolver una página *"Just a moment…"* a los clientes automáticos. El script lo
detecta (`cf-mitigated: challenge`) y te avisa: en ese caso, las cabeceras que veas pueden ser de
la página de challenge y **no** de tu aplicación real. Verifica también con un navegador real
(DevTools → Network → Response Headers).

## Siguiente nivel (requiere autorización explícita)

Este toolkit es **pasivo**. Para pruebas **activas** (fuzzing de parámetros, inyección, revisión del
flujo de checkout, escaneo autenticado) hace falta un plan con alcance definido, preferiblemente
contra un entorno de *staging*. Ver §7 de [`../security-assessment.md`](../security-assessment.md).
