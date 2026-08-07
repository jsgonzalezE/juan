#!/usr/bin/env bash
#
# origin-discovery.sh — ¿Se puede encontrar la IP de ORIGEN detrás de Cloudflare?
# ---------------------------------------------------------------------------
# Toda la seguridad de burmancoffee.com descansa en Cloudflare (WAF + CDN).
# Si un atacante descubre la IP real del servidor de origen, se SALTA Cloudflare
# por completo y ataca el servidor directamente. Este es el hueco nº1 que busca
# un pentester en una web "detrás de Cloudflare".
#
# Este script usa OSINT PASIVO + una verificación mínima (una petición HTTP por
# candidato). Es no intrusivo y seguro contra producción.
#
# Uso:  ./origin-discovery.sh [dominio]   (por defecto burmancoffee.com)
# Deps: dig, curl, python3 (recomendado)
# ---------------------------------------------------------------------------
set -u
TARGET="${1:-burmancoffee.com}"
c_reset=$'\e[0m'; c_bold=$'\e[1m'; c_red=$'\e[31m'; c_grn=$'\e[32m'; c_yel=$'\e[33m'; c_blu=$'\e[36m'
have(){ command -v "$1" >/dev/null 2>&1; }
sec(){ echo; echo "${c_bold}${c_blu}=== $* ===${c_reset}"; }
hit(){ echo "  ${c_red}${c_bold}[ORIGEN?]${c_reset} $*"; }
ok(){ echo "  ${c_grn}[cf]${c_reset}  $*"; }
info(){ echo "  [i]  $*"; }

have dig  || { echo "Necesitas 'dig' (apt-get install dnsutils)"; exit 1; }
echo "${c_bold}Búsqueda de IP de origen — ${TARGET} — $(date -u +%FT%TZ)${c_reset}"

# --- Rangos de Cloudflare (para saber qué IP NO es de Cloudflare = candidata a origen)
CF=$(curl -sS --max-time 15 https://www.cloudflare.com/ips-v4 2>/dev/null)
is_cf(){ # $1=ip -> "yes"/"no"
  have python3 || { echo "unknown"; return; }
  python3 - "$1" <<PY 2>/dev/null
import sys,ipaddress
ip=ipaddress.ip_address(sys.argv[1]); R="""$CF""".split()
print("yes" if any(ip in ipaddress.ip_network(r) for r in R if r) else "no")
PY
}

CANDIDATES=""   # acumula IPs sospechosas
note_ip(){ # $1=host $2=ip
  local v; v=$(is_cf "$2")
  if [ "$v" = "no" ]; then hit "$1 -> $2  (NO es Cloudflare — posible ORIGEN)"; CANDIDATES="$CANDIDATES $2";
  elif [ "$v" = "yes" ]; then ok "$1 -> $2 (Cloudflare)";
  else info "$1 -> $2 (no se pudo clasificar; sin python3)"; fi
}

# ---------------------------------------------------------------------------
sec "1. Hostnames que suelen apuntar al origen (saltándose el proxy)"
# Nombres clásicos que los admins dejan sin proxear (naranja->gris) en Cloudflare
for h in dev staging stage test qa origin direct direct-connect cpanel webmail \
         ftp mail smtp mx mx1 email server host vpn remote portal old legacy \
         backup api admin panel autodiscover cpcalendars cpcontacts ssh git; do
  fqdn="${h}.${TARGET}"
  for ip in $(dig +short "$fqdn" A 2>/dev/null | grep -E '^[0-9]+\.'); do
    note_ip "$fqdn" "$ip"
  done
done

# ---------------------------------------------------------------------------
sec "2. Todos los nombres en Certificate Transparency (crt.sh)"
subs=$(curl -sS --max-time 25 "https://crt.sh/?q=%25.$TARGET&output=json" 2>/dev/null \
  | tr ',{}' '\n' | grep -oiE "[a-z0-9._*-]+\.$TARGET" | tr 'A-Z' 'a-z' \
  | sed 's/^\*\.//' | sort -u)
if [ -n "$subs" ]; then
  echo "$subs" | sed 's/^/      /'
  echo "  Resolviendo cada uno para ver si alguno se sale de Cloudflare:"
  while read -r s; do
    [ -z "$s" ] && continue
    for ip in $(dig +short "$s" A 2>/dev/null | grep -E '^[0-9]+\.'); do note_ip "$s" "$ip"; done
  done <<< "$subs"
else
  info "crt.sh sin datos (o sin red). Manual: https://crt.sh/?q=%25.$TARGET"
fi

# ---------------------------------------------------------------------------
sec "3. Registros de correo (los MX/mail a veces viven en el origen)"
for ip in $(dig +short "$TARGET" MX 2>/dev/null | awk '{print $2}' | while read -r m; do dig +short "$m" A 2>/dev/null; done | grep -E '^[0-9]+\.'); do
  v=$(is_cf "$ip"); [ "$v" = "no" ] && info "MX -> $ip (revisar; si es tu hosting propio, puede ser el origen)" || ok "MX -> $ip"
done
info "MX del informe = Google Workspace, así que aquí probablemente no está el origen."

# ---------------------------------------------------------------------------
sec "4. Verificación: ¿algún candidato sirve el sitio directamente?"
CANDIDATES=$(echo "$CANDIDATES" | tr ' ' '\n' | sort -u | grep -E '^[0-9]+\.')
if [ -z "$CANDIDATES" ]; then
  ok "No se encontraron IPs fuera de Cloudflare por estas vías. El origen parece bien oculto. 👍"
else
  echo "  Probando cada candidato con Host: $TARGET (una petición benigna cada uno):"
  while read -r ip; do
    [ -z "$ip" ] && continue
    code=$(curl -sS --max-time 12 -o /dev/null -w '%{http_code}' --resolve "$TARGET:443:$ip" "https://$TARGET/" 2>/dev/null)
    if [ "$code" != "000" ] && [ -n "$code" ]; then
      hit "$ip responde al sitio directamente (HTTP $code) => ORIGEN CONFIRMADO / bypass de WAF posible"
      info "     Mitiga: rota la IP, activa Authenticated Origin Pulls y firewall que solo acepte rangos de Cloudflare."
    else
      info "$ip no sirvió el sitio directamente (code $code) — candidato débil."
    fi
  done <<< "$CANDIDATES"
fi

# ---------------------------------------------------------------------------
sec "5. Otras fuentes de histórico DNS (requieren cuenta/API — revisar a mano)"
cat <<EOF
  Estas fuentes guardan la IP de origen ANTES de que se activara Cloudflare:
    - SecurityTrails : https://securitytrails.com/domain/$TARGET/history/a
    - Shodan         : https://www.shodan.io/search?query=hostname:$TARGET  (o ssl.cert.subject.cn:$TARGET)
    - Censys         : https://search.censys.io/search?q=$TARGET
    - DNS History    : https://dnshistory.org/dns-records/$TARGET
    - ViewDNS        : https://viewdns.info/iphistory/?domain=$TARGET
  Si alguna muestra una IP que NO es de Cloudflare, pruébala con:
    curl -I --resolve $TARGET:443:<IP> https://$TARGET/
EOF
echo; echo "${c_bold}Líneas [ORIGEN?] en rojo = lo que hay que investigar.${c_reset}"
