# 🛡️ Guía de pruebas de seguridad — burmancoffee.com

**Para quién es esto:** para ti, que no eres técnico, tienes Windows con Chrome y PowerShell, y quieres comprobar la seguridad de tu propia tienda (prueba autorizada por el dueño del dominio).

**Cómo funciona:**
- Los bloques azules de **PowerShell** se copian y se pegan enteros (tecla Windows → escribe `PowerShell` → Enter → pega → Enter).
- Los **enlaces** se abren en Chrome; ya vienen rellenados con `burmancoffee.com`.
- Casi todo es **no intrusivo** (equivale a navegar o consultar DNS). Lo que puede tocar el sitio o disparar el firewall (WAF) de Cloudflare está en la sección **⚠️ Solo con permiso / en staging**.
- **Haz capturas de pantalla** de cada resultado: son tu informe para el jefe.

> **Regla de oro:** cuando veas un `403`, un `503` o una página que dice *"Just a moment…"*, normalmente es **Cloudflare bloqueando**, no una prueba de que algo esté protegido por detrás. No lo cuentes como "seguro" sin más.

---

## ⭐ EMPIEZA AQUÍ — Top pruebas (fácil + alto valor)

Estas 8, en orden. Con esto tienes el 80 % del valor en ~30 minutos.

### 1. Nota global de cabeceras de seguridad (securityheaders.com)
**Qué hace:** te da una nota de A+ a F y una lista en rojo de las protecciones que faltan. Captura perfecta para el jefe.

Abre en Chrome:
```
https://securityheaders.com/?q=https%3A%2F%2Fburmancoffee.com&followRedirects=on&hide=on
```
**Qué buscar:** la nota grande arriba a la izquierda y el bloque **"Missing Headers"** en rojo. Apunta cuáles faltan: `Strict-Transport-Security` (HSTS), `Content-Security-Policy`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`.
**Hallazgo probable:** SÍ. Es muy probable que falten HSTS y CSP (ya se sospechaba). ⚠️ Si la nota es rara o dice "Just a moment", analizó la página de reto de Cloudflare; confírmalo con la prueba 7.

---

### 2. ¿Alguien puede falsificar tu correo? (prueba de fuego — a tu propio buzón)
**Qué hace:** comprueba en la práctica si un atacante puede enviar un correo que parezca `@burmancoffee.com` y que **llegue**. Con DMARC en `p=none` y SPF `~all`, es lo esperable.
**⚠️ Prueba ACTIVA — envía SOLO a tu propio buzón `jburman@burmancoffee.com`. Nunca a clientes ni terceros.**

1. Abre en Chrome: `https://caniphish.com/free-tools/email-spoofing-test`
2. En *Recipient email*: `jburman@burmancoffee.com`
3. Dominio a falsificar: `burmancoffee.com` (p. ej. `ventas@burmancoffee.com`)
4. Envía y revisa **Bandeja de entrada Y carpeta de Spam** a los 2-5 minutos.
5. Si llega, ábrelo en Gmail → menú (tres puntos) → **"Mostrar original"** y mira las líneas `spf=`, `dkim=`, `dmarc=`.

**Qué buscar:** **HALLAZGO grave** si el correo falsificado llega a la bandeja (o incluso a Spam siendo aceptado con `dmarc=fail`). El arreglo real: subir DMARC a `p=reject` y SPF a `-all`.

---

### 3. ¿Están tus correos en filtraciones? (Have I Been Pwned)
**Qué hace:** lista qué direcciones `@burmancoffee.com` aparecen en brechas públicas. Como eres el dueño, puedes ver **todas** las del dominio.

- Búsqueda por dominio (recomendada): `https://haveibeenpwned.com/DomainSearch` → inicia sesión, añade `burmancoffee.com` y verifica con el DNS o el correo que te ofrece.
- Rápida por dirección suelta: `https://haveibeenpwned.com/` → prueba `jburman@`, `info@`, `ventas@`, `admin@`.

**Qué buscar:** cada cuenta listada = contraseña posiblemente expuesta. **Acción inmediata:** forzar cambio de contraseña + activar 2FA en esas cuentas.
**Hallazgo probable:** SÍ, casi seguro alguna dirección aparece.

---

### 4. Credenciales robadas por malware (Hudson Rock)
**Qué hace:** dice si algún equipo de un empleado/cliente fue infectado por un *infostealer* y sus contraseñas de la tienda se vendieron (a menudo en claro). Es la causa nº1 de accesos no autorizados hoy.

Pega en PowerShell:
```powershell
$dom = "burmancoffee.com"
$r = Invoke-RestMethod -Uri "https://cavalier.hudsonrock.com/api/json/v2/osint-tools/search-by-domain?domain=$dom" -TimeoutSec 60
$r | ConvertTo-Json -Depth 8
```
O por web: `https://www.hudsonrock.com/free-tools` → *Search by Domain*.
**Qué buscar:** campos `employees` / `users` mayores que 0 = equipos comprometidos. Acción: limpiar el equipo y cambiar contraseñas de esa persona.

---

### 5. Subdominios ocultos y fuga del servidor de origen (crt.sh)
**Qué hace:** lista TODOS los subdominios que alguna vez pidieron un certificado y marca cualquiera que apunte a una IP **que no sea de Cloudflare** (posible servidor real, saltándose el WAF).

Rápido en Chrome: `https://crt.sh/?q=%25.burmancoffee.com`

