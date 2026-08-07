# Guía de remediación paso a paso — burmancoffee.com

Instrucciones concretas para cada hallazgo de [`../security-assessment.md`](../security-assessment.md).
Casi todo se resuelve en el panel de **Cloudflare** y en el registrador **Register.com**.

Orden recomendado (de mayor a menor impacto / menor esfuerzo):

1. [Investigar `dev.burmancoffee.com` (H‑01)](#1--investigar-devburmancoffeecom-h-01) — 🔴
2. [Activar HSTS (H‑02)](#2--activar-hsts-h-02) — 🟠
3. [Endurecer DMARC (H‑03)](#3--endurecer-dmarc-h-03) — 🟠
4. [Habilitar DNSSEC (H‑04)](#4--habilitar-dnssec-h-04) — 🟠
5. [Endurecer SPF (H‑05)](#5--endurecer-spf-h-05) — 🟡
6. [Rotar clave DKIM de 1024 bits (H‑06)](#6--rotar-clave-dkim-de-1024-bits-h-06) — 🟡
7. [Publicar `security.txt` (H‑07)](#7--publicar-securitytxt-h-07) — 🟡
8. [Cabeceras obsoletas (informativos)](#8--limpiar-cabeceras-obsoletas-informativo) — ⚪

---

## 1 · 🔴 Investigar `dev.burmancoffee.com` (H‑01)

**Diagnóstico primero:**
```bash
dig +short dev.burmancoffee.com A
dig +short www.dev.burmancoffee.com A
curl -sSI https://dev.burmancoffee.com
```

- Si la IP **no** es de Cloudflare (rangos `104.16.0.0/13`, `172.64.0.0/13`, etc.) → **estás filtrando la IP de origen**. Acción urgente.
- Si responde `200 OK` sin pedir login → entorno de desarrollo expuesto.

**Acciones:**
- [ ] Poner `dev` **detrás de Cloudflare Access** (Zero Trust → Access → Applications → Self‑hosted), exigiendo login por email corporativo.
- [ ] Verificar **proxy naranja activado** en el registro DNS de `dev` (Cloudflare oculta la IP de origen).
- [ ] Si la IP de origen ya se expuso: **rotarla** y activar **Authenticated Origin Pulls** o firewall que solo acepte rangos de Cloudflare (`https://www.cloudflare.com/ips/`).
- [ ] Añadir `X-Robots-Tag: noindex` y `robots.txt` con `Disallow: /`.
- [ ] Revisar que `dev` no sirva `.git/`, `.env`, backups ni paneles admin sin auth.

---

## 2 · 🟠 Activar HSTS (H‑02)

Cloudflare → **SSL/TLS → Edge Certificates → HTTP Strict Transport Security (HSTS)** → *Enable*.

**Fase inicial (segura):**
- Max Age: **6 months** (`15552000`)
- Include subdomains: **OFF** (hasta resolver H‑01)
- Preload: **OFF**
- No‑Sniff header: ON

**Fase final (tras confirmar HTTPS en todos los subdominios):**
- Max Age: **12 months** (`31536000`)
- Include subdomains: **ON**
- Preload: solo si estás 100 % seguro (difícil de revertir)

Resultado esperado:
```bash
curl -sSI https://burmancoffee.com | grep -i strict-transport-security
# Strict-Transport-Security: max-age=31536000; includeSubDomains
```

---

## 3 · 🟠 Endurecer DMARC (H‑03)

Registro TXT en `_dmarc.burmancoffee.com`. Progresión por fases (no saltes a `reject`):

| Fase | Registro TXT | Cuándo |
|------|--------------|--------|
| Actual | `v=DMARC1; p=none; rua=mailto:b27ece511fa94b44b31a87a04c60d14c@dmarc-reports.cloudflare.net` | — |
| 2 | `v=DMARC1; p=quarantine; pct=25; rua=mailto:...; fo=1` | tras 1‑2 semanas revisando informes |
| 3 | `v=DMARC1; p=quarantine; pct=100; rua=mailto:...` | si no cae correo legítimo |
| 4 | `v=DMARC1; p=reject; sp=reject; rua=mailto:...` | objetivo final |

> Revisa los informes agregados (`rua`) antes de cada salto. Confirma que Google Workspace y Klaviyo (si envía como tu dominio) pasan alineados.

---

## 4 · 🟠 Habilitar DNSSEC (H‑04)

1. Cloudflare → **DNS → Settings → Enable DNSSEC**. Copia el registro **DS** que genera.
2. Register.com → panel del dominio → sección DNSSEC → **añade el registro DS** (Key Tag, Algorithm, Digest Type, Digest).
3. Verifica (tras propagación):
   ```bash
   dig +dnssec burmancoffee.com | grep -i rrsig
   ```
   o usa https://dnssec-analyzer.verisignlabs.com/

---

## 5 · 🟡 Endurecer SPF (H‑05)

1. Inventaría emisores legítimos que envían como `@burmancoffee.com` (Google Workspace ya incluido; ¿Klaviyo? ¿facturación? ¿CRM?).
2. Añade sus `include:` y cambia `~all` por `-all` **solo cuando DMARC confirme** que nada legítimo falla:
   ```
   Actual:  v=spf1 include:_spf.google.com ~all
   Objetivo: v=spf1 include:_spf.google.com [include:otros...] -all
   ```

---

## 6 · 🟡 Rotar clave DKIM de 1024 bits (H‑06)

- Localiza el selector de la clave de 1024 bits (`dig TXT <selector>._domainkey.burmancoffee.com`).
- Google Workspace: Admin → Apps → Gmail → *Authenticate email* → generar **2048 bits** y publicar el nuevo TXT.
- Elimina el selector antiguo si ya no se usa.

---

## 7 · 🟡 Publicar `security.txt` (H‑07)

Sirve el archivo [`../.well-known/security.txt`](../.well-known/security.txt) en:
```
https://burmancoffee.com/.well-known/security.txt
```

**Opciones de despliegue según tu stack:**
- **Shopify:** no permite `.well-known/` arbitrario fácilmente → usa un **Cloudflare Worker** o **Redirect Rule** que devuelva el contenido.
- **Cloudflare Worker (funciona con cualquier origen):**
  ```js
  export default {
    fetch(req) {
      const url = new URL(req.url);
      if (url.pathname === "/.well-known/security.txt" || url.pathname === "/security.txt") {
        return new Response(
  `Contact: mailto:jburman@burmancoffee.com
  Expires: 2027-08-03T00:00:00.000Z
  Preferred-Languages: es, en
  Canonical: https://burmancoffee.com/.well-known/security.txt`,
          { headers: { "content-type": "text/plain; charset=utf-8" } }
        );
      }
      return fetch(req);
    }
  }
  ```
- **Servidor propio (Nginx/Apache):** copia el archivo a `/.well-known/security.txt` en el docroot.

Verifica:
```bash
curl -sS https://burmancoffee.com/.well-known/security.txt
```

---

## 8 · ⚪ Limpiar cabeceras obsoletas (informativo)

Vía Cloudflare **Rules → Transform Rules → Modify Response Header**:

- **Quitar** `Expect-CT` (obsoleta).
- **Cambiar** `X-XSS-Protection: 1; mode=block` → `X-XSS-Protection: 0` (recomendación moderna; confía en la CSP).
- **Verificar la CSP real** de la aplicación (la vista en el informe podría ser la de la página de challenge de Cloudflare — ver §5 del informe principal).

---

## Checklist rápido

- [ ] **H‑01** `dev.burmancoffee.com` detrás de Access / IP de origen no expuesta 🔴
- [ ] **H‑02** HSTS activado (6m → 12m + includeSubDomains) 🟠
- [ ] **H‑03** DMARC → quarantine → reject 🟠
- [ ] **H‑04** DNSSEC activado + DS en Register.com 🟠
- [ ] **H‑05** SPF `~all` → `-all` 🟡
- [ ] **H‑06** Clave DKIM 1024 → 2048 bits 🟡
- [ ] **H‑07** `security.txt` publicado 🟡
- [ ] **H‑08** OCSP stapling verificado ⚪
- [ ] Cabeceras reales de la app verificadas (no la página de challenge) ⚪
- [ ] `Expect-CT` retirada / `X-XSS-Protection: 0` ⚪
