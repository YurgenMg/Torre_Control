#!/usr/bin/env python3
"""Wrapper para ejecutar load_data.py con manejo de output"""

import subprocess
import sys
import os

os.chdir(r'C:\Users\USUARIO\Documents\Yurgenpersonal\Tripleten\Portafolio\Proyecto_TorreContol')

print("[WRAPPER] Ejecutando load_data.py...")
print("[WRAPPER] Output será guardado en load_data_output.txt")
print()

# Ejecutar y capturar output en tiempo real
try:
    with open('load_data_output.txt', 'w', encoding='utf-8') as f:
        process = subprocess.Popen(
            ['python', 'scripts/load_data.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8'
        )

        for line in process.stdout:
            print(line, end='')
            f.write(line)
            f.flush()

        RETURNCODE = process.wait()
        print(f"\n[WRAPPER] Proceso finalizado con código: {RETURNCODE}")

except (FileNotFoundError, subprocess.SubprocessError, OSError, IOError) as e:
    print(f"[ERROR] {e}")
    sys.exit(1)
