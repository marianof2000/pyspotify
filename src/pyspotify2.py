#!/usr/bin/env python3

import json
import logging
import os
import subprocess
import time
from typing import List


# Configuración de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

HOME = os.path.expanduser("~")
RAIZ = os.path.join(HOME, "Music/Spotify")
SPOTDL_PROGRAM = os.path.join(HOME, ".pyenv/shims/spotdl")


def run_spotdl_command(command: List[str]):
    """Ejecuta un comando spotdl y captura la salida."""
    try:
        logging.info(f"Ejecutando spotdl con el comando: {command}")
        subprocess.run(command, check=True)  # Lanza una excepción si falla el comando
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al ejecutar spotdl: {e}")
        raise


def get_album_info(url: str) -> dict:
    """Obtiene información del álbum usando spotdl."""
    output_file = os.path.join(RAIZ, "datos.spotdl")
    try:
        run_spotdl_command([SPOTDL_PROGRAM, "save", url, "--save-file", output_file])
        time.sleep(30)  # Espera a que spotdl escriba el archivo
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
            logging.info("No se encontró el archivo temporal")


def download_album(url: str):
    """Descarga un álbum de Spotify."""
    try:
        album_info = get_album_info(url)
        artist = album_info["album_artist"].replace(" ", "")
        album = album_info["album_name"].replace(" ", "_")
        album_dir = os.path.join(RAIZ, artist, album)

        try:
            os.makedirs(album_dir, exist_ok=True)  # Crea el directorio si no existe
            logging.info(f"Directorio creado: {album_dir}")
        except OSError as e:
            logging.error(f"Error al crear el directorio: {e}")
            return

        os.chdir(album_dir)
        run_spotdl_command([SPOTDL_PROGRAM, "download", url, "--threads", "1"])
        logging.info("Descarga completada")
        time.sleep(120)  # Espera a que se complete la descarga

    except Exception as e:
        logging.error(f"Error al descargar el álbum: {e}")
    finally:
        os.chdir(RAIZ)
        limpiar_archivos_m3u()


def descargar_discos_desde_archivo(archivo_discos: str):
    """Descarga álbumes desde una lista de URLs en un archivo."""
    try:
        with open(archivo_discos, "r", encoding="utf-8") as f:
            for disco_url in f:
                download_album(disco_url.strip())
                time.sleep(10)  # Espera entre descargas
    except FileNotFoundError:
        logging.error(f"No se encontró el archivo: {archivo_discos}")
        return
    except Exception as e:
        logging.error(f"Error al procesar el archivo: {e}")
        return


def limpiar_archivos_m3u():
    """Elimina todos los archivos .m3u y .m3u8 del directorio raíz."""
    try:
        for item in os.listdir(RAIZ):
            if item.endswith((".m3u", ".m3u8")):
                file_path = os.path.join(RAIZ, item)
                os.remove(file_path)
                logging.info(f"Archivo eliminado: {file_path}")
    except OSError as e:
        logging.error(f"Error al eliminar archivos m3u: {e}")


def main():
    """Función principal para iniciar la descarga del álbum."""
    archivo_discos = os.path.join(RAIZ, "discos")
    descargar_discos_desde_archivo(archivo_discos)
    limpiar_archivos_m3u()


if __name__ == "__main__":
    main()
