#!/usr/bin/env bash
#
# recon.sh — Batería de pruebas de seguridad NO INTRUSIVAS para burmancoffee.com
# ---------------------------------------------------------------------------
# Todas las comprobaciones son de SOLO LECTURA y equivalen a lo que hace un
# navegador o una consulta DNS normal. NO hay fuzzing, inyección, fuerza bruta
# ni nada que pueda degradar el sitio. Es seguro ejecutarlo contra producción.
#
# Uso:
#   ./recon.sh                    # objetivo por defecto: burmancoffee.com
#   ./recon.sh midominio.com      # otro objetivo
#   ./recon.sh burmancoffee.com | tee recon-$(date +%F).txt
#
# Dependencias: curl, openssl (obligatorias); dig (dnsutils) y python3
# (recomendadas). El script degrada con elegancia si falta alguna.
# ---------------------------------------------------------------------------

set -u
TARGET="${1:-burmancoffee.com}"
UA="Mozilla/5.0 (compatible; SecurityRecon/1.0; +owner-authorized)"
CURL="curl -sS --max-time 20 -A ${UA// /_}"

c_reset=$'\e[0m'; c_bold=$'\e[1m'; c_red=$'\e[31m'; c_grn=$'\e[32m'; c_yel=$'\e[33m'; c_blu=$'\e[36m'
have() { command -v "$1" >/dev/null 2>&1; }
sec()  { echo; echo "${c_bold}${c_blu}=== $* ===${c_reset}"; }
ok()   { echo "  ${c_grn}[OK]${c_reset}  $*"; }
warn() { echo "  ${c_yel}[!] ${c_reset}  $*"; }
bad()  { echo "  ${c_red}[X] ${c_reset}  $*"; }
info() { echo "  [i]   $*"; }

echo "${c_bold}Recon no intrusivo — ${TARGET} — $(date -u +%FT%TZ)${c_reset}"
have dig    || warn "dig no instalado (apt-get install dnsutils) — se omiten algunas pruebas DNS"
have python3|| warn "python3 no instalado — se omite el chequeo de exposición de IP de origen"

# ---------------------------------------------------------------------------
sec "1. Registros DNS"
if have dig; then
  for rr in A AAAA MX NS SOA CAA; do
    out=$(dig +short "$TARGET" "$rr" 2>/dev/null)
    if [ -n "$out" ]; then echo "  ${c_bold}$rr${c_reset}:"; echo "$out" | sed 's/^/      /'; fi
  done
  caa=$(dig +short "$TARGET" CAA 2>/dev/null)
  [ -z "$caa" ] && warn "Sin registro CAA (recomendable: restringir qué CAs pueden emitir certificados)"
fi

# ---------------------------------------------------------------------------
sec "2. DNSSEC"
if have dig; then
  dnskey=$(dig +short "$TARGET" DNSKEY 2>/dev/null)
  ds=$(dig +short "$TARGET" DS 2>/dev/null)
  ad=$(dig +dnssec "$TARGET" A 2>/dev/null | grep -i RRSIG)
  if [ -n "$dnskey" ] || [ -n "$ds" ]; then ok "DNSSEC parece activo (DNSKEY/DS presentes)"; else
    bad "DNSSEC NO habilitado (sin DNSKEY/DS) — vulnerable a spoofing/cache poisoning"; fi
fi

# ---------------------------------------------------------------------------
sec "3. Autenticación de correo (SPF / DMARC / DKIM)"
if have dig; then
  spf=$(dig +short TXT "$TARGET" 2>/dev/null | tr -d '"' | grep -i 'v=spf1')
  if [ -n "$spf" ]; then
    info "SPF: $spf"
    echo "$spf" | grep -q -- '-all' && ok "SPF termina en -all (hardfail)" || warn "SPF no usa -all (softfail ~all o neutral) — suplantación más fácil"
  else bad "Sin registro SPF"; fi

  dmarc=$(dig +short TXT "_dmarc.$TARGET" 2>/dev/null | tr -d '"')
  if [ -n "$dmarc" ]; then
    info "DMARC: $dmarc"
    if   echo "$dmarc" | grep -qi 'p=reject';    then ok   "DMARC p=reject (máxima protección)"
    elif echo "$dmarc" | grep -qi 'p=quarantine';then warn "DMARC p=quarantine (parcial; el objetivo es p=reject)"
    else bad "DMARC p=none (solo monitorización; NO protege de suplantación)"; fi
  else bad "Sin registro DMARC"; fi

  echo "  Buscando selectores DKIM comunes:"
  for sel in google default selector1 selector2 k1 mail dkim s1 s2 klaviyo litesrv; do
    k=$(dig +short TXT "${sel}._domainkey.$TARGET" 2>/dev/null | tr -d '"' | tr -d ' ')
    [ -n "$k" ] && ok "DKIM selector '${sel}' presente"
  done
