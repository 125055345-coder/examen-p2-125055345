#!/usr/bin/env python3
# reducer.py
# Suma las unidades de cada clave "metodo_pago|dia".
#
# Entrada (stdin): salida del mapper YA ORDENADA por clave
#   Efectivo|Jueves<TAB>5
#   Efectivo|Jueves<TAB>3
#   Efectivo|Lunes<TAB>7
# Salida (stdout):
#   metodo_pago<TAB>dia<TAB>unidades

import sys


def emitir(clave, total):
    metodo, dia = clave.split("|")
    print(f"{metodo}\t{dia}\t{total}")


clave_actual = None
total = 0

for linea in sys.stdin:
    try:
        clave, valor = linea.rstrip("\n").split("\t", 1)
        valor = int(valor)
    except ValueError:
        continue

    if clave == clave_actual:
        # Misma clave que la linea anterior: seguimos acumulando.
        total += valor
    else:
        # Cambio la clave: el grupo anterior ya termino, lo imprimimos
        # y empezamos a contar el nuevo.
        if clave_actual is not None:
            emitir(clave_actual, total)
        clave_actual = clave
        total = valor

# El ultimo grupo no tiene una "siguiente clave" que lo dispare, hay que emitirlo aqui.
if clave_actual is not None:
    emitir(clave_actual, total)
