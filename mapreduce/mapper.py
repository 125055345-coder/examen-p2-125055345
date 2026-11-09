#!/usr/bin/env python3
# mapper.py
# Pregunta (matricula terminada en 5): unidades vendidas por metodo de pago y dia de la semana.
#
# Entrada (stdin): lineas del CSV
#   id,fecha_hora,tienda,categoria,producto,cantidad,precio_unitario,metodo_pago
# Salida (stdout): una linea por venta valida
#   metodo_pago|dia<TAB>cantidad

import sys
from datetime import date

# date.weekday() devuelve 0 para lunes ... 6 para domingo; usamos ese numero como indice.
# Sin acentos, igual que el dataset ("Electronica", "Papeleria").
DIAS = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]

for linea in sys.stdin:
    # strip() quita espacios y el fin de linea; el CSV termina en "\r\n",
    # asi que sin esto el metodo de pago saldria como "Tarjeta\r".
    linea = linea.strip()
    if not linea:
        continue

    campos = linea.split(",")

    # El encabezado no es un error: solo lo saltamos.
    if campos[0] == "id":
        continue

    try:
        if len(campos) != 8:
            raise ValueError("numero de columnas incorrecto")

        fecha = date.fromisoformat(campos[1][:10])   # "2025-06-27 12:09:37" -> "2025-06-27"
        dia = DIAS[fecha.weekday()]
        cantidad = int(campos[5])
        metodo = campos[7]
        if not metodo:
            raise ValueError("metodo de pago vacio")

    except ValueError:
        # Linea mal formada: la contamos con un contador de Hadoop y seguimos.
        # Hadoop Streaming interpreta este formato en stderr y lo muestra al final del job.
        sys.stderr.write("reporter:counter:Calidad,LineasMalFormadas,1\n")
        continue

    # La clave compuesta va antes del TAB; Hadoop ordena y agrupa por ella.
    print(f"{metodo}|{dia}\t{cantidad}")