fi

# ---------------------------------------------------------------------------
sec "4. TLS / SSL"
if have openssl; then
  echo "  Protocolos soportados:"
  for proto in ssl3 tls1 tls1_1 tls1_2 tls1_3; do
    r=$(echo | timeout 12 openssl s_client -connect "${TARGET}:443" -servername "$TARGET" -"$proto" 2>/dev/null | grep -c "BEGIN CERTIFICATE")
    if [ "$r" -ge 1 ]; then
      case $proto in
        ssl3|tls1|tls1_1) bad "  ${proto} NEGOCIADO (obsoleto/inseguro — deshabilitar)";;
        *) ok "  ${proto} soportado";;
      esac
    else info "  ${proto} no soportado"; fi
  done
  echo "  Certificado:"
  echo | timeout 12 openssl s_client -connect "${TARGET}:443" -servername "$TARGET" 2>/dev/null \
    | openssl x509 -noout -subject -issuer -dates 2>/dev/null | sed 's/^/      /'
  echo "  OCSP stapling:"
  st=$(echo | timeout 12 openssl s_client -connect "${TARGET}:443" -servername "$TARGET" -status 2>/dev/null | grep -i "OCSP Response Status")
  [ -n "$st" ] && ok "  $st" || warn "  OCSP stapling no presente"
fi

# ---------------------------------------------------------------------------
sec "5. Cabeceras HTTP de seguridad"
hdr=$($CURL -D - -o /dev/null "https://$TARGET/" 2>/dev/null)
lc=$(echo "$hdr" | tr 'A-Z' 'a-z')

# Detección de página de challenge de Cloudflare (importante: falsea las cabeceras)
if echo "$lc" | grep -q 'cf-mitigated: challenge' || echo "$lc" | grep -q 'server-timing: chlray'; then
  warn "¡OJO! Cloudflare devolvió una PÁGINA DE CHALLENGE — las cabeceras de abajo"
  warn "     pueden ser de esa página, NO de tu aplicación real. Verifica con un"
  warn "     navegador real (DevTools > Network > Response Headers)."
fi

check_hdr () { # nombre_cabecera  mensaje_si_falta  nivel(ok/warn)
  local h="$1"; local miss="$2"
  local v; v=$(echo "$hdr" | grep -i "^$h:" | head -1 | sed 's/\r//')
  if [ -n "$v" ]; then ok "$v"; else
    if [ "${3:-warn}" = "bad" ]; then bad "$miss"; else warn "$miss"; fi
  fi
}
check_hdr "strict-transport-security" "Falta HSTS (Strict-Transport-Security) — riesgo de SSL-stripping" bad
check_hdr "content-security-policy"   "Falta Content-Security-Policy" warn
check_hdr "x-content-type-options"    "Falta X-Content-Type-Options: nosniff" warn
check_hdr "x-frame-options"           "Falta X-Frame-Options (o CSP frame-ancestors)" warn
check_hdr "referrer-policy"           "Falta Referrer-Policy" warn
check_hdr "permissions-policy"        "Falta Permissions-Policy" warn
# Cabeceras obsoletas que conviene retirar/ajustar:
echo "$lc" | grep -q 'x-xss-protection: 1' && warn "x-xss-protection: 1 (obsoleta; recomendado 0 + CSP)"
echo "$lc" | grep -q 'expect-ct'            && warn "Expect-CT presente (obsoleta; puede retirarse)"
srv=$(echo "$hdr" | grep -i '^server:' | head -1 | sed 's/\r//'); [ -n "$srv" ] && info "$srv"