Completo en PowerShell (descarga la lista, resuelve y marca posibles orígenes):
```powershell
$dominio = "burmancoffee.com"
$cf = @('173.245.48.0/20','103.21.244.0/22','103.22.200.0/22','103.31.4.0/22',
 '141.101.64.0/18','108.162.192.0/18','190.93.240.0/20','188.114.96.0/20',
 '197.234.240.0/22','198.41.128.0/17','162.158.0.0/15','104.16.0.0/13',
 '104.24.0.0/14','172.64.0.0/13','131.0.72.0/22')
function InCidr($ip,$cidr){ $p=$cidr.Split('/'); try{$b=[Net.IPAddress]::Parse($p[0]).GetAddressBytes();$t=[Net.IPAddress]::Parse($ip).GetAddressBytes()}catch{return $false}; if($b.Length -ne 4 -or $t.Length -ne 4){return $false}; [array]::Reverse($b);[array]::Reverse($t); $bi=[BitConverter]::ToUInt32($b,0);$ti=[BitConverter]::ToUInt32($t,0); $s=32-[int]$p[1]; if($s -eq 32){return $true}; $m=([int64]0xffffffff -shl $s) -band 0xffffffff; return (($bi -band $m) -eq ($ti -band $m)) }
function EsCloudflare($ip){ foreach($c in $cf){ if(InCidr $ip $c){return $true} }; return $false }
try{ $crt=Invoke-RestMethod -Uri "https://crt.sh/?q=%25.$dominio&output=json" -UserAgent "Mozilla/5.0" -TimeoutSec 60 }catch{ "crt.sh no respondio; reintenta o usa el enlace de arriba." }
if($crt){
  $nombres = $crt.name_value -split "`n" | ForEach-Object { $_.Trim().TrimStart('*').Trim('.') } | Where-Object { $_ -and ($_ -like "*$dominio") } | Sort-Object -Unique
  "== $($nombres.Count) subdominios unicos =="; $nombres
  "`n== Resolviendo (marca POSIBLE ORIGEN si la IP no es de Cloudflare) =="
  foreach($n in $nombres){
    try{ $a = Resolve-DnsName -Name $n -Type A -ErrorAction Stop | Where-Object { $_.Type -eq 'A' }
      if(-not $a){ "{0,-45} (sin A)" -f $n; continue }
      foreach($ip in $a.IPAddress){ if(EsCloudflare $ip){ "{0,-45} {1}  [Cloudflare]" -f $n,$ip } else { "{0,-45} {1}  <<<<< POSIBLE ORIGEN" -f $n,$ip } }
    }catch{ "{0,-45} (no resuelve)" -f $n }
  }
}
```
**Qué buscar:** cualquier línea `<<<<< POSIBLE ORIGEN` o subdominios que no conocías (paneles, entornos internos).
**Hallazgo probable:** BAJO. Ya se comprobó que el origen está bien oculto; aquí buscas nombres **nuevos** que se hayan escapado. Que todo salga `[Cloudflare]` es lo esperable y bueno.

---

### 6. Búsqueda en Google/Bing de lo que ya está indexado (dorking)
**Qué hace:** enseña archivos y paneles del sitio que Google/Bing **ya sirven a cualquiera**: PDFs internos, copias `.sql`/`.bak`, `/wp-admin`, listados de carpetas.

Abre en Chrome (una pestaña por enlace):
```
https://www.google.com/search?q=site%3Aburmancoffee.com+filetype%3Apdf+OR+filetype%3Axls+OR+filetype%3Acsv+OR+filetype%3Asql+OR+filetype%3Alog+OR+filetype%3Abak+OR+filetype%3Aenv
https://www.google.com/search?q=site%3Aburmancoffee.com+inurl%3Aadmin+OR+inurl%3Alogin+OR+inurl%3Awp-admin
https://www.google.com/search?q=site%3Aburmancoffee.com+intitle%3A%22index+of%22
https://www.bing.com/search?q=site%3Aburmancoffee.com+filetype%3Apdf+OR+filetype%3Alog+OR+filetype%3Asql
```
**Qué buscar:** cualquier `.sql`/`.bak`/`.env`/`.log` o panel de administración. Sin resultados = buena señal.

---

### 7. HSTS y redirección http → https
**Qué hace:** comprueba si el sitio obliga a usar HTTPS. Sin HSTS, un atacante en la misma wifi puede interceptar la primera visita (SSL-strip).

Pega en PowerShell:
```powershell
$ua="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
"----- HSTS (debe existir) -----"
curl.exe -s -D - -o NUL -A $ua https://burmancoffee.com/ | Select-String -Pattern "strict-transport-security"
"----- Redireccion http->https (debe ser 301/308 a https://) -----"
curl.exe -s -D - -o NUL "http://burmancoffee.com/" | Select-String -Pattern "HTTP/|location:"
```
Preload: `https://hstspreload.org/?domain=burmancoffee.com`
**Qué buscar:** si la línea de HSTS **no imprime nada** = HALLAZGO (no hay HSTS). La redirección debe ser `301`/`308` hacia `https://` del mismo dominio.
**Hallazgo probable:** SÍ (HSTS ausente).

---

### 8. Ficheros peligrosos olvidados (.git, .env, copias de seguridad)
**Qué hace:** busca ficheros que jamás deberían ser públicos. Baja probabilidad, pero si aparece uno es **crítico** (credenciales, base de datos entera).

Pega en PowerShell (solo consulta el código de estado, no descarga nada):
```powershell
$ua="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0 Safari/537.36"
$base="https://burmancoffee.com"
$rutas=@("/.git/config","/.git/HEAD","/.env","/.env.production","/wp-config.php.bak","/backup.zip","/backup.sql","/database.sql","/dump.sql","/.DS_Store","/wp-content/debug.log","/phpinfo.php")
"RUTA                          -> CODIGO"
foreach($p in $rutas){ $u=$base+$p
  try{ $r=Invoke-WebRequest -Uri $u -Method Head -UseBasicParsing -TimeoutSec 15 -UserAgent $ua -ErrorAction Stop; $code=[int]$r.StatusCode }
  catch{ if($_.Exception.Response){$code=[int]$_.Exception.Response.StatusCode}else{$code="ERR"} }
  "{0,-30} -> {1}" -f $p,$code; Start-Sleep -Milliseconds 500 }
```
**Qué buscar:** cualquier `200`. **Verifica SIEMPRE abriéndolo en Chrome:** un `.env` real muestra `CLAVE=valor`; un `.git/config` real empieza por `[core]`. Si aparece la tienda normal, es un falso positivo (soft-404).
**Hallazgo probable:** BAJO (Cloudflare y el hosting suelen bloquear), pero impacto máximo si sale. Si encuentras un `.env`: trátalo como incidente y **rota todas las claves** (Klaviyo, pasarela de pago, base de datos).

---

## Catálogo completo por categoría

Todas las pruebas, deduplicadas. Prioriza las marcadas 🎯 (hallazgo probable).

### A) Correo (spoofing, DMARC, SPF, DKIM, transporte)

