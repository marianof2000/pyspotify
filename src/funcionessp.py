# funciones

import logging
import json
from typing import List
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from urllib.parse import urlparse

HOME = os.path.expanduser("~")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAIZ = str(PROJECT_ROOT / "salida")
SPOTDL_PROGRAM = os.path.join(HOME, ".pyenv/shims/spotdl")


def _is_spotify_url(url: str) -> bool:
    """
    Contrato:
        Determina si una cadena representa un enlace de Spotify.
    Precondiciones:
        `url` debe ser una cadena ya normalizada con `strip`.
    Postcondiciones:
        Devuelve True para URLs web de Spotify o URIs `spotify:`.
    """
    if url.startswith("spotify:"):
        return True
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    return host == "open.spotify.com" or host.endswith(".spotify.com")


def _safe_dir_name(name: str, fallback: str = "Desconocido") -> str:
    """
    Contrato:
        Convierte texto de metadata en un nombre seguro para directorio.
    Precondiciones:
        `name` puede ser una cadena vacia o valor falsy.
    Postcondiciones:
        Devuelve un nombre sin separadores ni caracteres invalidos de rutas.
    """
    if not name:
        return fallback
    name = re.sub(r'[\\/:*?"<>|]', " ", str(name))
    name = re.sub(r"\s+", " ", name).strip()
    return name or fallback


def _safe_file_name(name: str, fallback: str = "tema.mp3") -> str:
    """
    Contrato:
        Convierte texto de playlist en un nombre seguro para archivo.
    Precondiciones:
        `name` puede ser una cadena vacia o valor falsy.
    Postcondiciones:
        Devuelve un nombre sin separadores ni caracteres invalidos de rutas.
    """
    if not name:
        return fallback
    name = re.sub(r'[\\/:*?"<>|]', "_", str(name))
    name = re.sub(r"\s+", " ", name).strip()
    return name or fallback


def _check_dependencies() -> bool:
    """
    Contrato:
        Verifica que las dependencias externas de Spotify esten disponibles.
    Precondiciones:
        `SPOTDL_PROGRAM` puede apuntar a un ejecutable local o estar ausente.
    Postcondiciones:
        Devuelve True si `spotdl` puede ejecutarse; False en caso contrario.
    """
    if os.path.isfile(SPOTDL_PROGRAM) and os.access(SPOTDL_PROGRAM, os.X_OK):
        return True
    if shutil.which("spotdl"):
        return True
    logging.error(f"No se encontró spotdl ejecutable en {SPOTDL_PROGRAM} ni en PATH")
    return False


def _spotdl_program() -> str:
    """
    Contrato:
        Resuelve el ejecutable de `spotdl` a utilizar.
    Precondiciones:
        `_check_dependencies` deberia haber validado disponibilidad previamente.
    Postcondiciones:
        Devuelve la ruta hardcodeada si existe o el ejecutable encontrado en PATH.
    """
    if os.path.isfile(SPOTDL_PROGRAM) and os.access(SPOTDL_PROGRAM, os.X_OK):
        return SPOTDL_PROGRAM
    return shutil.which("spotdl") or SPOTDL_PROGRAM


def _run_spotdl_command(command: List[str]):
    """
    Contrato:
        Ejecuta un comando externo asociado a `spotdl`.
    Precondiciones:
        `command` debe ser una lista no vacia con el ejecutable en la primera posicion.
        El ejecutable indicado debe existir y tener permisos de ejecucion.
    Postcondiciones:
        Si el comando termina correctamente, la funcion finaliza sin devolver valor.
        Si el comando falla, registra el error y relanza `CalledProcessError`.
    """
    try:
        logging.info(f"Ejecutando spotdl con el comando: {command}")
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al ejecutar spotdl: {e}")
        raise


def _get_album_info(url: str) -> dict:
    """
    Contrato:
        Obtiene metadata del album o playlist de Spotify usando `spotdl save`.
    Precondiciones:
        `url` debe ser una URL aceptada por `spotdl`.
        `RAIZ` debe poder crearse para escribir el archivo temporal `datos.spotdl`.
    Postcondiciones:
        Devuelve el primer objeto de metadata del archivo generado por `spotdl`.
        Intenta eliminar el archivo temporal antes de finalizar.
        Si la metadata no puede leerse, registra el error y relanza la excepcion.
    """
    output_file = os.path.join(RAIZ, "datos.spotdl")
    try:
        os.makedirs(RAIZ, exist_ok=True)
        _run_spotdl_command([_spotdl_program(), "save", url, "--save-file", output_file])
        time.sleep(5)
        with open(output_file, "r", encoding="utf-8") as f:
            return json.load(f)[0]
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        json.JSONDecodeError,
    ) as e:
        logging.error(f"Error al obtener información del álbum: {e}")
        raise
    finally:
        try:
            os.remove(output_file)
            logging.info("Archivo temporal eliminado")
        except FileNotFoundError:
            pass


