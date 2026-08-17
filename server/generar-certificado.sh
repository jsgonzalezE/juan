#!/usr/bin/env bash
#
# Genera el certificado HTTPS local de Burman Inventario.
# Crea una "autoridad" propia (burman-ca.crt, que se instala UNA VEZ en cada
# teléfono) y el certificado del servidor firmado por ella.
#
# En Windows: ejecutar desde Git Bash (viene con Git for Windows).
# En Mac/Linux: ejecutar en la terminal normal. Requiere openssl.
#
#   ./generar-certificado.sh            → detecta la IP sola
#   ./generar-certificado.sh 192.168.1.50   → usa esa IP
#
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v openssl >/dev/null 2>&1; then
  echo "✘ No encontré openssl. En Windows abre esto desde Git Bash (instala Git for Windows)."
  exit 1
fi

IP="${1:-}"
if [ -z "$IP" ]; then
  IP=$(node -e "const i=require('os').networkInterfaces();for(const n in i){for(const x of i[n]){if(x.family==='IPv4'&&!x.internal){console.log(x.address);process.exit(0)}}}" 2>/dev/null || true)
fi
if [ -z "$IP" ]; then
  echo "Escribe la IP de esta computadora en la red (ej. 192.168.1.50):"
  read -r IP
fi

mkdir -p certs
cd certs

DIAS=3650  # 10 años

if [ ! -f burman-ca.key ]; then
  echo "→ Creando la autoridad local (burman-ca)…"
  openssl genrsa -out burman-ca.key 2048 2>/dev/null
  openssl req -x509 -new -nodes -key burman-ca.key -sha256 -days $DIAS \
    -subj "/CN=Burman Coffee CA local/O=Burman Coffee" -out burman-ca.crt
fi

echo "→ Creando el certificado del servidor para $IP…"
openssl genrsa -out key.pem 2048 2>/dev/null
openssl req -new -key key.pem -subj "/CN=Burman Inventario/O=Burman Coffee" -out server.csr

cat > san.cnf <<EOF
subjectAltName = IP:$IP, IP:127.0.0.1, DNS:localhost, DNS:burman.local
EOF

openssl x509 -req -in server.csr -CA burman-ca.crt -CAkey burman-ca.key \
  -CAcreateserial -days $DIAS -sha256 -extfile san.cnf -out cert.pem 2>/dev/null

rm -f server.csr san.cnf

echo ""
echo "✔ Listo. Archivos en server/certs/:"
echo "   - cert.pem + key.pem   → los usa el servidor automáticamente"
echo "   - burman-ca.crt        → instálalo UNA VEZ en cada teléfono"
echo ""
echo "Arranca el servidor (node server/serve.js) y en los teléfonos abre:"
echo "   http://$IP:8080/burman-ca.crt   (para descargar el certificado)"
echo "   https://$IP:8443/               (la app, ya con cámara)"
echo ""
echo "Si la IP de la compu cambia, vuelve a correr este script con la IP nueva."
