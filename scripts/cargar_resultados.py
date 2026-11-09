#!/usr/bin/env python3
# cargar_resultados.py
# Lee la salida del job (part-00000) y guarda cada fila en la tabla "resultados".
# Se ejecuta DENTRO del contenedor api, porque ahi ya estan psycopg2 y la red hacia "db":
#   docker compose exec api python /scripts/cargar_resultados.py

import os
import sys

import psycopg2

RUTA_DEFECTO = "/data/output/resultado/part-00000"

CREAR_TABLA = """
CREATE TABLE IF NOT EXISTS resultados (
    id          SERIAL PRIMARY KEY,
    metodo_pago VARCHAR(30) NOT NULL,
    dia         VARCHAR(10) NOT NULL,
    unidades    INTEGER     NOT NULL,
    UNIQUE (metodo_pago, dia)
)
"""

# "Upsert": si ya existe la pareja (metodo_pago, dia), solo actualiza las unidades.
# Asi puedes correr el script varias veces sin duplicar filas.
# EXCLUDED es la fila que se intento insertar.
UPSERT = """
INSERT INTO resultados (metodo_pago, dia, unidades)
VALUES (%s, %s, %s)
ON CONFLICT (metodo_pago, dia) DO UPDATE SET unidades = EXCLUDED.unidades
"""


def leer_salida(ruta):
    """Convierte cada linea 'metodo<TAB>dia<TAB>unidades' en una tupla."""
    filas = []
    with open(ruta, encoding="utf-8") as f:
        for num, linea in enumerate(f, start=1):
            partes = linea.rstrip("\n").split("\t")
            try:
                metodo, dia, unidades = partes   # falla si no son exactamente 3 partes
                filas.append((metodo, dia, int(unidades)))
            except ValueError:
                print(f"Linea {num} ignorada: {linea!r}", file=sys.stderr)
    return filas


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else RUTA_DEFECTO
    filas = leer_salida(ruta)
    if not filas:
        sys.exit(f"No se encontraron filas validas en {ruta}")

    conn = psycopg2.connect(
        host=os.environ.get("DB_HOST", "db"),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
    try:
        with conn, conn.cursor() as cur:   # una sola transaccion: se carga todo o nada
            cur.execute(CREAR_TABLA)
            cur.executemany(UPSERT, filas)  # ejecuta el UPSERT una vez por cada tupla
    finally:
        conn.close()

    print(f"{len(filas)} registros cargados desde {ruta}")


if __name__ == "__main__":
    main()
