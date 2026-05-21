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
    """
    Contrato:
        Ejecuta el flujo principal de descargas de Spotify.
    Precondiciones:
        Debe existir el archivo `~/Music/Spotify/discos` con una URL por linea.
        `funcionessp` debe poder encontrar y ejecutar `spotdl`.
    Postcondiciones:
        Delega la descarga de las URLs al modulo `funcionessp`.
        No devuelve valor; los resultados se escriben en el arbol de musica.
    """
    archivo_discos = os.path.join(RAIZ, "discos")
    funcionessp.descargar_discos_desde_archivo(archivo_discos)


if __name__ == "__main__":
    main()
