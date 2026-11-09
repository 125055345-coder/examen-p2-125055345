#!/usr/bin/env python3
# secuencial.py
# Responde la MISMA pregunta que el job de MapReduce, pero en un solo proceso,
# leyendo el CSV linea por linea. Sirve para comparar tiempos y verificar resultados.
#
# Uso:    python3 secuencial.py /data/input/ventas_125055345.csv
# Salida: metodo_pago<TAB>dia<TAB>unidades   (mismo formato que el reducer)

import sys
from datetime import date

DIAS = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]

if len(sys.argv) != 2:
    sys.exit("Uso: python3 secuencial.py <ruta_csv>")

totales = {}   # diccionario {(metodo, dia): unidades}; hace el papel del shuffle + reduce
malas = 0

with open(sys.argv[1], encoding="utf-8") as f:
    for linea in f:
        # Esta parte es identica al mapper: misma limpieza y mismas validaciones.
        linea = linea.strip()
        if not linea:
            continue
        campos = linea.split(",")
        if campos[0] == "id":
            continue
        try:
            if len(campos) != 8:
                raise ValueError("numero de columnas incorrecto")
            dia = DIAS[date.fromisoformat(campos[1][:10]).weekday()]
            cantidad = int(campos[5])
            metodo = campos[7]
            if not metodo:
                raise ValueError("metodo de pago vacio")
        except ValueError:
            malas += 1
            continue

        # En vez de imprimir clave/valor, acumulamos directo en memoria.
        clave = (metodo, dia)
        totales[clave] = totales.get(clave, 0) + cantidad

for (metodo, dia), total in sorted(totales.items()):
    print(f"{metodo}\t{dia}\t{total}")

# A stderr para que no se mezcle con los resultados
print(f"Lineas mal formadas: {malas}", file=sys.stderr)
