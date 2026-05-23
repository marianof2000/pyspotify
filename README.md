# Spotify / YouTube Downloader

Scripts para descargar discos desde Spotify con `spotdl` y desde YouTube/YouTube Music con `yt-dlp`.

## Requisitos

- Python 3.
- `ffmpeg` instalado y disponible en el sistema.
- Dependencias Python declaradas en `requirements.txt`.
- Para Spotify, el comando `spotdl` debe estar instalado. El codigo actual lo busca en `~/.pyenv/shims/spotdl`.

## Instalacion

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

El punto de entrada principal es `main.py`. Hay que indicar si se quiere usar Spotify o YouTube:

```bash
python3 main.py --sp
python3 main.py --yt
```

Antes de descargar, cada flujo valida sus dependencias principales. Spotify verifica `spotdl`;
YouTube verifica `ffmpeg` y usa `yt-dlp`.

Al finalizar, cada flujo imprime un resumen con links procesados, exitosos, fallidos e ignorados.

## Spotify

El flujo de Spotify lee URLs desde `src/links.txt` por defecto, igual que YouTube.
Si el archivo contiene links mezclados, Spotify solo procesa los links de Spotify.

```text
src/links.txt
```

Cada linea debe contener una URL de Spotify. Ejemplo:

```text
https://open.spotify.com/album/...
https://open.spotify.com/playlist/...
```

Para ejecutar:

```bash
python3 main.py --sp
```

Tambien se puede indicar otro archivo:

```bash
python3 main.py --sp -f lista.txt
```

Las descargas se guardan dentro de:

```text
salida/
  Banda/
    Disco/
      temas.mp3
```

## YouTube / YouTube Music

El flujo de YouTube lee URLs desde `src/links.txt` por defecto.
Si el archivo contiene links mezclados, YouTube solo procesa los links de YouTube.

Ejemplo de `src/links.txt`:

```text
https://music.youtube.com/playlist?list=...
https://www.youtube.com/watch?v=...
```

Para ejecutar con las opciones por defecto:

```bash
python3 main.py --yt
```

Tambien se puede indicar otro archivo, carpeta de salida o bitrate:

```bash
python3 main.py --yt -f links.txt -o salida --kbps 320
```

Opciones utiles:

- `-f`, `--file`: archivo con URLs.
- `-o`, `--outdir`: carpeta base de salida.
- `--kbps`: calidad MP3, entre 64 y 320.
- `--cookies`: archivo de cookies para contenido restringido.
- `--proxy`: proxy HTTP/SOCKS.
- `--rate-limit`: limite de velocidad, por ejemplo `2M`.
- `--no-playlist`: descarga solo el video indicado, no la playlist completa.

El directorio `salida/` esta ignorado por Git, por lo que las descargas no quedan bajo seguimiento.

## Estructura

```text
main.py                 # Selector entre Spotify y YouTube
requirements.txt        # Dependencias directas
src/pyspotify.py        # Entrada actual para Spotify
src/funcionessp.py      # Funciones de Spotify
src/pyyoutube.py        # Entrada actual para YouTube
src/funcionesyt.py      # Funciones de YouTube / yt-dlp
```

## Notas

- Se mantiene una sola entrada de Spotify: `src/pyspotify.py`.
- Algunas rutas estan hardcodeadas para el entorno local. Una mejora pendiente es pasarlas a argumentos de linea de comandos o variables de entorno.
