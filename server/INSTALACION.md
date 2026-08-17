# 🖥 Alojar Burman Inventario en el compu de la bodega

Guía para tener la app corriendo en la computadora de Burman, servida por la red local
(los teléfonos se conectan por wifi). Pensada para Windows; al final están las notas
para Mac/Linux.

> **Lo único delicado**: los navegadores solo permiten usar la cámara en páginas
> **HTTPS**. Por eso el paso 3 crea un certificado local que se instala una vez en
> cada teléfono. Sin ese paso la app abre, pero la cámara no prende.

---

## 1. Preparar la computadora (una sola vez)

1. Instala **Node.js LTS**: https://nodejs.org → botón verde "LTS" → siguiente,
   siguiente, listo.
2. Instala **Git for Windows**: https://gitforwindows.org (trae "Git Bash", que se usa
   para el certificado y para actualizar la app).
3. Descarga la app: abre **Git Bash** y ejecuta

   ```
   cd /c/
   git clone https://github.com/jsgonzalezE/juan.git burman-inventario
   ```

   Queda en `C:\burman-inventario`.

## 2. Arrancar el servidor

Doble clic a **`C:\burman-inventario\server\iniciar-windows.bat`**.

- La primera vez, Windows pregunta por el firewall → **Permitir acceso** (redes privadas).
- La ventana negra muestra las direcciones del servidor. Déjala abierta.
- Prueba en la misma compu: abre `http://localhost:8080` — debe verse la app.

## 3. Certificado para que la cámara funcione (una sola vez)

1. Clic derecho en la carpeta `C:\burman-inventario\server` → **Open Git Bash here**.
2. Ejecuta:

   ```
   ./generar-certificado.sh
   ```

   (detecta la IP de la compu solo; si tiene varias, pásala a mano:
   `./generar-certificado.sh 192.168.1.50`)
3. Cierra y vuelve a abrir el servidor (el `.bat`). Ahora anuncia HTTPS.

**En cada teléfono (una vez):**

1. Conéctalo al **wifi de la bodega**.
2. Abre `http://IP-DE-LA-COMPU:8080/burman-ca.crt` → se descarga el certificado.
3. Instálalo:
   - **Android**: Ajustes → Seguridad y privacidad → Más ajustes → Instalar
     certificados → **Certificado de CA** → elegir el archivo descargado.
     (El menú cambia un poco según la marca; buscar "CA" en Ajustes ayuda.)
   - **iPhone**: al abrir el archivo dice "Perfil descargado" → Ajustes → **Perfil
     descargado** → Instalar. Después: Ajustes → General → Información →
     **Confianza de certificados** → activar "Burman Coffee CA local".
4. Abre **`https://IP-DE-LA-COMPU:8443`** → menú del navegador → **Agregar a pantalla
   de inicio**. Acepta el permiso de cámara. Listo: ya es la app de trabajo.

## 4. Recomendado: IP fija

En el router de la bodega, reserva la IP de esa computadora (DHCP reservation /
"IP fija por MAC"). Así la dirección nunca cambia. Si algún día cambia, se vuelve a
correr `./generar-certificado.sh IP-NUEVA` y ya.

## 5. Que arranque solo al prender el compu

1. Clic derecho a `iniciar-windows.bat` → **Crear acceso directo**.
2. Teclas `Windows + R` → escribe `shell:startup` → Enter.
3. Arrastra el acceso directo a esa carpeta. Con eso el servidor arranca al iniciar
   sesión.

## 6. Actualizar la app cuando haya versión nueva

Abrir Git Bash en `C:\burman-inventario` y:

```
git pull
```

Reiniciar el servidor. **Los datos no se tocan**: viven en cada teléfono (y se
respaldan desde Ajustes → Datos y respaldo).

---

## Alternativas

- **Sin certificados, con HTTPS válido**: instalar [Tailscale](https://tailscale.com)
  (gratis para equipos chicos) en la compu y en los teléfonos, y en la compu correr
  `tailscale serve --bg 8080`. Da una dirección `https://…ts.net` con certificado real,
  sin instalar nada en los teléfonos, y funciona incluso fuera de la bodega.
- **GitHub Pages** (`https://jsgonzaleze.github.io/juan/`): sigue disponible como
  respaldo; la app funciona sin internet igual una vez instalada, porque todo corre en
  el teléfono.

## Mac / Linux

Igual pero sin `.bat`: `node server/serve.js` en una terminal, y el certificado con
`./server/generar-certificado.sh`. Para autoarranque, un servicio de systemd o un
"Login Item".
