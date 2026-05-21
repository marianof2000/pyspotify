#!/usr/bin/env python3

import logging
import os
from src import funcionessp


# Configuración de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

HOME = os.path.expanduser("~")
RAIZ = os.path.join(HOME, "Music/Spotify")


def main():
    """Función principal para iniciar la descarga del álbum."""
    archivo_discos = os.path.join(RAIZ, "discos")
    funcionessp.descargar_discos_desde_archivo(archivo_discos)


if __name__ == "__main__":
    main()
