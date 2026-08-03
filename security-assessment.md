# Evaluación de seguridad — burmancoffee.com

- **Objetivo:** `burmancoffee.com` (tienda de e‑commerce, fronting de Cloudflare)
- **Fecha del análisis:** 2026-08-03
- **Solicitante:** propietario del dominio (`jburman@burmancoffee.com`)
- **Fuente de datos:** informe *Web‑Check* (`lissy93/web-check`) — 38 comprobaciones, 13 incidencias
- **Tipo de evaluación:** análisis pasivo / no intrusivo + revisión experta del informe. **No** se ejecutó explotación activa ni escaneo intrusivo contra la tienda en producción.

> ⚠️ **Alcance y método.** Este documento es una **revisión de seguridad basada en el informe Web‑Check que aportaste**, enriquecida con análisis experto de los datos crudos (cabeceras, DNS, TLS, DKIM, subdominios). El entorno donde se generó este informe **no tiene salida a Internet** (política de egress bloqueada), por lo que **no** se realizó un escaneo en vivo nuevo. Ninguna de las recomendaciones requiere confiar ciegamente en el informe: todas incluyen cómo **verificarlas tú mismo**. Ver [«Cómo verificar en vivo»](#cómo-verificar-en-vivo) y [«Pruebas activas: siguiente fase»](#pruebas-activas-siguiente-fase).

---

## 1. Resumen ejecutivo

La postura de seguridad de `burmancoffee.com` es **buena en lo fundamental**: TLS 1.3 moderno con forward secrecy, WAF de Cloudflare por delante, certificado válido, SPF y DKIM presentes, y sin coincidencias en listas de amenazas ni de bloqueo. No hay vulnerabilidades críticas conocidas.

Las incidencias detectadas son de **endurecimiento (hardening)**, no brechas explotables de forma directa. Ordenadas por riesgo real:

| Prioridad | Hallazgo | Riesgo | Esfuerzo |
|-----------|----------|--------|----------|
| 🔴 Alta | Subdominio `dev.burmancoffee.com` expuesto públicamente (posible fuga de IP de origen y entorno sin endurecer) | Bypass de WAF / exposición de entorno de desarrollo | Medio |
| 🟠 Media | Sin cabecera **HSTS** (Strict-Transport-Security) | SSL‑stripping / downgrade MITM | Bajo |
| 🟠 Media | **DMARC** en `p=none` (solo monitorización) | Suplantación de tu dominio en phishing a clientes | Bajo |
| 🟠 Media | **DNSSEC** no habilitado | Envenenamiento de caché / spoofing DNS | Bajo |
| 🟡 Baja | **SPF** con `~all` (softfail) en lugar de `-all` | Suplantación de correo más fácil | Bajo |
| 🟡 Baja | Una clave **DKIM** publicada es RSA de 1024 bits | Firma de correo débil (legado) | Bajo |
| 🟡 Baja | Sin **`security.txt`** | Sin canal claro para reportar vulnerabilidades | Muy bajo |
| 🟡 Baja | **OCSP stapling** no presente | Rendimiento/privacidad en revocación de cert. | Muy bajo |
| ⚪ Info | Cabecera `Server: cloudflare` (divulgación menor) | Fingerprinting mínimo | — |
| ⚪ Info | `x-xss-protection` y `Expect-CT` obsoletas | Cabeceras heredadas | Muy bajo |
| ⚪ Info | Puntuación SEO 40 (Lighthouse) | No es un problema de seguridad | — |

> 🧩 **Advertencia metodológica importante:** el escáner recibió una **página de desafío (challenge) de Cloudflare**, no la respuesta real de la aplicación (evidencia: cabecera `cf-mitigated: challenge` y `server-timing: chlray`). Por tanto, **varios «aprobados» de cabeceras HTTP (CSP, X‑Frame‑Options, COOP/COEP/CORP, Referrer‑Policy) probablemente reflejan la página de challenge de Cloudflare, no las cabeceras reales de tu tienda.** Conviene re‑verificar las cabeceras contra una respuesta real de la aplicación (ver §5).

---

## 2. Lo que está bien (no tocar)

Merece la pena documentar lo que ya está correcto:

- ✅ **TLS 1.3** negociado, suite `TLS_AES_256_GCM_SHA384`, clave efímera **ECDH X25519 (253‑bit)**, **forward secrecy** activo.
- ✅ **Certificado válido y confiable** (Google Trust Services, P‑256), expira 2026‑10‑20, renovado 2026‑07‑22.
- ✅ **HTTP/2** vía ALPN.
- ✅ **WAF de Cloudflare** detectado y activo (de hecho interceptó al escáner con un challenge).
- ✅ **SPF** publicado y **DKIM** presente (Google Workspace).
- ✅ **Sin coincidencias** en Google Safe Browsing, phishing, feeds de amenazas ni 12 listas de bloqueo DNS probadas.
- ✅ **Sin CVEs activos** conocidos para la superficie detectada.
- ✅ **Dominio sólido:** registrado en 2002, vigente hasta 2033, en Register.com; nameservers de Cloudflare.
- ✅ Puntuaciones Lighthouse altas: Rendimiento 97, Accesibilidad 93, Buenas prácticas 96.

---

## 3. Hallazgos priorizados y remediación

### 🔴 H‑01 · Subdominio de desarrollo expuesto: `dev.burmancoffee.com`

**Qué es.** Los registros de Certificate Transparency (crt.sh) revelan 3 subdominios: `www.burmancoffee.com`, **`dev.burmancoffee.com`** y **`www.dev.burmancoffee.com`**. Un entorno `dev` accesible públicamente es, con frecuencia, el punto más débil de una infraestructura por lo demás bien protegida.

**Por qué importa (riesgo real).**
- Los entornos de desarrollo/staging suelen tener **debug activado, credenciales por defecto, datos de prueba, versiones antiguas de software y sin WAF**.
- Si `dev.burmancoffee.com` **no está detrás de Cloudflare** (o apunta directo al servidor de origen), puede **revelar la IP de origen** de la tienda. Con la IP de origen, un atacante puede **saltarse por completo el WAF de Cloudflare** y atacar el servidor directamente.
- Puede exponer código, rutas administrativas o backups no destinados al público.

**Cómo verificarlo tú mismo.**
```bash
# ¿A qué IP resuelve? ¿Es Cloudflare (104.x / 172.67.x) o una IP de origen?
dig +short dev.burmancoffee.com A
dig +short www.dev.burmancoffee.com A

# ¿Responde? ¿Pide autenticación? ¿Filtra algo?
curl -sSI https://dev.burmancoffee.com
```

**Remediación.**
1. Si `dev` no necesita ser público: ponlo **detrás de Cloudflare Access** (Zero Trust) exigiendo login, o **restringe por IP** / VPN, o simplemente **desactívalo** cuando no se use.
2. Asegúrate de que **resuelve a IPs de Cloudflare** (proxy naranja activado), nunca directo al origen.
3. Añade `X-Robots-Tag: noindex` y `robots.txt` para que no se indexe.
4. Revisa que no exponga `.git/`, backups, `.env`, paneles de administración ni endpoints de API sin auth.
5. Si la IP de origen ya se filtró: **rota la IP de origen** y usa **Cloudflare Authenticated Origin Pulls** o reglas de firewall que solo acepten tráfico de rangos de Cloudflare.

---

### 🟠 H‑02 · Falta la cabecera HSTS (Strict-Transport-Security)

**Qué es.** El sitio **no envía** `Strict-Transport-Security`. (El informe lo marca dos veces: «Missing Strict-Transport-Security» y «No HSTS header».)

**Por qué importa.** Sin HSTS, un atacante en la red (Wi‑Fi público, MITM) puede hacer **SSL‑stripping**: forzar al navegador a hablar HTTP en claro y capturar sesiones/credenciales. HSTS ordena al navegador usar **siempre HTTPS** para tu dominio.

**Remediación (Cloudflare, 2 min).** Panel → **SSL/TLS → Edge Certificates → HTTP Strict Transport Security (HSTS) → Enable**.
- Empieza conservador: `max-age=15552000` (6 meses), **sin** `includeSubDomains` todavía.
- Cuando confirmes que **todos** los subdominios (incluido `dev`) sirven HTTPS correctamente, sube a `max-age=31536000` (1 año) + `includeSubDomains`.
- `preload` **solo** al final y con cautela: es difícil de revertir y afecta a *todos* los subdominios.

Cabecera objetivo final:
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
```
> ⚠️ **Cuidado con `includeSubDomains`:** si `dev.burmancoffee.com` u otro subdominio no soporta HTTPS al 100 %, dejará de ser accesible. Resuelve H‑01 antes de activar `includeSubDomains`.

---

### 🟠 H‑03 · DMARC en modo solo‑monitorización (`p=none`)

**Qué es.** Registro actual:
```
v=DMARC1; p=none; rua=mailto:b27ece511fa94b44b31a87a04c60d14c@dmarc-reports.cloudflare.net
```
`p=none` significa que **no se aplica ninguna acción** al correo que suplanta tu dominio; solo se recopilan informes.

**Por qué importa.** Para un negocio que envía correos a clientes (pedidos, marketing vía Klaviyo), `p=none` **no impide que alguien envíe phishing haciéndose pasar por `@burmancoffee.com`**. Es un riesgo reputacional y de fraude a tus clientes.

**Remediación (despliegue gradual, DNS).** Ya tienes `rua` (informes agregados a Cloudflare) — úsalo para verificar que tu correo legítimo (Google Workspace, Klaviyo si envía como tu dominio) pasa alineado, y luego endurece por fases:

1. **Semanas 1–2 (monitor):** revisa los informes DMARC actuales. Confirma que Google Workspace y cualquier ESP pasan SPF/DKIM alineados.
2. **Fase 2 (cuarentena parcial):**
   ```
   v=DMARC1; p=quarantine; pct=25; rua=mailto:b27ece511fa94b44b31a87a04c60d14c@dmarc-reports.cloudflare.net; fo=1
   ```
3. **Fase 3 (cuarentena total):** sube `pct=100`.
4. **Fase 4 (rechazo):**
   ```
   v=DMARC1; p=reject; sp=reject; rua=mailto:b27ece511fa94b44b31a87a04c60d14c@dmarc-reports.cloudflare.net
   ```
   `sp=reject` protege también los subdominios.

> No saltes directo a `p=reject`: podrías tirar correo legítimo. Avanza fase a fase revisando los informes `rua`.

---

### 🟠 H‑04 · DNSSEC no habilitado

**Qué es.** El dominio está `unsigned`: sin DNSKEY, DS ni RRSIG. Las respuestas DNS no están firmadas criptográficamente.

**Por qué importa.** Sin DNSSEC, un atacante que pueda envenenar cachés DNS podría **redirigir tu dominio** (correo o web) a servidores maliciosos sin romper TLS a ojos del usuario.

**Remediación (Cloudflare + registrador, ~10 min + propagación).**
1. Cloudflare → **DNS → Settings → Enable DNSSEC**. Cloudflare te dará un registro **DS** (algoritmo, digest, key tag).
2. Entra en tu registrador **Register.com** y **añade ese registro DS** en la configuración del dominio.
3. Verifica con `dig +dnssec burmancoffee.com` o [dnssec-analyzer.verisignlabs.com](https://dnssec-analyzer.verisignlabs.com/).

---

### 🟡 H‑05 · SPF con softfail (`~all`)

**Qué es.** `v=spf1 include:_spf.google.com ~all`. El `~all` (softfail) indica «probablemente no autorizado» en vez de `-all` (hardfail, «rechazar»).

**Por qué importa.** Con softfail, muchos receptores aún **aceptan** correo que falla SPF (lo marcan, no lo rechazan). Combinado con DMARC `p=none`, la protección anti‑suplantación es débil.

**Remediación.**
1. Primero, **inventaría todos tus emisores legítimos**: Google Workspace ya está. Si **Klaviyo** (detectado por `klaviyo-site-verification`) envía correo *como* `@burmancoffee.com`, añade su `include` de SPF; si envía desde su propio subdominio/dominio, no hace falta.
2. Cuando los informes DMARC confirmen que no falla nada legítimo, cambia `~all` → `-all`:
   ```
   v=spf1 include:_spf.google.com ~all      →      v=spf1 include:_spf.google.com -all
   ```
   (Añade los `include:` de otros emisores antes del `-all`.)

---

### 🟡 H‑06 · Una clave DKIM es RSA de 1024 bits

**Qué es.** Entre las claves DKIM publicadas, una es de **1024 bits** (prefijo `MIGfMA0...`); las otras dos son de 2048 bits.

**Por qué importa.** 1024 bits es el mínimo legado y se considera **débil**; NIST y los grandes proveedores recomiendan **2048 bits**.

**Remediación.** Identifica el selector de esa clave (probablemente un servicio antiguo o secundario) y **rota a 2048 bits**, o elimina el selector si ya no se usa. En Google Workspace: Admin → Apps → Google Workspace → Gmail → *Authenticate email* → generar clave DKIM de 2048 bits.

---

### 🟡 H‑07 · Sin `security.txt`

**Qué es.** No existe `https://burmancoffee.com/.well-known/security.txt` (RFC 9116).

**Por qué importa.** Es el canal estándar para que investigadores de seguridad te reporten vulnerabilidades de forma responsable en lugar de divulgarlas o venderlas.

**Remediación.** Publica el archivo incluido en este repo en `.well-known/security.txt`. Ver [`.well-known/security.txt`](.well-known/security.txt) y la guía de despliegue.

---

### 🟡 H‑08 · OCSP stapling no presente

**Qué es.** El servidor no «grapa» (staple) la respuesta OCSP de revocación del certificado.

**Por qué importa.** Bajo. Afecta al **rendimiento y la privacidad** de la comprobación de revocación del certificado, no a la seguridad directa. Con Cloudflare suele gestionarse automáticamente.

**Remediación.** Normalmente no requiere acción manual en Cloudflare. Verifica con:
```bash
openssl s_client -connect burmancoffee.com:443 -status < /dev/null 2>/dev/null | grep -i "OCSP"
```

---

### ⚪ Informativos

- **`Server: cloudflare`** — divulgación mínima (no revela versión). Inherente a Cloudflare; sin acción práctica.
- **`x-xss-protection: 1; mode=block`** — cabecera **obsoleta**; en navegadores antiguos podía introducir problemas. Recomendación moderna: `x-xss-protection: 0` y confiar en una **CSP** sólida.
- **`Expect-CT: max-age=86400, enforce`** — cabecera **obsoleta** (Certificate Transparency ya es obligatoria). Inofensiva; puede retirarse.
- **SEO 40 (Lighthouse)** — **no es un problema de seguridad**; es visibilidad en buscadores (meta tags, robots, estructura). Fuera del alcance de esta evaluación, pero anotado por transparencia.

---

## 4. Superficie e infraestructura (contexto)

| Elemento | Valor |
|----------|-------|
| CDN / WAF / DNS | Cloudflare (AS13335) |
| IPs (edge Cloudflare) | 104.26.11.8, 104.26.10.8, 172.67.73.104 |
| Puertos abiertos | 80, 443, 8080 *(puertos estándar del edge de Cloudflare, no del origen)* |
| Nameservers | kate.ns.cloudflare.com, walt.ns.cloudflare.com |
| Correo | Google Workspace (MX de Google) + Klaviyo (marketing) |
| Certificado | Google Trust Services, TLS 1.3, exp. 2026‑10‑20 |
| Subdominios (CT logs) | www, **dev**, www.dev |

> **Sobre el puerto 8080:** aparece «abierto» pero es uno de los **puertos HTTP estándar del proxy de Cloudflare**; termina en el edge de Cloudflare, no en tu servidor de origen. No es una exposición del origen por sí mismo.

---

## 5. La página de challenge de Cloudflare (verificar cabeceras reales)

El informe capturó cabeceras con `cf-mitigated: challenge` y `server-timing: chlray;...` — señales inequívocas de que Web‑Check recibió la **página «Just a moment…» de Cloudflare**, no la respuesta real de tu aplicación.

**Implicación:** los «aprobados» de cabeceras HTTP (CSP `default-src 'none'`, X‑Frame‑Options, COOP/COEP/CORP, Referrer‑Policy) **pueden pertenecer a la página de challenge**, no a tu tienda. Antes de darlos por buenos, verifica las **cabeceras reales de la aplicación** con una petición que pase el challenge (navegador real o herramienta con JS), o desde el propio Cloudflare.

```bash
# Cabeceras crudas (probablemente verás el challenge):
curl -sSI https://burmancoffee.com

# Verificación recomendada con navegador real (pasa el challenge):
#   DevTools → Network → documento principal → Response Headers
# Comprobar presencia REAL de: Content-Security-Policy, X-Frame-Options,
#   X-Content-Type-Options, Referrer-Policy, y (tras H-02) HSTS.
```

---

## 6. Cómo verificar en vivo

Como este informe se generó **sin acceso a Internet**, aquí tienes los comandos para reproducir/validar cada hallazgo desde tu máquina:

```bash
# TLS y certificado
openssl s_client -connect burmancoffee.com:443 -servername burmancoffee.com < /dev/null 2>/dev/null | openssl x509 -noout -dates -subject -issuer

# Cabeceras (incluye ver si hay challenge)
curl -sSI https://burmancoffee.com

# HSTS presente?
curl -sSI https://burmancoffee.com | grep -i strict-transport-security

# DMARC / SPF / DKIM
dig +short TXT _dmarc.burmancoffee.com
dig +short TXT burmancoffee.com | grep spf1

# DNSSEC
dig +dnssec burmancoffee.com | grep -i rrsig

# Subdominios y posible IP de origen
dig +short dev.burmancoffee.com A
curl -sSI https://dev.burmancoffee.com

# security.txt
curl -sS https://burmancoffee.com/.well-known/security.txt
```

Herramientas externas recomendadas (gratuitas): **SSL Labs** (grado TLS), **Mozilla HTTP Observatory** (cabeceras), **DMARC/dmarcian**, **Hardenize**, **crt.sh** (subdominios).

---

## 7. Pruebas activas: siguiente fase

Esta evaluación es **pasiva/no intrusiva**. Un test de penetración *activo* (fuzzing, pruebas de inyección, escaneo de vulnerabilidades autenticado, revisión de la lógica del checkout, etc.) sobre la **tienda en producción** conviene planificarlo aparte porque:

- Puede **degradar o interrumpir** la tienda en vivo y afectar a clientes reales.
- Puede **disparar el WAF de Cloudflare** y bloquear tu propia IP.
- Idealmente se ejecuta contra un **entorno de staging** equivalente, en una ventana acordada, con backups y con la lista de bypass del WAF configurada para el tester.

Si quieres avanzar a esa fase, dímelo y preparamos un **plan de pentest con alcance definido** (activos, ventana horaria, reglas de enfrentamiento, entorno). También puedo **revisar el código de la aplicación** si añades el repositorio de la tienda a esta sesión.

---

## 8. Referencias

- Informe origen: Web‑Check (`github.com/lissy93/web-check`)
- RFC 9116 — `security.txt`
- RFC 7489 — DMARC
- RFC 6797 — HSTS
- Cloudflare Docs — DNSSEC, HSTS, Authenticated Origin Pulls, Cloudflare Access
