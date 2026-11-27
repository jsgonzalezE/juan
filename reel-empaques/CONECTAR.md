# Cómo conectarse (para ChatGPT / Codex)

Todo está preparado. La rama `codex/noah` ya existe en `jsgonzalezE/juan` con las carpetas listas.
Solo hay que bajarla, poner los cuadros y publicarla.

## La primera vez

```bash
git clone https://github.com/jsgonzalezE/juan.git
cd juan
git checkout codex/noah
```

Si la carpeta ya estaba clonada:

```bash
git fetch origin codex/noah
git checkout codex/noah
```

## Cada vez que haya algo nuevo

1. Copiar los cuadros a `reel-empaques/noah_anim/<animacion>/`.
2. Escribir la nota arriba en `reel-empaques/noah_anim/NOTAS.md`.
3. Publicar:

```bash
git add reel-empaques/noah_anim
git commit -m "Noah: caminar y contento, prueba 01"
git push origin codex/noah
```

4. Avisarle al cliente que ya se publicó. Claude no recibe aviso: el cliente le dice "revisa".

## Leer lo que deja Claude

```bash
git fetch origin claude/sharp-pasteur-xeb10s
git show origin/claude/sharp-pasteur-xeb10s:reel-empaques/NOTAS_PARA_NOAH.md
git show origin/claude/sharp-pasteur-xeb10s:reel-empaques/ENCARGO_ANIMACIONES_NOAH.md
```

## Reglas

- Escribir solo dentro de `reel-empaques/noah_anim/` y solo en la rama `codex/noah`.
- No tocar la rama `claude/sharp-pasteur-xeb10s`.
- El repositorio es público mientras el cliente no lo cambie: no subir imágenes de los empaques.
- Si `git push` pide iniciar sesión, es la ventana de GitHub en el computador del cliente: él debe
  autorizarla una vez.
- Si GitHub no funciona, el plan B es un zip con la misma estructura de carpetas, que el cliente
  adjunta en el chat de Claude.
