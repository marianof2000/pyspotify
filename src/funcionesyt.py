# Funciones de descarga para YouTube Music

import re
import time
import unicodedata
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urlparse
from yt_dlp import YoutubeDL


def _read_urls(links_path: Path) -> Iterable[str]:
    """
    Contrato:
        Lee URLs desde un archivo de texto.
    Precondiciones:
        `links_path` debe apuntar a un archivo existente y legible en UTF-8.
    Postcondiciones:
        Genera una URL por cada linea no vacia que no comience con `#`.
        Lanza `FileNotFoundError` si el archivo no existe.
    """
    if not links_path.exists():
        raise FileNotFoundError(f"No encontré {links_path}")
    for line in links_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        yield line


def _is_youtube_url(url: str) -> bool:
    """
    Contrato:
        Determina si una cadena representa un enlace de YouTube o YouTube Music.
    Precondiciones:
        `url` debe ser una cadena ya normalizada con `strip`.
    Postcondiciones:
        Devuelve True para dominios `youtube.com`, subdominios y `youtu.be`.
    """
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    return host == "youtu.be" or host == "youtube.com" or host.endswith(".youtube.com")


def _read_youtube_urls(links_path: Path) -> Iterable[str]:
    """
    Contrato:
        Lee solo URLs de YouTube desde un archivo de texto compartido.
    Precondiciones:
        `links_path` debe apuntar a un archivo existente y legible en UTF-8.
    Postcondiciones:
        Genera una URL por cada linea que corresponda a YouTube.
    """
    for url in _read_urls(links_path):
        if _is_youtube_url(url):
            yield url


def _normalize_unicode(s: str) -> str:
    """
    Contrato:
        Normaliza una cadena y remueve marcas diacriticas combinadas.
    Precondiciones:
        `s` debe ser una cadena de texto.
    Postcondiciones:
        Devuelve una cadena normalizada en forma NFKD sin diacriticos combinados.
        No modifica la cadena original.
    """
    s = unicodedata.normalize("NFKD", s)
    # Mantén letras y espacios, quita diacríticos combinados
    return "".join(c for c in s if not unicodedata.combining(c))


def _slugify(name: str, maxlen: int = 120) -> str:
    """
    Contrato:
        Convierte un texto en un nombre seguro para carpeta.
    Precondiciones:
        `name` debe ser una cadena o un valor falsy aceptable.
        `maxlen` debe ser un entero positivo.
    Postcondiciones:
        Devuelve un nombre sin caracteres conflictivos de rutas.
        Compacta espacios, limita la longitud y evita nombres reservados comunes.
    """
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
    """
    Contrato:
        Extrae metadata de una URL sin descargar el contenido.
    Precondiciones:
        `url` debe ser una URL aceptada por `yt-dlp`.
        Debe haber conectividad y soporte del extractor correspondiente.
    Postcondiciones:
        Devuelve el diccionario de metadata entregado por `yt-dlp`.
        Puede propagar excepciones de `YoutubeDL.extract_info`.
    """
    ydl_opts = {"quiet": True, "skip_download": True}
    with YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


def _build_postprocessors(kbps: int):
    """
    Contrato:
        Construye la cadena de postprocesadores de `yt-dlp`.
    Precondiciones:
        `kbps` debe representar una calidad MP3 valida para FFmpeg.
        `ffmpeg` debe estar disponible cuando los postprocesadores se ejecuten.
    Postcondiciones:
        Devuelve una lista de configuraciones para convertir a MP3, convertir
        miniaturas, embeber portada y escribir metadata.
    """
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
    no_warnings: bool,
    no_playlist: bool,
) -> dict:
    """
    Contrato:
        Construye las opciones comunes para una descarga con `YoutubeDL`.
    Precondiciones:
        `outtmpl` debe ser una plantilla de salida valida para `yt-dlp`.
        `kbps` debe ser una calidad aceptada por el postprocesador de audio.
        Si se informan `cookies`, `proxy` o `rate_limit`, deben ser valores validos.
    Postcondiciones:
        Devuelve un diccionario de opciones listo para instanciar `YoutubeDL`.
        Incluye opciones condicionales solo cuando sus argumentos fueron provistos.
    """
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
        "no_warnings": no_warnings,
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
    """
    Contrato:
        Deriva el nombre de carpeta y si el recurso representa una playlist.
    Precondiciones:
        `info_dict` debe ser un diccionario de metadata compatible con `yt-dlp`.
    Postcondiciones:
        Devuelve una tupla `(folder_name, is_playlist)`.
        Usa valores por defecto cuando no encuentra artista o album.
    """
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

    folder_name = f"{artist_name} {album_title}".strip().replace("Album", "")
    folder_name = "".join(folder_name.split())
    is_playlist = bool(info_dict.get("_type") == "playlist" or info_dict.get("entries"))
    return folder_name, is_playlist