def _rename_mp3_from_playlist(album_dir: str, playlist_path: str):
    """
    Contrato:
        Renombra archivos MP3 dentro de `album_dir` usando las entradas de una playlist.
    Precondiciones:
        `album_dir` debe ser un directorio existente.
        `playlist_path` debe apuntar a un archivo `.m3u` o `.m3u8` legible.
        La playlist debe contener entradas `#EXTINF` seguidas por rutas de audio.
    Postcondiciones:
        Para cada pista encontrada, intenta renombrar el archivo correspondiente.
        Registra advertencias si no encuentra el archivo esperado.
        No devuelve valor.
    """
    album_path = Path(album_dir)
    with open(playlist_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    for idx, line in enumerate(lines):
        if line.startswith("#EXTINF"):
            if idx + 1 < len(lines):
                file_rel = lines[idx + 1]
                file_name = Path(file_rel).name
                if not file_name:
                    continue
                candidates = [
                    album_path / file_name,
                    album_path / file_name.replace(" ", "_"),
                ]
                old_path = next((path for path in candidates if path.exists()), None)
                if old_path is None:
                    logging.warning(f"No se encontró el archivo de audio listado: {file_rel}")
                    continue
                new_path = album_path / _safe_file_name(file_name)
                if old_path == new_path:
                    continue
                try:
                    old_path.rename(new_path)
                    logging.info(f"Renombrado {old_path} → {new_path}")
                except Exception as e:
                    logging.error(f"Error al renombrar {old_path}: {e}")


def _procesar_playlist_y_renombrar(album_dir: str):
    """
    Contrato:
        Busca playlists dentro de un directorio de album y procesa sus renombres.
    Precondiciones:
        `album_dir` debe ser un directorio existente y legible.
    Postcondiciones:
        Ejecuta el renombrado para cada archivo `.m3u` o `.m3u8` encontrado.
        Registra el procesamiento de cada playlist.
        No devuelve valor.
    """
    for item in os.listdir(album_dir):
        if item.endswith((".m3u", ".m3u8")):
            playlist_path = os.path.join(album_dir, item)
            try:
                _rename_mp3_from_playlist(album_dir, playlist_path)
            finally:
                logging.info(f"Playlist procesada: {playlist_path}")


def _download_album(url: str) -> bool:
    """
    Contrato:
        Descarga un album o playlist de Spotify y procesa sus archivos resultantes.
    Precondiciones:
        `url` debe ser una URL aceptada por `spotdl`.
        `RAIZ` debe existir o poder crearse para crear directorios de artista y album.
        El comando `spotdl` configurado debe estar disponible.
    Postcondiciones:
        Crea el directorio de destino si no existe.
        Ejecuta la descarga con `spotdl`.
        Intenta procesar playlists generadas para renombrar MP3.
        Restaura el directorio de trabajo a `RAIZ` al finalizar.
        Devuelve True si el flujo del album finaliza sin excepciones.
    """
    try:
        album_info = _get_album_info(url)
        artist = _safe_dir_name(album_info.get("album_artist"), "Artista desconocido")
        album = _safe_dir_name(album_info.get("album_name"), "Disco desconocido")
        album_dir = os.path.join(RAIZ, artist, album)
        print(album_dir)

        os.makedirs(album_dir, exist_ok=True)
        logging.info(f"Directorio creado: {album_dir}")

        os.chdir(album_dir)
        _run_spotdl_command([_spotdl_program(), "download", url, "--threads", "2"])
        logging.info("Descarga completada")
        time.sleep(5)  # Espera a que terminen de generarse los archivos

        # *** NUEVO: procesar playlist y renombrar los mp3 ***
        _procesar_playlist_y_renombrar(album_dir)
        return True

    except Exception as e:
        logging.error(f"Error al descargar el álbum: {e}")
        return False
    finally:
        os.chdir(RAIZ)


def _descargar_discos_desde_archivo(archivo_discos: str) -> dict:
    """
    Contrato:
        Descarga secuencialmente discos de Spotify listados en un archivo.
    Precondiciones:
        `archivo_discos` debe apuntar a un archivo de texto legible.
        Cada linea no vacia puede contener una URL; solo se procesan las de Spotify.
    Postcondiciones:
        Intenta descargar cada URL de Spotify del archivo en orden.
        Registra errores de archivo inexistente o fallos generales.
        Devuelve un resumen con totales de links procesados, exitosos, fallidos e ignorados.
    """
    resumen = {"procesados": 0, "ok": 0, "fallidos": 0, "ignorados": 0}
    try:
        spotify_urls = []
        with open(archivo_discos, "r", encoding="utf-8") as f:
            for disco_url in f:
                disco_url = disco_url.strip()
                if not disco_url or disco_url.startswith("#"):
                    continue
                if not _is_spotify_url(disco_url):
                    resumen["ignorados"] += 1
                    logging.info(f"Link ignorado por no ser de Spotify: {disco_url}")
                    continue
                spotify_urls.append(disco_url)
        if spotify_urls and not _check_dependencies():
            resumen["fallidos"] = len(spotify_urls)
            resumen["procesados"] = len(spotify_urls)
            return resumen
        for disco_url in spotify_urls:
            resumen["procesados"] += 1
            if not _download_album(disco_url):
                resumen["fallidos"] += 1
            else:
                resumen["ok"] += 1
                time.sleep(5)
        return resumen
    except FileNotFoundError:
        logging.error(f"No se encontró el archivo: {archivo_discos}")
        resumen["fallidos"] += 1
        return resumen
    except Exception as e:
        logging.error(f"Error al procesar el archivo: {e}")
        resumen["fallidos"] += 1
        return resumen


def _limpiar_archivos_m3u():
    """
    Contrato:
        Elimina playlists `.m3u` y `.m3u8` ubicadas directamente en `RAIZ`.
    Precondiciones:
        `RAIZ` debe existir y ser un directorio legible.
        El proceso debe tener permisos para eliminar los archivos encontrados.
    Postcondiciones:
        Borra los archivos `.m3u` y `.m3u8` encontrados en `RAIZ`.
        Si ocurre un error de sistema, lo registra y relanza.
    """
    try:
        for item in os.listdir(RAIZ):
            if item.endswith((".m3u", ".m3u8")):
                os.remove(os.path.join(RAIZ, item))
    except OSError as e:
        logging.error(f"Error al eliminar archivos m3u en RAIZ: {e}")
        raise


if __name__ == "__main__":
    print("Funciones cargadas")
