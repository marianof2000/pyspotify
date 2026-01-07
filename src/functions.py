# funciones

import logging
import json
from typing import List
import os
import subprocess

HOME = os.path.expanduser("~")
RAIZ = os.path.join(HOME, "Music/Spotify")
SPOTDL_PROGRAM = os.path.join(HOME, ".pyenv/shims/spotdl")

def _run_spotdl_command(command: List[str]):
    """Ejecuta un comando spotdl y captura la salida."""
    try:
        logging.info(f"Ejecutando spotdl con el comando: {command}")
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al ejecutar spotdl: {e}")
        raise


def _get_album_info(url: str) -> dict:
    """Obtiene información del álbum usando spotdl."""
    output_file = os.path.join(RAIZ, "datos.spotdl")
    try:
        _run_spotdl_command([SPOTDL_PROGRAM, "save", url, "--save-file", output_file])
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
    """Renombra los mp3 en album_dir según el contenido de la playlist m3u."""
    with open(playlist_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    for idx, line in enumerate(lines):
        if line.startswith("#EXTINF"):
            # Extrae el título después de la coma
            parts = line.split(",", 1)
            if len(parts) != 2:
                continue
            track_name = parts[1].strip()
            # La siguiente línea es la ruta al archivo MP3
            if idx + 1 < len(lines):
                file_rel = lines[idx + 1]
                logging.info(f"Renombrando {file_rel[2:]} → {file_rel}")
                file_name = os.path.basename(file_rel[2:].replace(" ", "_"))
                old_path = os.path.join(album_dir, file_name)
                if not os.path.exists(old_path):
                    logging.warning(f"No se encontró el archivo de audio: {old_path}")
                    continue
                # Sanitizar nombre de archivo
                safe_name = re.sub(r'[\\\/:*?"<>|]', "_", file_rel)
                new_file_name = f"{safe_name}"
                new_path = os.path.join(album_dir, new_file_name)
                try:
                    os.rename(old_path, new_path)
                    logging.info(f"Renombrado {old_path} → {new_path}")
                except Exception as e:
                    logging.error(f"Error al renombrar {old_path}: {e}")


def procesar_playlist_y_renombrar(album_dir: str):
    """Busca playlists (.m3u/.m3u8) en album_dir, renombra mp3 y elimina la playlist."""
    for item in os.listdir(album_dir):
        if item.endswith((".m3u", ".m3u8")):
            playlist_path = os.path.join(album_dir, item)
            try:
                rename_mp3_from_playlist(album_dir, playlist_path)
            finally:
                # os.remove(playlist_path)
                logging.info(f"Eliminada playlist: {playlist_path}")


def _download_album(url: str):
    """Descarga un álbum de Spotify y renombra los MP3 según la playlist."""
    try:
        album_info = _get_album_info(url)
        artist = album_info["album_artist"].replace(" ", "")
        album = album_info["album_name"].replace(" ", "_")
        album_dir = os.path.join(RAIZ, artist, album)
        print(album_dir)

        os.makedirs(album_dir, exist_ok=True)
        logging.info(f"Directorio creado: {album_dir}")

        os.chdir(album_dir)
        _run_spotdl_command([SPOTDL_PROGRAM, "download", url, "--threads", "2"])
        logging.info("Descarga completada")
        time.sleep(5)  # Espera a que terminen de generarse los archivos

        # *** NUEVO: procesar playlist y renombrar los mp3 ***
        procesar_playlist_y_renombrar(album_dir)

    except Exception as e:
        logging.error(f"Error al descargar el álbum: {e}")
    finally:
        os.chdir(RAIZ)


def descargar_discos_desde_archivo(archivo_discos: str):
    """Descarga álbumes desde una lista de URLs en un archivo."""
    try:
        with open(archivo_discos, "r", encoding="utf-8") as f:
            for disco_url in f:
                _download_album(disco_url.strip())
                time.sleep(5)
    except FileNotFoundError:
        logging.error(f"No se encontró el archivo: {archivo_discos}")
    except Exception as e:
        logging.error(f"Error al procesar el archivo: {e}")


def _limpiar_archivos_m3u():
    """Elimina todos los archivos .m3u y .m3u8 del directorio raíz."""
    try:
        for item in os.listdir(RAIZ):
            if item.endswith((".m3u", ".m3u8")):
                os.remove(os.path.join(RAIZ, item))
    except OSError as e:
        logging.error(f"Error al eliminar archivos m3u en RAIZ: {e}")
        raise


if __name__ == "__main__":
    print("Funciones cargadas")