# ---------------------------------------------------------------------------
sec "6. Redirección HTTP -> HTTPS"
loc=$($CURL -D - -o /dev/null "http://$TARGET/" 2>/dev/null | grep -i '^location:' | head -1 | sed 's/\r//')
code=$($CURL -o /dev/null -w '%{http_code}' "http://$TARGET/" 2>/dev/null)
if echo "$loc" | grep -qi 'https://'; then ok "HTTP redirige a HTTPS ($code) -> $loc"
else warn "HTTP no redirige claramente a HTTPS (code $code)"; fi

# ---------------------------------------------------------------------------
sec "7. Cookies (flags de seguridad)"
cookies=$(echo "$hdr" | grep -i '^set-cookie:')
if [ -n "$cookies" ]; then
  echo "$cookies" | while read -r line; do
    l=$(echo "$line" | tr 'A-Z' 'a-z')
    flags=""
    echo "$l" | grep -q 'secure'    || flags="$flags SIN-Secure"
    echo "$l" | grep -q 'httponly'  || flags="$flags SIN-HttpOnly"
    echo "$l" | grep -q 'samesite'  || flags="$flags SIN-SameSite"
    name=$(echo "$line" | sed -E 's/set-cookie:[[:space:]]*([^=]+)=.*/\1/I')
    [ -n "$flags" ] && warn "Cookie '$name':$flags" || ok "Cookie '$name' con flags correctos"
  done
else info "No se observaron cookies en la respuesta inicial"; fi

# ---------------------------------------------------------------------------
sec "8. security.txt (RFC 9116)"
for path in ".well-known/security.txt" "security.txt"; do
  cc=$($CURL -o /dev/null -w '%{http_code}' "https://$TARGET/$path" 2>/dev/null)
  [ "$cc" = "200" ] && { ok "/$path presente (200)"; break; } || info "/$path -> $cc"
done

# ---------------------------------------------------------------------------
sec "9. Rutas/archivos sensibles (solo códigos de estado, no se descarga contenido)"
for p in "robots.txt" "sitemap.xml" ".git/HEAD" ".env" ".well-known/" "wp-login.php" "admin/" "server-status" "config.php.bak" ".DS_Store"; do
  cc=$($CURL -o /dev/null -w '%{http_code}' "https://$TARGET/$p" 2>/dev/null)
  case "$p" in
    ".git/HEAD"|".env"|"config.php.bak"|".DS_Store"|"server-status")
      [ "$cc" = "200" ] && bad "/$p ACCESIBLE (200) — posible exposición sensible" || info "/$p -> $cc";;
    *)
      [ "$cc" = "200" ] && ok "/$p -> 200" || info "/$p -> $cc";;
  esac
done

# ---------------------------------------------------------------------------
sec "10. Subdominios (Certificate Transparency) + exposición de IP de ORIGEN"
subs=$($CURL "https://crt.sh/?q=%25.$TARGET&output=json" 2>/dev/null \
  | tr ',' '\n' | grep -i 'common_name\|name_value' | grep -oiE "[a-z0-9._-]+\.$TARGET" \
  | tr 'A-Z' 'a-z' | sort -u)
if [ -z "$subs" ]; then
  info "crt.sh no devolvió datos (o sin red). Prueba manual: https://crt.sh/?q=%25.$TARGET"
else
  echo "  Subdominios observados:"; echo "$subs" | sed 's/^/      /'
  if have dig && have python3; then
    cfranges=$($CURL https://www.cloudflare.com/ips-v4 2>/dev/null)
    echo "  Comprobando si algún subdominio expone una IP de origen (fuera de Cloudflare):"
    echo "$subs" | while read -r s; do
      [ -z "$s" ] && continue
      ips=$(dig +short "$s" A 2>/dev/null | grep -E '^[0-9]+\.')
      for ip in $ips; do
        inside=$(python3 - "$ip" <<PY 2>/dev/null
import sys,ipaddress
ip=ipaddress.ip_address(sys.argv[1])
ranges="""$cfranges""".split()
print("yes" if any(ip in ipaddress.ip_network(r) for r in ranges if r) else "no")
PY
)
        if [ "$inside" = "no" ]; then
          bad "$s -> $ip  NO es de Cloudflare — POSIBLE IP DE ORIGEN EXPUESTA (permite bypass del WAF)"
        else
          ok "$s -> $ip (Cloudflare)"
        fi
      done
    done
  fi
fi

echo; echo "${c_bold}Fin del recon. Revisa las líneas [X] (rojo) y [!] (amarillo).${c_reset}"
