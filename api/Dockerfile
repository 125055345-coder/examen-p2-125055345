FROM python:3.12-slim

# Muestra los print() en "docker compose logs" al momento, sin buffer
ENV PYTHONUNBUFFERED=1

# Cliente SSH: para demostrar el acceso api -> hadoop por nombre de servicio
RUN apt-get update \
 && apt-get install -y --no-install-recommends openssh-client \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Primero solo requirements.txt: si cambias app.py, Docker reutiliza la capa del pip install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5000
CMD ["python", "app.py"]
