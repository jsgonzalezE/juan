# Toolkit de pruebas de seguridad

Herramientas para pasar del informe a **hallazgos reales** en `burmancoffee.com`.

| Archivo | Qué hace | Intrusividad |
|---------|----------|--------------|
| [`recon.sh`](recon.sh) | Batería general: DNS, DNSSEC, TLS, cabeceras, cookies, security.txt, rutas sensibles, subdominios | 🟢 No intrusivo |
| [`origin-discovery.sh`](origin-discovery.sh) | **Caza la IP de origen** detrás de Cloudflare (el vector nº1 para saltarse el WAF) | 🟢 No intrusivo |
| [`pentest-playbook.md`](pentest-playbook.md) | **Mapa de ataque priorizado**: dónde entrar, cómo probar, qué es un hallazgo | 📄 Guía |

---

## `recon.sh`

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

## `origin-discovery.sh`

Busca la **IP del servidor de origen** detrás de Cloudflare — el hueco nº1 para saltarse el WAF.
Prueba hostnames típicos sin proxear (`dev`, `ftp`, `cpanel`, `mail`…), enumera crt.sh, revisa los
MX y, por cada IP que **no** sea de Cloudflare, hace **una** petición con `Host: burmancoffee.com`
para confirmar si sirve el sitio directamente. No intrusivo.

```bash
./origin-discovery.sh burmancoffee.com | tee origin-$(date +%F).txt
```

Las líneas `[ORIGEN?]` en rojo son IPs candidatas a origen. Si alguna responde al sitio → **bypass
de WAF posible** → rota la IP + Authenticated Origin Pulls + firewall solo‑Cloudflare.

## `pentest-playbook.md`

El **mapa de por dónde entrar**, ordenado por probabilidad real de encontrar algo: IP de origen,
entorno `dev`, suplantación de correo (DMARC `p=none`, explotable hoy), toma de subdominio, secretos
en el frontend/Klaviyo, lógica de e‑commerce, y toma de cuenta del registrador. Cada vector dice
**dónde mirar → cómo probar → qué es un hallazgo**, marcando 🟢 no intrusivo vs. 🟠 activo.

## Siguiente nivel (requiere autorización explícita)

`recon.sh` y `origin-discovery.sh` son **no intrusivos**. Para las pruebas **activas** del playbook
(fuzzing de parámetros, inyección, revisión del flujo de checkout, PoC de suplantación) hace falta un
plan con alcance definido, preferiblemente contra **staging**. Ver §7 de
[`../security-assessment.md`](../security-assessment.md) y el [`pentest-playbook.md`](pentest-playbook.md).
