import sys
# Importamos los módulos (ahora es seguro porque el código está encapsulado)
from src import pyspotify, pyyoutube

def main():
    """
    Contrato:
        Selecciona el flujo de descarga a ejecutar segun las banderas de CLI.
    Precondiciones:
        `sys.argv` puede incluir `--sp` para Spotify o `--yt` para YouTube.
    Postcondiciones:
        Si la bandera es valida, delega la ejecucion al modulo correspondiente.
        Si falta la bandera, informa el uso esperado por consola.
    """
    # Revisamos qué bandera está presente
    if "--sp" in sys.argv:
        # IMPORTANTE: Quitamos '--sp' de sys.argv para que pyspotify
        # no se queje de un "unrecognized argument: --sp"
        sys.argv.remove("--sp")
        pyspotify.main()
        
    elif "--yt" in sys.argv:
        # Lo mismo para YouTube, quitamos la bandera antes de pasar el control
        sys.argv.remove("--yt")
        pyyoutube.main()

    else:
        print("Error: Debes especificar --sp (Spotify) o --yt (YouTube)")
        print("Ejemplo: uv run python main.py --sp -f lista.txt")

if __name__ == "__main__":
    main()
