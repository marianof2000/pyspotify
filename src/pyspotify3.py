#!/usr/bin/env python3

import json
import os
import logging
from src import funcionessp


# Configuración de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

HOME = os.path.expanduser("~")
RAIZ = os.path.join(HOME, "Music/Spotify")
SPOTDL_PROGRAM = os.path.join(HOME, ".pyenv/shims/spotdl")


def main():
    """Función principal para iniciar la descarga del álbum."""
    solo_renombrar = False
    if solo_renombrar:
        # a desarrollar
        functions.procesar_playlist_y_renombrar(album_dir)
    else:
        archivo_discos = os.path.join(RAIZ, "discos")
        #print(archivo_discos)
        functions.descargar_discos_desde_archivo(archivo_discos)
    # limpiar_archivos_m3u()


if __name__ == "__main__":
    main()
