# app.py - API del DataMart
# Expone los resultados del job de MapReduce:
# unidades vendidas por metodo de pago y dia de la semana.

import os
import time

import psycopg2
from psycopg2 import errors
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request

app = Flask(__name__)
app.json.sort_keys = False   # respeta el orden de las columnas en el JSON

# Conexion: los valores vienen de variables de entorno (.env + docker-compose.yml).
# DB_HOST = "db" es el NOMBRE DEL SERVICIO en el compose; Docker lo resuelve como hostname.
DB = {
    "host": os.environ.get("DB_HOST", "db"),
    "dbname": os.environ["POSTGRES_DB"],
    "user": os.environ["POSTGRES_USER"],
    "password": os.environ["POSTGRES_PASSWORD"],
}

DIAS_VALIDOS = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]

CREAR_TABLA = """
CREATE TABLE IF NOT EXISTS resultados (
    id          SERIAL PRIMARY KEY,
    metodo_pago VARCHAR(30) NOT NULL,
    dia         VARCHAR(10) NOT NULL,
    unidades    INTEGER     NOT NULL,
    UNIQUE (metodo_pago, dia)
)
"""


def ejecutar(sql, params=(), traer="todos"):
    """Abre una conexion, ejecuta la consulta y la cierra.
    traer="todos" -> lista de filas, "uno" -> una fila (o None), None -> nada."""
    conn = psycopg2.connect(**DB)
    try:
        with conn:   # hace commit si todo sale bien, o rollback si hay un error
            with conn.cursor(cursor_factory=RealDictCursor) as cur:   # filas como diccionarios
                cur.execute(sql, params)   # %s + params: psycopg2 escapa los valores (evita SQL injection)
                if traer == "todos":
                    return cur.fetchall()
                if traer == "uno":
                    return cur.fetchone()
                return None
    finally:
        conn.close()   # ojo: "with conn" en psycopg2 NO cierra la conexion, por eso se cierra aqui


def validar_unidades(valor):
    return isinstance(valor, int) and not isinstance(valor, bool) and valor >= 0


# ---------- Lectura ----------

@app.get("/resultados")
def listar():
    return jsonify(ejecutar("SELECT * FROM resultados ORDER BY metodo_pago, dia"))


@app.get("/resultados/<metodo_pago>")
def por_metodo(metodo_pago):
    # LOWER en ambos lados: /resultados/tarjeta y /resultados/Tarjeta dan lo mismo
    filas = ejecutar(
        "SELECT * FROM resultados WHERE LOWER(metodo_pago) = LOWER(%s) ORDER BY dia",
        (metodo_pago,),
    )
    if not filas:
        return jsonify({"error": f"No hay resultados para '{metodo_pago}'"}), 404
    return jsonify(filas)


# ---------- Escritura (CRUD) ----------

@app.post("/resultados")
def crear():
    datos = request.get_json(silent=True) or {}
    metodo = datos.get("metodo_pago")
    dia = datos.get("dia")
    unidades = datos.get("unidades")

    if not isinstance(metodo, str) or not metodo.strip():
        return jsonify({"error": "metodo_pago es obligatorio"}), 400
    if dia not in DIAS_VALIDOS:
        return jsonify({"error": f"dia debe ser uno de {DIAS_VALIDOS}"}), 400
    if not validar_unidades(unidades):
        return jsonify({"error": "unidades debe ser un entero >= 0"}), 400

    try:
        fila = ejecutar(
            "INSERT INTO resultados (metodo_pago, dia, unidades) VALUES (%s, %s, %s) RETURNING *",
            (metodo.strip(), dia, unidades),
            traer="uno",
        )
    except errors.UniqueViolation:
        # La restriccion UNIQUE (metodo_pago, dia) de la tabla impide duplicados
        return jsonify({"error": "Ya existe un registro para ese metodo de pago y dia"}), 409
    return jsonify(fila), 201


@app.put("/resultados/<int:registro_id>")
def actualizar(registro_id):
    datos = request.get_json(silent=True) or {}
    if not validar_unidades(datos.get("unidades")):
        return jsonify({"error": "unidades debe ser un entero >= 0"}), 400

    fila = ejecutar(
        "UPDATE resultados SET unidades = %s WHERE id = %s RETURNING *",
        (datos["unidades"], registro_id),
        traer="uno",
    )
    if fila is None:
        return jsonify({"error": f"No existe el registro {registro_id}"}), 404
    return jsonify(fila)


@app.delete("/resultados/<int:registro_id>")
def borrar(registro_id):
    fila = ejecutar("DELETE FROM resultados WHERE id = %s RETURNING *", (registro_id,), traer="uno")
    if fila is None:
        return jsonify({"error": f"No existe el registro {registro_id}"}), 404
    return jsonify({"borrado": fila})


# ---------- Arranque ----------

def preparar_base(intentos=10):
    """Crea la tabla si no existe. Reintenta por si la base todavia esta arrancando."""
    for i in range(1, intentos + 1):
        try:
            ejecutar(CREAR_TABLA, traer=None)
            print("Base de datos lista", flush=True)
            return
        except psycopg2.OperationalError:
            print(f"Base de datos no disponible (intento {i}/{intentos})", flush=True)
            time.sleep(2)
    raise SystemExit("No se pudo conectar a la base de datos")


if __name__ == "__main__":
    preparar_base()
    # host 0.0.0.0: escucha en todas las interfaces del contenedor.
    # Con el default (127.0.0.1) la API solo seria visible DENTRO del contenedor
    # y el mapeo de puertos del compose no funcionaria.
    app.run(host="0.0.0.0", port=5000)
