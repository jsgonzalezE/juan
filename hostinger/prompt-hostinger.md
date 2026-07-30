# Prompt para el asistente de IA de Hostinger (Kodee)

Copia todo el bloque de abajo y pégalo en el chat del asistente de Hostinger.

---

Hola. Necesito documentar la configuración técnica de mi hosting para que un
desarrollador remoto pueda trabajar en mi sitio. Respóndeme de forma concreta
y ordenada a TODO lo siguiente.

**IMPORTANTE SOBRE SEGURIDAD:** no escribas ninguna contraseña, token, llave
privada ni credencial en tu respuesta. Para cada credencial que haga falta,
dime únicamente en qué pantalla del hPanel se genera o se restablece. Yo las
manejaré por separado.

## 1. Identificación del entorno

- ¿Qué plan tengo exactamente (Shared, Cloud, VPS)?
- ¿El sitio está hecho con Hostinger Website Builder, con WordPress, o son
  archivos que subí yo?
- ¿Cuál es el dominio principal y qué subdominios existen?
- ¿Hay un entorno de staging o solo producción?

## 2. Acceso por Git (esto es lo prioritario)

- ¿Mi plan incluye la función "Git" del hPanel?
- Si sí: ¿cómo conecto un repositorio de GitHub, qué ruta de destino usa, y se
  puede activar auto-deploy por webhook?
- ¿Qué rama se despliega por defecto?

## 3. Acceso SSH

- ¿Mi plan incluye SSH?
- Si sí: host, puerto y usuario (sin contraseña).
- ¿Puedo usar llaves SSH en vez de contraseña? ¿Dónde subo la llave pública?
- ¿Hay restricción por IP? Mi conexión sale desde una IP dinámica de un
  servidor en la nube, así que necesito saber si eso es un problema.

## 4. Acceso FTP/SFTP

- Host, puerto, usuario y protocolo exacto (¿FTP, FTPS o SFTP?).
- ¿Hay lista blanca de IPs?

## 5. Rutas de archivos

- ¿Cuál es la ruta absoluta del document root de mi sitio? (algo como
  `/home/uXXXXXXXX/domains/midominio.com/public_html`)
- ¿Dónde están los logs de error del servidor?

## 6. Stack técnico

- Versión de PHP activa y si la puedo cambiar.
- ¿Hay soporte de Node.js? ¿Qué versión?
- Servidor web (Apache / LiteSpeed / nginx) y si respeta `.htaccess`.
- ¿Hay caché o CDN activo que deba purgar después de cada cambio?

## 7. Base de datos

- Motor y versión (MySQL / MariaDB).
- Host, puerto y nombre de la base de datos (sin usuario ni contraseña).
- ¿Está permitido el acceso remoto? Si no, ¿dónde se habilita y se agregan IPs?
- ¿Hay phpMyAdmin disponible?

## 8. API de Hostinger

- ¿Mi cuenta puede generar un token de la API de Hostinger?
- ¿En qué sección del hPanel se genera?
- ¿Qué permisos o alcances tiene ese token?
- ¿Existe un servidor MCP oficial de Hostinger que pueda conectar a un agente
  de IA? Si existe, ¿cómo se configura?

## 9. Respaldos y seguridad (antes de tocar nada)

- ¿Tengo backups automáticos activos? ¿Con qué frecuencia y cuántos se
  conservan?
- ¿Cómo hago un backup manual completo ahora mismo (archivos + base de datos)?
- ¿Cómo restauro si algo sale mal?

Responde punto por punto. Si algo NO está disponible en mi plan, dilo
explícitamente en vez de omitirlo.
