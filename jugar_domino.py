import os
import sys
import subprocess

# Ruta de tu intérprete de Anaconda
python_path = r"C:\Users\juanv\anaconda3\python.exe"

# Comando para ejecutar el juego
command = [python_path, "-m", "domino.pygame_main"]

try:
    subprocess.run(command, check=True)
except FileNotFoundError:
    print("⚠️ No se encontró Python en la ruta especificada.")
    print("Verifica que la ruta de Anaconda sea correcta.")
    sys.exit(1)
except subprocess.CalledProcessError as e:
    print(f"❌ Error al ejecutar el juego: {e}") 