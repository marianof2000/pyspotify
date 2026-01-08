# Funciones de descarga para YouTube Music

import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Iterable, Optional, Tuple
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


def _normalize_unicode(s: str) -> str:
    """Normaliza a NFC y remueve diacríticos si es conveniente."""
    s = unicodedata.normalize("NFKD", s)
    # Mantén letras y espacios, quita diacríticos combinados
    return "".join(c for c in s if not unicodedata.combining(c))


def _slugify(name: str, maxlen: int = 120) -> str:
    """Sanitiza a nombre de carpeta (sin caracteres conflictivos, preservando espacios)."""
    if not name:
        return "Desconocido"
    name = _normalize_unicode(name)
    # Remplazo de caracteres problemáticos en rutas
    name = re.sub(r'[\\/:*?"<>|]', " ", name)
    # Compactar espacios
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


def _probe_info(url: str) -> dict:
    """Extrae metadata sin descargar para decidir carpeta y plantilla."""
    ydl_opts = {"quiet": True, "skip_download": True}
    with YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


def _build_postprocessors(kbps: int):
    """Cadena de postprocesadores para MP3 + cover embebida + metadatos."""
    return [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": str(kbps),
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


def _build_common_opts(
    outtmpl: str,
    kbps: int,
    cookies: Optional[str],
    proxy: Optional[str],
    rate_limit: Optional[str],
    no_playlist: bool,
) -> dict:
    """Opciones comunes para YoutubeDL."""
    opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "postprocessors": _build_postprocessors(kbps),
        "writethumbnail": True,
        "addmetadata": True,
        "embedthumbnail": True,
        "ignoreerrors": True,
        "continuedl": True,
        "quiet": False,
        "nocheckcertificate": True,
        "no_warnings": True,
        # Robustez:
        "retries": 10,
        "fragment_retries": 10,
    }
    if cookies:
        opts["cookiefile"] = cookies
    if proxy:
        opts["proxy"] = proxy
    if rate_limit:
        opts["ratelimit"] = rate_limit
    if no_playlist:
        opts["noplaylist"] = True
    return opts


def _compose_folder_name(info_dict):
    album_title = (
        info_dict.get("playlist_title") or info_dict.get("title") or "Unknown Album"
    )

    artist_name = None
    entries = info_dict.get("entries")
    if entries and isinstance(entries, list) and len(entries) > 0:
        first_entry = entries[0]
        artist_name = first_entry.get("artist")
        if not artist_name:
            artists_list = first_entry.get("artists")
            if (
                artists_list
                and isinstance(artists_list, list)
                and len(artists_list) > 0
            ):
                artist_name = artists_list[0]

    if not artist_name:
        artist_name = info_dict.get("artist")
        if not artist_name:
            artists_list = info_dict.get("artists")
            if (
                artists_list
                and isinstance(artists_list, list)
                and len(artists_list) > 0
            ):
                artist_name = artists_list[0]

    if not artist_name:
        artist_name = "Unknown Artist"

    folder_name = f"{artist_name} - {album_title}".strip().replace("Album", "")
    folder_name = "".join(folder_name.split())
    is_playlist = bool(info_dict.get("_type") == "playlist" or info_dict.get("entries"))
    return folder_name, is_playlist


def _rename_thumbnails_to_cover(folder: Path):
    """
    Renombra thumbnails .jpg resultantes a cover.jpg junto a cada mp3.
    yt-dlp genera un .jpg por cada base de archivo; buscamos parear.
    """
    for jpg in folder.glob("*.jpg"):
        # Busca un .mp3 con mismo stem
        stem = jpg.stem
        mp3 = folder / f"{stem}.mp3"
        if mp3.exists():
            cover = folder / f"{stem}.cover.jpg"
            try:
                jpg.rename(cover)
            except Exception:
                # Si ya existe, no romper el flujo
                pass


def download_disc(
    url: str,
    base_out: Path,
    kbps: int,
    cookies: Optional[str],
    proxy: Optional[str],
    rate_limit: Optional[str],
    no_playlist: bool,
) -> Optional[Path]:
    """
    Descarga un “disco” (playlist o video) en su propia subcarpeta.
    Devuelve la carpeta creada, o None si falla la extracción previa.
    """
    try:
        info = _probe_info(url)
    except Exception as e:
        print(f"[WARN] No pude extraer metadata de: {url} -> {e}")
        return None

    folder_name, is_playlist = _compose_folder_name(info)
    folder = base_out / _slugify(folder_name)
    folder.mkdir(parents=True, exist_ok=True)

    # Elegir plantilla de numeración:
    # - Si es playlist: usamos playlist_index
    # - Si no: usamos autonumber
    if is_playlist:
        name_tmpl = "%(playlist_index)02d-%(title).200s.%(ext)s"
    else:
        name_tmpl = "%(autonumber)02d-%(title).200s.%(ext)s"

    outtmpl = str(folder / name_tmpl)

    ydl_opts = _build_common_opts(
        outtmpl, kbps, cookies, proxy, rate_limit, no_playlist
    )

    def _progress_hook(d):
        if d.get("status") == "downloading":
            eta = d.get("eta")
            speed = d.get("speed")
            print(
                f"[DL] {d.get('filename','')} - {d.get('downloaded_bytes',0)} bytes "
                f"{'(eta: '+str(eta)+'s)' if eta else ''} "
                f"{'(speed: '+str(speed)+' B/s)' if speed else ''}"
            )
        elif d.get("status") == "finished":
            print(f"[OK] Descargado: {d.get('filename','')}")

    ydl_opts["progress_hooks"] = [_progress_hook]

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        # Renombrar thumbnails a cover.jpg (por pista)
        _rename_thumbnails_to_cover(folder)
        return folder
    except Exception as e:
        print(f"[ERROR] Falló la descarga de: {url} -> {e}")
        return None


if __name__ == "__main__":
    print("Funciones cargadas")