def _rename_thumbnails_to_cover(folder: Path):
    """
    Contrato:
        Renombra miniaturas JPG generadas por `yt-dlp` junto a sus MP3.
    Precondiciones:
        `folder` debe ser un directorio existente.
        Las miniaturas y MP3 deben compartir el mismo stem para poder parearse.
    Postcondiciones:
        Para cada JPG con MP3 equivalente, intenta renombrarlo a `*.cover.jpg`.
        Ignora errores individuales de renombrado para no cortar el flujo.
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


def _has_recent_mp3_files(folder: Path, started_at: float, known_files: set[Path]) -> bool:
    """
    Contrato:
        Determina si una descarga produjo o actualizo archivos MP3.
    Precondiciones:
        `folder` debe ser una ruta de directorio existente o esperada.
        `started_at` debe ser el timestamp tomado antes de iniciar la descarga.
        `known_files` debe contener los MP3 existentes antes de iniciar la descarga.
    Postcondiciones:
        Devuelve True si hay al menos un MP3 nuevo o modificado durante la descarga.
    """
    current_files = {path for path in folder.glob("*.mp3") if path.is_file()}
    new_files = current_files - known_files
    if new_files:
        return True
    return any(path.stat().st_mtime >= started_at for path in current_files)


def _download_disc(
    url: str,
    base_out: Path,
    kbps: int,
    cookies: Optional[str],
    proxy: Optional[str],
    rate_limit: Optional[str],
    no_warnings: bool,
    no_playlist: bool,
) -> Optional[Path]:
    """
    Contrato:
        Descarga una playlist o video en una subcarpeta propia y lo convierte a MP3.
    Precondiciones:
        `url` debe ser aceptada por `yt-dlp`.
        `base_out` debe existir o poder crearse antes de llamar esta funcion.
        `kbps` debe pertenecer al conjunto de calidades admitidas por la CLI.
        Si se informan `cookies`, `proxy` o `rate_limit`, deben ser validos.
    Postcondiciones:
        Devuelve la carpeta de salida si queda al menos un MP3 nuevo o actualizado.
        Devuelve `None` si falla la extraccion previa, la descarga o no se genera audio.
        Intenta renombrar miniaturas JPG a `*.cover.jpg` al finalizar.
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
        outtmpl, kbps, cookies, proxy, rate_limit, no_warnings, no_playlist
    )

    def _progress_hook(d):
        """
        Contrato:
            Reporta por consola eventos de progreso enviados por `yt-dlp`.
        Precondiciones:
            `d` debe ser un diccionario de estado provisto por `yt-dlp`.
        Postcondiciones:
            Imprime informacion de descarga o finalizacion cuando el estado aplica.
            No devuelve valor ni altera el estado de descarga.
        """
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
        known_mp3_files = {path for path in folder.glob("*.mp3") if path.is_file()}
        started_at = time.time()
        with YoutubeDL(ydl_opts) as ydl:
            result_code = ydl.download([url])
        if result_code not in (0, None):
            print(f"[WARN] yt-dlp terminó con código {result_code} para: {url}")
            return None
        # Renombrar thumbnails a cover.jpg (por pista)
        _rename_thumbnails_to_cover(folder)
        if not _has_recent_mp3_files(folder, started_at, known_mp3_files):
            print(f"[WARN] No se generó ningún MP3 en: {folder}")
            return None
        return folder
    except Exception as e:
        print(f"[ERROR] Falló la descarga de: {url} -> {e}")
        return None


if __name__ == "__main__":
    print("Funciones cargadas")
