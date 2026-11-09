# Examen Segundo Parcial — Pipeline de datos contenerizado

- **Matrícula:** 125055345
- **Pregunta asignada (último dígito 5):** Unidades vendidas por método de pago y día de la semana.

## Arquitectura

| Servicio | Qué hace |
|---|---|
| `hadoop` | Debian + Java 17 + Python 3 + Hadoop 3.5.0 (standalone) + OpenSSH. Ejecuta el job de MapReduce. |
| `db` | PostgreSQL 16 con volumen nombrado `pgdata`. |
| `api` | Flask. Expone los resultados y el CRUD sobre la tabla `resultados`. |

Los tres servicios están en la red `datamart_net` y se comunican por nombre de servicio.

## Cómo reproducir

```bash
# 1. Generar el dataset (~400 MB, no se sube al repo)
python3 scripts/generar_dataset.py 125055345

# 2. Variables de entorno
cp .env.example .env

# 3. Levantar todo
docker compose up --build -d

# 4. Job de MapReduce
docker compose exec hadoop bash -c 'rm -rf /data/output/resultado && time hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar -files mapper.py,reducer.py -input /data/input/ventas_125055345.csv -output /data/output/resultado -mapper "python3 mapper.py" -reducer "python3 reducer.py"'

# 5. Script secuencial y comparación
docker compose exec hadoop bash -c 'time python3 secuencial.py /data/input/ventas_125055345.csv > /data/output/secuencial.txt'
docker compose exec hadoop bash -c 'diff <(sort /data/output/resultado/part-00000) <(sort /data/output/secuencial.txt) && echo "RESULTADOS IDENTICOS"'

# 6. Cargar resultados en la base de datos
docker compose exec api python /scripts/cargar_resultados.py
```

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/resultados` | Todos los registros |
| GET | `/resultados/<metodo_pago>` | Filtro por método de pago (sin distinguir mayúsculas) |
| POST | `/resultados` | Crea un registro: `{"metodo_pago": "...", "dia": "Lunes", "unidades": 10}` |
| PUT | `/resultados/<id>` | Actualiza unidades: `{"unidades": 20}` |
| DELETE | `/resultados/<id>` | Borra un registro |

## Tiempos medidos

| Método | Tiempo real (`time`) |
|---|---|
| Hadoop Streaming | _pendiente_ |
| Script secuencial | _pendiente_ |

**¿Por qué uno fue más rápido?** _pendiente: escribir el párrafo con base en los tiempos medidos._

## Evidencias

Ver carpeta `evidencias/`:

- `hadoop_version.txt` — salida de `hadoop version`
- `ssh_localhost.txt` y `ssh_api_a_hadoop.txt` — acceso SSH sin contraseña
- `job_hadoop.log` — salida del job (incluye el contador `LineasMalFormadas`)
- `resultado_job.txt` — contenido de `part-00000`
- `secuencial.log` y `comparacion.txt` — tiempo del secuencial y verificación
- `api_*.json` — respuestas de la API
- `persistencia.txt` — datos tras `docker compose down` / `up`