| Prueba | Sev. | Intrus. | ¿Hallazgo esperado? |
|---|---|---|---|
| Spoofing al propio buzón | Alta | activa (a tu buzón) | 🎯 probable (ver Top #2 / sección permiso) |
| Auditoría DMARC (sp, pct, rua) | Media | no intrusiva | 🎯 probable |
| MTA-STS ausente | Media | no intrusiva | 🎯 muy probable |
| Auditoría SPF (lookups, `~all` vs `-all`) | Media | no intrusiva | 🎯 confirma `~all` débil |
| DKIM: selectores y tamaño de clave | Media | no intrusiva | 🎯 confirma la RSA 1024 |
| TLS-RPT ausente | Baja | no intrusiva | 🎯 muy probable |
| BIMI ausente | Informativa | no intrusiva | esperado (no es brecha) |
| Typosquatting (dominios parecidos) | Alta | no intrusiva | variable |

**Auditoría DMARC + MTA-STS + TLS-RPT + BIMI (todo de una vez):**
```powershell
"--- DMARC (mira sp=, pct=, rua=) ---"
(Resolve-DnsName -Name _dmarc.burmancoffee.com -Type TXT).Strings -join ''
"--- MTA-STS (debe existir para cifrado obligatorio) ---"
try { (Resolve-DnsName -Name _mta-sts.burmancoffee.com -Type TXT -ErrorAction Stop).Strings -join '' } catch { 'NO existe MTA-STS' }
try { (Invoke-WebRequest -Uri 'https://mta-sts.burmancoffee.com/.well-known/mta-sts.txt' -UseBasicParsing -TimeoutSec 15).Content } catch { 'NO existe la politica mta-sts.txt' }
"--- TLS-RPT ---"
try { (Resolve-DnsName -Name _smtp._tls.burmancoffee.com -Type TXT -ErrorAction Stop).Strings -join '' } catch { 'NO existe TLS-RPT' }
"--- BIMI (informativo) ---"
try { (Resolve-DnsName -Name default._bimi.burmancoffee.com -Type TXT -ErrorAction Stop).Strings -join '' } catch { 'NO existe BIMI (normal mientras DMARC=p=none)' }
```
**Positivo:** falta `sp=` (subdominios sin proteger), falta `rua=` (el "monitor" de p=none no sirve), `pct<100`, o MTA-STS/TLS-RPT ausentes. Lectura amable: `https://mxtoolbox.com/SuperTool.aspx?action=dmarc%3aburmancoffee.com&run=toolpage` y `https://www.hardenize.com/report/burmancoffee.com`.

**Auditoría SPF:** abre `https://mxtoolbox.com/SuperTool.aspx?action=spf%3aburmancoffee.com&run=toolpage` y mira si marca `PermError` / *Too many DNS lookups* (>10) o **más de un** registro `v=spf1`. Confirma que termina en `~all` (débil) → debería ser `-all`.

**DKIM (verifica la clave de 1024 bits y su selector):**
```powershell
$dominio='burmancoffee.com'
$selectores='google','default','selector1','selector2','k1','k2','s1','s2','dkim','mail','klaviyo','kl','smtp','1','2'
foreach ($s in $selectores) {
  $n="$s._domainkey.$dominio"
  try {
    $r=Resolve-DnsName -Name $n -Type TXT -ErrorAction Stop
    $txt=(($r | Where-Object {$_.Strings}) | ForEach-Object { $_.Strings }) -join ''
    if ($txt -match 'DKIM1|p=') {
      $p=''; if ($txt -match 'p=([A-Za-z0-9+/=]+)') { $p=$Matches[1] }
      $bits= if ($p.Length -lt 260) { '~1024 bits (DEBIL)' } elseif ($p.Length -lt 500) { '~2048 bits (OK)' } else { '4096+' }
      Write-Host "selector '$s' -> long p=$($p.Length) -> $bits" -ForegroundColor Green
    }
  } catch {}
}
```
**Positivo:** el selector con `p=` de ~216 caracteres es la clave débil ya detectada. **Anota su nombre** para rotarla a 2048 bits.

**Typosquatting:** `https://dnstwist.it/?domain=burmancoffee.com` (fíjate en filas con IP real y, sobre todo, con **MX** apuntando a un tercero = capacidad de enviar correo suplantando tu marca).
```powershell
$variantes='burmancofee.com','burmancoffe.com','burman-coffee.com','burmancoffees.com','burmancoffee.net','burmancoffee.co','burmancoffee.shop','burmancoffee.store','burmancoffee.us'
foreach ($d in $variantes) {
  $a=Resolve-DnsName -Name $d -Type A -ErrorAction SilentlyContinue
  $mx=Resolve-DnsName -Name $d -Type MX -ErrorAction SilentlyContinue
  if ($a -or $mx) { Write-Host "$d -> REGISTRADO/ACTIVO  A:$([bool]$a) MX:$([bool]$mx)" -ForegroundColor Yellow } else { "$d -> sin resolucion" }
}
```

---

### B) DNS y dominio

| Prueba | Sev. | Intrus. | ¿Hallazgo esperado? |
|---|---|---|---|
| Auditoría de registros TXT (tokens olvidados) | Media | no intrusiva | posible |
| CAA ausente/permisivo | Baja | no intrusiva | 🎯 probable falta |
| Toma de subdominio (CNAME colgante) | Alta | no intrusiva | baja prob., alto impacto |
| Confirmar DNSSEC unsigned | Media | no intrusiva | ✅ ya confirmado |
| Candado del registrador + 2FA | Media | no intrusiva | revisar |
| Transferencia de zona (AXFR) | Informativa | no intrusiva | casi seguro limpio |

**TXT + CAA + DNSSEC + estado del dominio (todo junto):**
```powershell
"--- TXT (busca tokens de servicios que ya no uses) ---"
Resolve-DnsName burmancoffee.com -Type TXT | ForEach-Object { ($_.Strings -join '') }
"--- CAA (si vacio: cualquier CA puede emitir certificados) ---"
try { Resolve-DnsName burmancoffee.com -Type CAA -ErrorAction Stop } catch { 'Sin CAA / no soportado; verifica en el navegador' }
"--- DNSSEC (DS y DNSKEY vacios = unsigned, ya confirmado) ---"
Resolve-DnsName burmancoffee.com -Type DS -ErrorAction SilentlyContinue
Resolve-DnsName burmancoffee.com -Type DNSKEY -ErrorAction SilentlyContinue
"--- Estado/candado del dominio ---"
(Invoke-RestMethod "https://rdap.verisign.com/com/v1/domain/BURMANCOFFEE.COM").status
```
**Positivo:** tokens `...-site-verification` de servicios abandonados (integraciones zombie); **sin CAA** (recomendable limitar a Google Trust Services + Cloudflare); DS/DNSKEY vacíos confirma DNSSEC sin activar (arreglo: 1 clic en Cloudflare); el estado del dominio **debe** incluir `client transfer prohibited` (y a ser posible update/delete). Comprueba a mano que hay **2FA** en la cuenta del registrador y de Cloudflare (hallazgo organizativo alto si falta).

**Toma de subdominio (dangling CNAME):** enumera con `https://crt.sh/?q=%25.burmancoffee.com` y revisa CNAMEs que apunten a S3/GitHub/Heroku/Netlify/Shopify. Si al abrir el subdominio ves `NoSuchBucket`, `There isn't a GitHub Pages site here`, `No such app`, etc. → un atacante podría reclamarlo (**reclamarlo tú para probar es ACTIVO; solo documéntalo**).

**AXFR (comprobación de sanidad):** en PowerShell, línea a línea: `nslookup` → `server kate.ns.cloudflare.com` → `ls -d burmancoffee.com` → `exit`. Lo correcto es *"Query refused"*. Solo sería grave si listara registros reales.

---

### C) TLS y cabeceras HTTP

| Prueba | Sev. | Intrus. | ¿Hallazgo esperado? |
|---|---|---|---|
| securityheaders.com (nota global) | Media | no intrusiva | 🎯 ver Top #1 |
| HSTS + redirección http→https | Media/Baja | no intrusiva | 🎯 ver Top #7 |
| CSP real de la app | Media | no intrusiva | 🎯 probable ausente |
| Flags de cookies (Secure/HttpOnly/SameSite) | Media | no intrusiva | revisar |
| SSL Labs (protocolos/cifrados) | Media | no intrusiva | probable limpio (TLS 1.3 OK) |
| Cabeceras obsoletas / fuga de versión | Baja | no intrusiva | posible |
| Contenido mixto | Baja | navegador | probable limpio |

**Volcado de cabeceras + cookies + métodos obsoletos (una sola vez):**
```powershell
$ua="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0 Safari/537.36"
"===== TODAS LAS CABECERAS ====="
curl.exe -s -D - -o NUL -A $ua https://burmancoffee.com/
"===== CSP / HSTS / cabeceras clave ====="
$h=(Invoke-WebRequest 'https://burmancoffee.com/' -UseBasicParsing -UserAgent $ua).Headers
'Strict-Transport-Security','Content-Security-Policy','X-Frame-Options','X-Content-Type-Options','Referrer-Policy','Permissions-Policy' | ForEach-Object { if($h[$_]){ "OK    $_ = $($h[$_])" } else { "FALTA $_" } }
```
**Positivo:** cada `FALTA` es un hallazgo. **CSP ausente** en una tienda con checkout = sin contención si aparece un XSS. `x-powered-by:` o un `server:` con versión (p. ej. `nginx/1.18.0`, `PHP/7.x`) = fuga de información (`server: cloudflare` a secas es normal). Si solo obtienes la página de reto (`403` / "Just a moment"), mira la CSP real en Chrome: **F12 → Network → recarga → clic en el documento → Response Headers**.

**Cookies:** en la salida `Set-Cookie`, prioriza las de la app (`PHPSESSID`, carrito, login). Si a esas les falta `HttpOnly`, `Secure` o `SameSite`, es hallazgo (secuestro de sesión). Las `__cf_*` / `cf_clearance` son de Cloudflare y están bien.

**SSL Labs:** `https://www.ssllabs.com/ssltest/analyze.html?d=burmancoffee.com&hideResults=on` → busca que solo estén `Yes` TLS 1.2 y 1.3, sin suites WEAK. (Probable A/A+, ya que el cert es válido.)

**Contenido mixto:** en Chrome abre la home, F12 → Console → recarga; busca *"Mixed Content"*. Repite en producto y **checkout**.

---

### D) Subdominios y servidor de origen

> **Contexto honesto:** el origen ya está **bien oculto** (dev/staging/cpanel/webmail/ftp van por Cloudflare). Estas pruebas buscan la fuga que se haya escapado. Lo más probable es que salgan **limpias**; si alguna marca una IP no-Cloudflare, es un hallazgo importante.

| Prueba | Sev. | Intrus. | ¿Hallazgo esperado? |
|---|---|---|---|
| crt.sh + fuga de origen | Media | no intrusiva | ver Top #5 |
| DNS pasivo (OTX + HackerTarget) | Media | no intrusiva | baja prob. |
| Histórico de IP (ViewDNS, SecurityTrails) | Alta | no intrusiva | baja prob. |
| Shodan/Censys por certificado | Alta | no intrusiva | baja prob. |
| Fuerza bruta suave de subdominios | Media | no intrusiva | baja prob. |
| Hash del favicon en Shodan | Alta | no intrusiva | muy baja prob. |
| Fuga de IP por cabeceras de correo saliente | Media | activa leve | posible |
| Confirmar IP de origen candidata | Alta | **activa** | solo si sale candidata |

**DNS pasivo (OTX + HackerTarget)** — reutiliza las funciones `EsCloudflare`/`InCidr` de la prueba Top #5, luego:
```powershell
"===== AlienVault OTX (con fechas) ====="
try{ $otx=Invoke-RestMethod -Uri "https://otx.alienvault.com/api/v1/indicators/domain/burmancoffee.com/passive_dns" -UserAgent "Mozilla/5.0" -TimeoutSec 60
 $otx.passive_dns | Sort-Object hostname | ForEach-Object { if($_.address -and -not (EsCloudflare $_.address)){ "{0,-38} {1}  <<<<< POSIBLE ORIGEN [{2} {3}..{4}]" -f $_.hostname,$_.address,$_.record_type,$_.first,$_.last } else { "{0,-38} {1}" -f $_.hostname,$_.address } } }catch{ "OTX no respondio" }
"===== HackerTarget ====="
try{ (Invoke-RestMethod -Uri "https://api.hackertarget.com/hostsearch/?q=burmancoffee.com" -TimeoutSec 60) -split "`n" | Where-Object {$_ -match ','} | ForEach-Object { $x=$_.Split(','); if(-not (EsCloudflare $x[1])){ "$($x[0]) $($x[1])  <<<<< POSIBLE ORIGEN" } else { $_ } } }catch{ "HackerTarget: limite diario" }
```

**Fuentes web de histórico/origen** (anota toda IP que NO empiece por `104.16-31 / 172.64-71 / 162.158 / 162.159 / 173.245.48 / 108.162 / 141.101`):
- `https://viewdns.info/iphistory/?domain=burmancoffee.com`
- `https://securitytrails.com/domain/burmancoffee.com/history/a` (cuenta gratuita)
- `https://dnsdumpster.com/` (escribe el dominio)
- Shodan: `https://www.shodan.io/search?query=ssl.cert.subject.CN%3A%22burmancoffee.com%22` y `https://www.shodan.io/domain/burmancoffee.com`
- Censys: `https://search.censys.io/search?resource=hosts&q=burmancoffee.com`

**Fuerza bruta suave de subdominios** (equivale a navegar, no toca el sitio) — reutiliza `EsCloudflare`:
```powershell
$w=@('www','shop','store','tienda','blog','wp','admin','panel','portal','mail','webmail','smtp','api','app','dev','test','stage','staging','qa','demo','beta','old','new','backup','origin','direct','cpanel','whm','ftp','vpn','remote','ns1','ns2','cdn','assets','img','static','media','files','support','status','git','db','internal','intranet','office','secure','login','sso','my','client','order','checkout','pay','news','newsletter','go','track','stats','sandbox','v1','v2')
foreach($s in $w){ $fqdn="$s.burmancoffee.com"
  try{ $a=Resolve-DnsName -Name $fqdn -Type A -ErrorAction Stop | ?{ $_.Type -eq 'A' }
    if($a){ foreach($ip in $a.IPAddress){ if(EsCloudflare $ip){ "{0,-30} {1} [Cloudflare]" -f $fqdn,$ip } else { "{0,-30} {1} <<<<< POSIBLE ORIGEN" -f $fqdn,$ip } } } }catch{} }
```
**Nota:** es normal que `mail/smtp/autodiscover` apunten a Google y que `shop` apunte a un SaaS (Shopify/Klaviyo); esos NO son tu origen. Solo interesan IPs de hosting normal.

**Fuga por correo saliente** (activa leve — a tu buzón): genera un correo desde la propia tienda (recuperar contraseña / formulario de contacto) hacia `jburman@burmancoffee.com`, ábrelo en Gmail → "Mostrar original" y lee las líneas `Received:` y cabeceras `X-Originating-IP`, `X-Sender-IP`, `X-PHP-Originating-Script`. Una IP no-Cloudflare/no-Google es candidata a origen.

---

### E) Ficheros y aplicación web

| Prueba | Sev. | Intrus. | ¿Hallazgo esperado? |
|---|---|---|---|
| robots.txt / sitemap / Wayback | Informativa | no intrusiva | 🎯 suele dar rutas |
| Huella de tecnología (cabeceras/cookies/404) | Baja | no intrusiva | 🎯 revela plataforma |
| Paneles de acceso (/admin, /wp-login) | Media | no intrusiva | posible |
| Source maps (.js.map) | Media | no intrusiva | posible |
| Métodos HTTP (OPTIONS lectura) | Media | no intrusiva | probable limpio |
| .git / .env / .DS_Store | Alta | no intrusiva | ver Top #8 |
| Listados de directorio abiertos | Media | no intrusiva | baja prob. |
| Copias de seguridad (.bak/.zip/.sql) | Alta | no intrusiva | baja prob., alto impacto |

**Rutas que el sitio revela:** abre `https://burmancoffee.com/robots.txt`, `…/sitemap.xml`, `…/.well-known/security.txt`. Histórico real: `https://web.archive.org/web/*/burmancoffee.com/*`. **Ojo:** que una ruta esté en `Disallow` NO la protege; solo pide que no la indexen.

**Huella + paneles + source maps + métodos (bloque combinado):**
```powershell
$ua="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0 Safari/537.36"; $base="https://burmancoffee.com"
$home=Invoke-WebRequest "$base/" -UseBasicParsing -UserAgent $ua
"===== Cookies (pista de plataforma) ====="; $home.Headers["Set-Cookie"]
"===== ¿WordPress? (si /wp-json/ da JSON, lo es) ====="
try{ (Invoke-WebRequest "$base/wp-json/" -UseBasicParsing -UserAgent $ua).StatusCode }catch{ "no WP o bloqueado" }
"===== Paneles (200/302/401 = existe) ====="
foreach($p in "/admin","/wp-login.php","/wp-admin/","/account","/login","/phpmyadmin/"){
  try{ $r=Invoke-WebRequest "$base$p" -Method Head -UseBasicParsing -TimeoutSec 12 -UserAgent $ua -ErrorAction Stop; "{0,-16} -> {1}" -f $p,[int]$r.StatusCode }
  catch{ if($_.Exception.Response){ "{0,-16} -> {1}" -f $p,[int]$_.Exception.Response.StatusCode } }
  Start-Sleep -Milliseconds 400 }
"===== Métodos que anuncia el servidor ====="
try{ $o=Invoke-WebRequest "$base/" -Method Options -UseBasicParsing -UserAgent $ua -ErrorAction Stop; "Allow: "+$o.Headers["Allow"] }catch{ "OPTIONS bloqueado (Cloudflare)" }
```
**Positivo:** cookies `wordpress_`/`woocommerce_`/`PHPSESSID` delatan la plataforma; un panel en `200/302/401` es superficie a proteger con MFA y límite de intentos; en `Allow:`, ver `PUT`/`DELETE`/`TRACE`/`PROPFIND` sería hallazgo (probable que solo salga `GET, HEAD, POST, OPTIONS`).

**Listados de directorio + copias de seguridad** (une con el bloque Top #8; añade estas rutas):
```powershell
$dirs=@("/uploads/","/wp-content/uploads/","/backup/","/backups/","/files/","/media/","/tmp/")
foreach($d in $dirs){ try{ $r=Invoke-WebRequest "https://burmancoffee.com$d" -UseBasicParsing -TimeoutSec 12
  if($r.Content -match "Index of /"){ "$d -> LISTADO ABIERTO" } else { "$d -> $([int]$r.StatusCode) sin listado" } }catch{ if($_.Exception.Response){"$d -> $([int]$_.Exception.Response.StatusCode)"} } ; Start-Sleep -Milliseconds 400 }
```

---

### F) E-commerce y terceros

| Prueba | Sev. | Intrus. | ¿Hallazgo esperado? |
|---|---|---|---|
| Identificar plataforma + fuga de versión | Informativa | no intrusiva | 🎯 base para 5/6 |
| **Secretos en el frontend (Klaviyo/Stripe)** | Alta | no intrusiva | 🎯 revisar bien |
| Endpoints Shopify (si aplica) | Baja | no intrusiva | solo si es Shopify |
| Endpoints WordPress/Woo (si aplica) | Media | no intrusiva | 🎯 si es WordPress |
| Manipulación de carrito/precios | Alta | **activa** | ver sección permiso |

**Identificar plataforma:** `https://www.wappalyzer.com/lookup/burmancoffee.com/` o `https://builtwith.com/burmancoffee.com`. Si es WordPress/Woo, haz los endpoints de abajo.

**Secretos en el frontend (importante):** en Chrome abre la home, `Ctrl+U`, `Ctrl+F` y busca: `sk_live`, `sk_test`, `AKIA`, `AIza`, `private`, `secret`, `token`, `klaviyo`. Luego F12 → Sources → `Ctrl+Shift+F` y repite en todos los JS.
```powershell
$ua='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0 Safari/537.36'; $base='https://burmancoffee.com'
$home=(Invoke-WebRequest "$base/" -UseBasicParsing -UserAgent $ua).Content
$pat='sk_live_[0-9a-zA-Z]{10,}','sk_test_[0-9a-zA-Z]{10,}','rk_live_[0-9a-zA-Z]{10,}','AKIA[0-9A-Z]{16}','AIza[0-9A-Za-z_-]{35}','ghp_[0-9A-Za-z]{36}','-----BEGIN [A-Z ]*PRIVATE KEY-----','pk_[0-9a-zA-Z]{20,}'
function Scan($t,$o){ foreach($p in $pat){ foreach($m in [regex]::Matches($t,$p)){ '['+$o+'] '+$m.Value } } }
Scan $home 'HTML'
$urls=[regex]::Matches($home,'src="([^"]+[.]js[^"]*)"')|%{$_.Groups[1].Value}|Select-Object -Unique
foreach($u in $urls){ if($u -match '^//'){$u='https:'+$u} elseif($u -match '^/'){$u=$base+$u} elseif($u -notmatch '^http'){$u=$base+'/'+$u}
  try{ Scan (Invoke-WebRequest $u -UseBasicParsing -UserAgent $ua).Content $u }catch{} }
"===== Fin (todo lo listado necesita revision manual) ====="
```
**Positivo / CRÍTICO:** `sk_live_`, `rk_live_`, `AKIA`, o un bloque `PRIVATE KEY` → rotar YA. **`pk_` es AMBIGUO:** si es de **Stripe** (`pk_live`/`pk_test`) es clave **pública** y es normal; si es la **privada de Klaviyo** (empieza por `pk_`) es **CRÍTICO** (permite exportar toda tu base de clientes). Verifica en el panel de Stripe/Klaviyo a cuál corresponde. La *public key* de 6 caracteres de Klaviyo es esperada, NO es hallazgo.

**Endpoints WordPress/WooCommerce** (solo si es WordPress):
```powershell
$ua='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0 Safari/537.36'
try{ $u=Invoke-RestMethod 'https://burmancoffee.com/wp-json/wp/v2/users' -UserAgent $ua -ErrorAction Stop; 'USUARIOS EXPUESTOS:'; $u|Select id,name,slug|Format-Table -Auto }catch{ "wp-json/users -> $($_.Exception.Response.StatusCode.value__) (bien)" }
try{ $x=Invoke-WebRequest 'https://burmancoffee.com/xmlrpc.php' -UseBasicParsing -UserAgent $ua -ErrorAction Stop; "xmlrpc.php -> $($x.StatusCode) (habilitado)" }catch{ "xmlrpc.php -> $($_.Exception.Response.StatusCode.value__)" }
$home=(Invoke-WebRequest 'https://burmancoffee.com/' -UseBasicParsing -UserAgent $ua).Content
"===== PLUGINS/VERSIONES ====="
([regex]::Matches($home,'wp-content/plugins/([^/]+)/[^"]*ver=([0-9.]+)')|%{ $_.Groups[1].Value+' v'+$_.Groups[2].Value })|Select -Unique
```
**Positivo:** `wp-json/users` que devuelve nombres = enumeración de usuarios (facilita fuerza bruta contra `/wp-login.php`); `xmlrpc.php` con `200` = habilitado (bloquéalo); lista de plugins con versión → busca CVE en `https://wpscan.com/plugins`.

**Endpoints Shopify** (solo si es Shopify): abre `https://burmancoffee.com/products.json` y `…/cart.js`. Es comportamiento normal de Shopify, pero **reporta** si aparecen productos con `published_at` en el futuro (lanzamientos secretos filtrados). `/admin` debe redirigir a `accounts.shopify.com`.

---

### G) OSINT y fugas de información

| Prueba | Sev. | Intrus. | ¿Hallazgo esperado? |
|---|---|---|---|
| Google/Bing dorking | Media | no intrusiva | 🎯 ver Top #6 |
| Wayback (histórico de rutas) | Media | no intrusiva | 🎯 suele dar rutas |
| Have I Been Pwned | Alta | no intrusiva | 🎯 ver Top #3 |
| Hudson Rock (infostealers) | Alta | no intrusiva | ver Top #4 |
| Secretos en GitHub/pastes | Alta | no intrusiva | posible |
| OSINT de correos/empleados | Baja | no intrusiva | informativo |
| Metadatos en documentos | Baja | no intrusiva | baja prob. |

**Wayback (rutas históricas que pueden seguir vivas):**
```powershell
$out="$env:USERPROFILE\Desktop\wayback_burmancoffee.txt"
Invoke-WebRequest -Uri "http://web.archive.org/cdx/search/cdx?url=burmancoffee.com*&output=text&fl=original&collapse=urlkey&limit=10000" -UseBasicParsing -OutFile $out -TimeoutSec 180
Get-Content $out | Select-String -Pattern "admin|login|wp-admin|phpmyadmin|\.sql|\.bak|\.zip|\.env|\.log|config|backup|checkout|account|invoice|upload|staging|dev" | Set-Content "$env:USERPROFILE\Desktop\wayback_interesantes.txt"
notepad "$env:USERPROFILE\Desktop\wayback_interesantes.txt"
```
Abre cada ruta interesante en Chrome sobre `burmancoffee.com`; si carga o pide login, sigue viva hoy.

**Secretos en GitHub / pastes** (requiere cuenta gratuita de GitHub logueada):
```
https://github.com/search?q=%22burmancoffee.com%22+(password+OR+api_key+OR+secret+OR+token+OR+smtp)&type=code
https://github.com/search?q=%22burmancoffee.com%22&type=commits
https://grep.app/search?q=burmancoffee.com
https://www.google.com/search?q=(site%3Apastebin.com+OR+site%3Arentry.co)+burmancoffee.com
```
**Positivo:** dominio junto a una clave/contraseña → trátala como comprometida y rótala. Aunque el repo se borre, si sale en `commits` sigue siendo público.

**OSINT de correos/empleados** (defensivo): `https://hunter.io/search/burmancoffee.com`, `https://intelx.io/?s=burmancoffee.com`, LinkedIn vía `https://www.google.com/search?q=site%3Alinkedin.com%2Fin+%22burmancoffee%22`. Úsalo para saber qué cuentas proteger primero con 2FA.

**Metadatos:** descarga un PDF que salga en el dorking y súbelo a `https://www.metadata2go.com/` para ver `Author`, software y versión (nombres de empleados, software antiguo).

---

### H) Cloudflare / infraestructura

| Prueba | Sev. | Intrus. | ¿Hallazgo esperado? |
|---|---|---|---|
| Buckets S3/GCS adivinables | Alta | no intrusiva | posible, alto impacto |
| CORS mal configurado | Media | no intrusiva | posible |
| security.txt ausente | Informativa | no intrusiva | 🎯 confirmado casi |
| Cobertura Cloudflare (`/cdn-cgi/trace`) | Informativa | no intrusiva | probable OK |
| Rate-limiting en login | Media | **activa** | ver sección permiso |

**Buckets en la nube:**
```powershell
$nombres=@("burmancoffee","burman-coffee","burmancoffee-backups","burmancoffee-backup","burmancoffee-assets","burmancoffee-media","burmancoffee-uploads","burmancoffee-prod","burmancoffee-db","burmancoffee-store","backups-burmancoffee")
foreach($n in $nombres){ foreach($u in @("https://$n.s3.amazonaws.com/","https://storage.googleapis.com/$n/")){
  try{ $r=Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 12
    $x=if($r.Content -match "<ListBucketResult"){"  <<< LISTADO PUBLICO"}else{""}; Write-Host "[200] $u$x" -ForegroundColor Green }
  catch{ $c=0; if($_.Exception.Response){$c=[int]$_.Exception.Response.StatusCode}; if($c -eq 403){ Write-Host "[403 existe-privado] $u" -ForegroundColor Yellow } } } }
```
También: `https://buckets.grayhatwarfare.com/` → busca "burmancoffee". **Verde con `<ListBucketResult>`** = bucket público (grave si hay backups/SQL).

**CORS:**
```powershell
$evil="https://atacante-falso.example"
foreach($t in "https://burmancoffee.com/","https://burmancoffee.com/wp-json/","https://burmancoffee.com/?wc-ajax=get_refreshed_fragments"){
  try{ $r=Invoke-WebRequest -Uri $t -Headers @{Origin=$evil} -UseBasicParsing -TimeoutSec 12
    $acao=($r.Headers["Access-Control-Allow-Origin"] -join ","); $acac=($r.Headers["Access-Control-Allow-Credentials"] -join ",")
    if($acao){ "[$($r.StatusCode)] $t  ACAO='$acao' ACAC='$acac'" } else { "[$($r.StatusCode)] sin CORS (bien) $t" } }catch{ "no accesible $t" } }
```
**Positivo:** `ACAO` que **refleja** `atacante-falso.example` es lo peor (y con `ACAC=true` = CRÍTICO). `ACAO=*` es hallazgo medio.

**security.txt** (confirma la ausencia ya sospechada): abre `https://burmancoffee.com/.well-known/security.txt` y `…/security.txt`. Ambos `404` = falta (recomendación: publicar uno con `Contact: mailto:jburman@burmancoffee.com`, generado en `https://securitytxt.org/`).

**Cobertura Cloudflare:** abre `https://burmancoffee.com/cdn-cgi/trace` — debe mostrar `fl=…`, `h=burmancoffee.com`, `tls=TLSv1.3`. Un host que carga la web pero **no** tiene esta firma podría no estar proxeado (revísalo en el panel de Cloudflare).

---

## ⚠️ Solo con permiso / en staging

Estas pruebas **pueden tocar producción, disparar el WAF de Cloudflare o registrar datos**. Requieren el OK explícito del dueño y, a ser posible, hacerse contra **staging** (hoy da 502; pedir al equipo que lo levante). **Nunca completes un pago real ni envíes correo suplantado a nadie que no sea tu propio buzón.**

| Prueba | Riesgo | Cómo hacerla con cuidado |
|---|---|---|
| **Spoofing al propio buzón** (Top #2) | Envía un correo falsificado | Solo a `jburman@burmancoffee.com`. Nunca a clientes/proveedores. Es la demo más potente para el jefe. |
| **Confirmar IP de origen candidata** | Conexión directa al servidor real | Solo si las pruebas D dieron una IP no-Cloudflare. 1 petición GET por IP, fuera de hora pico, sin bucles. |
| **Manipulación de carrito/precios** | Modifica el carrito, puede registrar pedidos | En STAGING. Con F12→Network copia la petición de cambio de cantidad y prueba `quantity=-1`; mira si el servidor recalcula el total. |
| **Métodos PUT/DELETE/TRACE** | Puede escribir/borrar ficheros | Solo la lectura con OPTIONS es segura. Probar PUT real: en staging, pactado. |
| **Rate-limiting en login** | Intentos de acceso repetidos | 10 intentos lentos con un usuario **inexistente** (no bloquea a clientes). Para en cuanto veas `429` o challenge. |

**Confirmar IP de origen (si tienes una candidata):**
```powershell
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
[Net.ServicePointManager]::ServerCertificateValidationCallback={$true}
$dominio="burmancoffee.com"
$candidatas=@("1.2.3.4")   # <-- SUSTITUYE por las IPs reales encontradas
foreach($ip in $candidatas){ foreach($esq in @("https","http")){ $uri="{0}://{1}/" -f $esq,$ip
  try{ $r=Invoke-WebRequest -Uri $uri -Headers @{Host=$dominio} -UseBasicParsing -TimeoutSec 12 -MaximumRedirection 0 -ErrorAction Stop
    $c=if($r.RawContent -match 'burman|coffee|add-to-cart|woocommerce|wp-content|cart'){'<<<<< COINCIDE: ORIGEN real'}else{'(responde, sin coincidencia)'}
    "{0,-26} HTTP {1} {2}" -f $uri,$r.StatusCode,$c }
  catch{ $resp=$_.Exception.Response; if($resp){ "{0,-26} HTTP {1}" -f $uri,[int]$resp.StatusCode } else { "{0,-26} sin respuesta" -f $uri } } } }
```
**Positivo:** `<<<<< COINCIDE` = esa IP sirve la tienda saltándose Cloudflare. Arreglo: en el firewall del origen, permitir **solo** IPs de Cloudflare, y rotar la IP.

**Rate-limiting en login (10 intentos, usuario inexistente):**
```powershell
$login="https://burmancoffee.com/wp-login.php"   # cambia si el login real es otra URL
$usuario="pentest-noexiste-0001@example.com"
for($i=1;$i -le 10;$i++){ $body=@{ log=$usuario; pwd=("Xx-noexiste-{0}!" -f $i); "wp-submit"="Log In" }
  try{ $r=Invoke-WebRequest -Uri $login -Method Post -Body $body -UseBasicParsing -TimeoutSec 15 -ErrorAction Stop; "Intento $i: HTTP $([int]$r.StatusCode)" }
  catch{ $c=0; if($_.Exception.Response){$c=[int]$_.Exception.Response.StatusCode}
    if($c -eq 429){ Write-Host "Intento $i: 429 RATE-LIMIT (bien). PARANDO." -ForegroundColor Green; break }
    elseif($c -eq 403){ Write-Host "Intento $i: 403 challenge Cloudflare (bien). PARANDO." -ForegroundColor Green; break }
    else{ "Intento $i: HTTP $c" } }
  Start-Sleep -Seconds 1 }
```
**Positivo:** si los 10 pasan sin `429`/CAPTCHA/challenge = no hay rate-limiting (activa Rate Limiting Rules en Cloudflare).

---

## Ya probado (no repetir)

| Área | Resultado verificado | Riesgo | Recomendación |
|---|---|---|---|
| **DMARC** | `p=none` (solo monitor), confirmado en vivo | 🟡 Medio | Subir a `p=quarantine` → `p=reject` |
| **SPF** | `~all` (softfail), confirmado | 🟡 Medio | Endurecer a `-all` (hardfail) |
| **DKIM** | 3 claves; una **RSA 1024-bit** (débil, confirmada con openssl) | 🟡 Medio | Rotar el selector débil a 2048 bits |
| **IP de origen** | NO se filtra por dev/staging/cpanel/webmail/ftp | 🟢 Bien | Mantener; vigilar nuevos subdominios |
| **dev / staging** | Existen, tras Cloudflare, devuelven **502 Bad Gateway (nginx)** = backend caído | 🟢 Higiene | No es brecha; apagar o proteger si no se usan |
| **DNSSEC** | Unsigned (no habilitado) | 🟡 Medio | Activar en Cloudflare (1 clic) + subir DS al registrador |
| **security.txt** | Ausente | ⚪ Informativo | Publicar `/.well-known/security.txt` con contacto |
| **HSTS** | Probablemente ausente (pendiente confirmar con Top #1/#7) | 🟡 Medio | Añadir HSTS + preload tras periodo de prueba |
| **TLS / certificado** | TLS 1.3, cert Google Trust Services **válido** | 🟢 Bien | Ninguna |
| **Infra delante** | Cloudflare (WAF+CDN+DNS), correo Google Workspace, marketing Klaviyo | 🟢 Contexto | — |

---

## Lectura honesta de resultados

**Muy probable que salga HALLAZGO (prioriza y captura):**
- Faltan cabeceras HSTS / CSP (Top #1, #7).
- DMARC sin `sp=` ni `rua=`; SPF `~all`; DKIM 1024 (ya conocidos, solo confirmar).
- MTA-STS y TLS-RPT ausentes (típico en PYME).
- Algún correo en Have I Been Pwned (Top #3).
- security.txt ausente.

**Puede o no salir (revisa con calma):**
- Hudson Rock (infostealers), typosquatting, CORS, buckets, enumeración de usuarios de WordPress, tokens DNS olvidados, secretos en GitHub.

**Casi seguro sale LIMPIO (bueno; documenta que se comprobó):**
- Fuga del servidor de origen (ya está bien oculto).
- `.git` / `.env` / backups / listados de directorio (Cloudflare + hosting suelen bloquear) — **pero si aparece uno, es lo más grave de toda la lista**.
- Transferencia de zona AXFR, contenido mixto, protocolos TLS obsoletos.

**Para el informe al jefe:** las capturas de **securityheaders** (nota A-F), del **correo falsificado que llega a tu buzón**, y de **Have I Been Pwned** son las tres más contundentes y fáciles de explicar. El arreglo de mayor impacto y menor coste: **DMARC `p=reject` + SPF `-all` + rotar la clave DKIM de 1024 + activar DNSSEC y HSTS en Cloudflare.**