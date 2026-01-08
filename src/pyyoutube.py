
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descarga discos con yt-dlp leyendo URLs desde links.txt (mismo directorio):
- Crea una carpeta por disco (playlist o video) dentro de ./salida (o la que indiques)
- Convierte a MP3 (bitrate configurable, default 128 kbps)
- Numera los temas (playlist_index si hay playlist; si no, autonumber)
- Descarga la carátula (thumbnail), la convierte a JPG y la embebe como album art
- Guarda también el JPG de la carátula junto al MP3 (renombrado a cover.jpg)

Uso:
    python discos_ytdlp.py
    python discos_ytdlp.py -o ./mi_salida -f mis_links.txt --kbps 320
    python discos_ytdlp.py --cookies ./cookies.txt --rate-limit 2M
"""

import argparse
from pathlib import Path
from src import funcionesyt

DEFAULT_LINKS_FILE = "links.txt"
def main():
    parser = argparse.ArgumentParser(
        description="Lee URLs desde links.txt y descarga cada disco en su propia carpeta con MP3 (bitrate configurable) + carátula."
    )
    parser.add_argument(
        "-f", "--file",
        default=DEFAULT_LINKS_FILE,
        help="Archivo de texto con las URLs (por defecto: links.txt en el mismo directorio).",
    )
    parser.add_argument(
        "-o", "--outdir",
        default="/home/marianof/Music/Spotify",
        help="Directorio base de salida (por defecto: /home/marianof/Music/Spotify).",
    )
    parser.add_argument(
        "--kbps",
        type=int,
        default=128,
        choices=[64, 96, 128, 160, 192, 224, 256, 320],
        help="Bitrate MP3 en kbps (default 128).",
    )
    parser.add_argument(
        "--cookies",
        default=None,
        help="Ruta a archivo de cookies (formato Netscape) para contenido restringido.",
    )
    parser.add_argument(
        "--proxy",
        default=None,
        help="Proxy (ej.: socks5://127.0.0.1:9050 o http://127.0.0.1:8080).",
    )
    parser.add_argument(
        "--rate-limit",
        default=None,
        help="Límite de velocidad (ej.: 2M, 1M).",
    )
    parser.add_argument(
        "--no-warnings",
        default=True,
        help="Sin advertencias",
    )
    parser.add_argument(
        "--no-playlist",
        action="store_true",
        help="Si se pasa, no descargará la playlist completa cuando la URL apunte a una.",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    links_path = (script_dir / args.file).resolve()
    base_out = Path(args.outdir).resolve()
    base_out.mkdir(parents=True, exist_ok=True)

    urls = list(funcionesyt.read_urls(links_path))
    if not urls:
        print(f"[INFO] No hay URLs en {links_path}")
        return

    print(f"[INFO] Voy a procesar {len(urls)} URL(s) desde {links_path}")
    for i, url in enumerate(urls, 1):
        print(f"\n[INFO] ({i}/{len(urls)}) Descargando disco: {url}")
        folder = funcionesyt.download_disc(
            url=url,
            base_out=base_out,
            kbps=args.kbps,
            cookies=args.cookies,
            proxy=args.proxy,
            rate_limit=args.rate_limit,
            no_playlist=args.no_playlist,
        )
        if folder:
            print(f"[OK] Guardado en: {folder}")
        else:
            print("[WARN] Este disco no se pudo descargar.")

if __name__ == "__main__":
    main()
