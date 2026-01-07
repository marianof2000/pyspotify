import sys
# Importamos los módulos (ahora es seguro porque el código está encapsulado)
from src import pyspotify3, pyyoutube

def main():
    # Revisamos qué bandera está presente
    if "--sp" in sys.argv:
        # IMPORTANTE: Quitamos '--sp' de sys.argv para que pyspotify3 
        # no se queje de un "unrecognized argument: --sp"
        sys.argv.remove("--sp")
        pyspotify3.main()
        
    elif "--yt" in sys.argv:
        # Lo mismo para YouTube, quitamos la bandera antes de pasar el control
        sys.argv.remove("--yt")
        pyyoutube.main()
        
    else:
        print("❌ Error: Debes especificar --sp (Spotify) o --yt (YouTube)")
        print("Ejemplo: python main.py --sp -f lista.txt")

if __name__ == "__main__":
    main()
    