#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descarga discos con yt-dlp leyendo URLs desde links.txt (mismo directorio):
- Crea una carpeta por disco (playlist o video) dentro de ./salida
- Convierte a MP3 128 kbps
- Numera los temas (playlist_index si hay playlist; si no, autonumber)
- Descarga la carátula (thumbnail), la convierte a JPG y la embebe como album art
- Guarda también el JPG de la carátula junto al MP3

Uso:
    python discos_ytdlp.py
    python discos_ytdlp.py -o ./mi_salida -f mis_links.txt
"""

import argparse
import os
import re
from pathlib import Path
from typing import Iterable, Optional
from yt_dlp import YoutubeDL


DEFAULT_LINKS_FILE = "links.txt"


def read_urls(links_path: Path) -> Iterable[str]:
    """Lee URLs (una por línea), ignorando vacías y comentarios (#...)."""
    if not links_path.exists():
        raise FileNotFoundError(f"No encontré {links_path}")
    for line in links_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        yield line


def slugify(name: str, maxlen: int = 120) -> str:
    """Sanitiza a nombre de carpeta (sin caracteres conflictivos)."""
    # Reemplazos típicos en nombres de rutas
    name = re.sub(r"[\\/:*?\"<>|]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    if len(name) > maxlen:
        name = name[:maxlen].rstrip()
    # Evitar nombres reservados en Windows
    reserved = (
        {"CON", "PRN", "AUX", "NUL"}
        | {f"COM{i}" for i in range(1, 10)}
        | {f"LPT{i}" for i in range(1, 10)}
    )
    if name.upper() in reserved:
        name = f"_{name}_"
    return name or "Desconocido"


def probe_info(url: str) -> dict:
    """Extrae metadata sin descargar para decidir carpeta y plantilla."""
    ydl_opts = {"quiet": True, "skip_download": True}
    with YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


def build_postprocessors():
    """Cadena de postprocesadores para MP3 + cover embebida + metadatos."""
    return [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        },
        {
            "key": "FFmpegThumbnailsConvertor",
            "format": "jpg",
        },
        {
            "key": "EmbedThumbnail",
        },
        {
            "key": "FFmpegMetadata",
        },
    ]


def build_common_opts(outtmpl: str) -> dict:
    """Opciones comunes para YoutubeDL."""
    return {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "postprocessors": build_postprocessors(),
        "writethumbnail": True,
        "addmetadata": True,
        "embedthumbnail": True,
        "ignoreerrors": True,
        "continuedl": True,
        "quiet": False,
        "nocheckcertificate": True,
    }


def download_disc(url: str, base_out: Path) -> Optional[Path]:
    """
    Descarga un “disco” (playlist o video) en su propia subcarpeta.
    Devuelve la carpeta creada, o None si falla la extracción previa.
    """
    try:
        info = probe_info(url)
    except Exception as e:
        print(f"[WARN] No pude extraer metadata de: {url} -> {e}")
        return None

    # Determinar nombre de carpeta
    # Preferimos: playlist_title > album > uploader > title
    # folder_name que sea artista - nombre disco

    folder_name = (
        info.get("playlist_title")
        or info.get("album")
        or info.get("uploader")
        or info.get("title")
        or "Disco"
    )
    folder = base_out / slugify("".join(folder_name.split()))
    folder.mkdir(parents=True, exist_ok=True)

    # Elegir plantilla de numeración:
    # - Si es playlist: usamos playlist_index
    # - Si no: usamos autonumber
    is_playlist = bool(info.get("_type") == "playlist" or info.get("entries"))

    if is_playlist:
        name_tmpl = "%(playlist_index)02d-%(title).200s.%(ext)s"
    else:
        name_tmpl = "%(autonumber)02d-%(title).200s.%(ext)s"

    outtmpl = str(folder / name_tmpl)

    ydl_opts = build_common_opts(outtmpl)
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return folder
    except Exception as e:
        print(f"[ERROR] Falló la descarga de: {url} -> {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Lee URLs desde links.txt y descarga cada disco en su propia carpeta con MP3 128 kbps + carátula."
    )
    parser.add_argument(
        "-f",
        "--file",
        default=DEFAULT_LINKS_FILE,
        help="Archivo de texto con las URLs (por defecto: links.txt en el mismo directorio).",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        default="/home/marianof/Music/Spotify",
        help="Directorio base de salida (por defecto: /home/marianof/Music/Spotify).",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    links_path = (script_dir / args.file).resolve()
    base_out = Path(args.outdir).resolve()
    base_out.mkdir(parents=True, exist_ok=True)

    urls = list(read_urls(links_path))
    if not urls:
        print(f"[INFO] No hay URLs en {links_path}")
        return

    print(f"[INFO] Voy a procesar {len(urls)} URL(s) desde {links_path}")
    for i, url in enumerate(urls, 1):
        print(f"\n[INFO] ({i}/{len(urls)}) Descargando disco: {url}")
        folder = download_disc(url, base_out)
        if folder:
            print(f"[OK] Guardado en: {folder}")
        else:
            print("[WARN] Este disco no se pudo descargar.")


if __name__ == "__main__":
    main()
