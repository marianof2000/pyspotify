#!/usr/bin/env python3

import logging
import argparse
from pathlib import Path
from src import funcionessp


# Configuración de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

DEFAULT_LINKS_FILE = "links.txt"


def main():
    """
    Contrato:
        Ejecuta el flujo principal de descargas de Spotify.
    Precondiciones:
        Debe existir el archivo de enlaces indicado por CLI, por defecto
        `links.txt` en el mismo directorio que este modulo.
        `funcionessp` debe poder encontrar y ejecutar `spotdl`.
    Postcondiciones:
        Delega la descarga de las URLs al modulo `funcionessp`.
        No devuelve valor; los resultados se escriben en el arbol de musica.
    """
    parser = argparse.ArgumentParser(
        description="Lee URLs de Spotify desde links.txt y descarga cada disco con spotdl."
    )
    parser.add_argument(
        "-f",
        "--file",
        default=DEFAULT_LINKS_FILE,
        help="Archivo de texto con las URLs (por defecto: links.txt en el mismo directorio).",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    links_path = (script_dir / args.file).resolve()
    funcionessp.descargar_discos_desde_archivo(str(links_path))


if __name__ == "__main__":
    main()
