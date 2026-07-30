# Conexión al hosting

Documentación para conectar un agente de desarrollo remoto al sitio alojado en
Hostinger.

## Archivos

- `prompt-hostinger.md` — prompt listo para pegar en el asistente de IA de
  Hostinger (Kodee).

## Reglas de seguridad de este repo

**Nunca commitees credenciales aquí.** Ni en un repo privado.

Un repo de Git no es un gestor de secretos:

- El historial es permanente. Borrar el archivo en un commit posterior no borra
  el secreto: sigue accesible en el historial para siempre.
- Cada clon se lleva una copia completa del historial.
- Basta cambiar la visibilidad a público, o dar acceso a un colaborador, para
  filtrar todo de golpe.

### Sí se puede guardar aquí

Información técnica no sensible: tipo de plan, versiones de PHP/Node, servidor
web, rutas del document root, nombre de la base de datos, qué funciones están
disponibles en el plan, procedimiento de backup.

### No se guarda aquí, nunca

Contraseñas de FTP/SSH/base de datos, llaves privadas SSH, tokens de la API de
Hostinger, contraseñas de aplicación de WordPress, cualquier cosa que sirva
para autenticarse.

Esas se pasan por un canal aparte, en el momento en que se necesitan, y se
rotan cuando el trabajo termina.

## Orden de preferencia para conectarse

1. **Git desde el hPanel.** El más robusto. El código vive en GitHub, Hostinger
   lo despliega. No requiere abrir accesos de red hacia el servidor ni compartir
   credenciales de shell.
2. **SSH con llave pública.** Buena opción si el plan lo incluye. Requiere que
   el entorno del agente pueda salir por el puerto SSH, lo cual no siempre está
   permitido.
3. **FTP/SFTP.** Último recurso. FTP plano transmite credenciales sin cifrar;
   si se usa, que sea SFTP o FTPS.

## Antes de cualquier cambio

Hacer un backup manual completo (archivos + base de datos) y confirmar que se
sabe cómo restaurarlo.
