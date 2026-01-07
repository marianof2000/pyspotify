#!/home/marianof/.pyenv/shims/python
# pip install -U spotdl
# usar con Python 3.11 o menor

""" Descarga todos los discos las listas de spotify """

import json
import os
import subprocess
import time

HOME = os.path.expanduser("~")
RAIZ = os.path.join(HOME, "Music/Spotify")


def descarga(url):
    """Descarga la lista de reproducción de un disco"""
    salida = os.path.join(RAIZ, "datos.spotdl")
    programa = os.path.join(HOME, ".pyenv/shims/spotdl")  # $HOME/.pyenv/shims/spotdl
    subprocess.Popen(f"{programa} save '{url}' --save-file '{salida}'", shell=True)
    time.sleep(30)
    try:
        with open(salida, "rt", encoding="utf-8") as f:
            data = json.load(f)
            artista = data[0]["album_artist"].replace(" ", "")
            album = data[0]["album_name"].replace(" ", "")
    except Exception as e:
        print(f"Error: {e}")
    else:
        path = os.path.join(RAIZ, artista, album)
        try:
            os.makedirs(path)
        except FileExistsError:
            print("El directorio ya está creado!")
        else:
            print(f"Se creó {path}\n")
        try:
            os.chdir(path)
        except FileExistsError:
            print("No existe el directorio de descarga")
        else:
            print(programa)
            try:
                subprocess.Popen(
                    f"{programa} download '{url}'  --threads 1", shell=True
                )
            except Exception as e:
                print(f"Error: {e}")
            else:
                print("Se descargaron los archivos")
            time.sleep(120)
    finally:
        os.chdir(RAIZ)
        try:
            os.remove(salida)
        except Exception as e:
            print(f"{e}: El archivo no existe")
        else:
            print("Se elimino el archivo")
    return


def limpiar():
    """Elimina todos los archivos .m3u y .m3u8 de la raíz"""
    lista = os.listdir(RAIZ)
    for item in lista:
        if item.endswith(".m3u") or item.endswith(".m3u8"):
            try:
                os.remove(os.path.join(RAIZ, item))
            except Exception as e:
                print(f"{e}: El archivo no existe")
            else:
                print("Se elimino el archivo")
    return


def main():
    """Descarga todos los discos de la raíz"""
    archivo = os.path.join(RAIZ, "discos")
    with open(archivo, "rt", encoding="utf-8") as f:
        for disco in f:
            descarga(disco.rstrip())
    time.sleep(10)
    limpiar()
    return


if __name__ == "__main__":
    main()
