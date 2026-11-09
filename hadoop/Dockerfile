# Imagen de Hadoop 3.5.0 en modo standalone, con Python 3 y servidor SSH
FROM debian:bookworm-slim

ARG HADOOP_VERSION=3.5.0

# JAVA_HOME: donde esta Java. default-java es un enlace que Debian crea hacia el JDK instalado (17).
# HADOOP_HOME: donde vamos a descomprimir Hadoop.
# PATH: agregamos bin/ y sbin/ de Hadoop para poder escribir "hadoop" desde cualquier carpeta.
ENV JAVA_HOME=/usr/lib/jvm/default-java \
    HADOOP_HOME=/opt/hadoop \
    PATH=/opt/hadoop/bin:/opt/hadoop/sbin:$PATH

# 1) Paquetes: Java (OpenJDK 17), Python 3, servidor y cliente SSH, curl para descargar Hadoop.
#    El mkdir evita un error conocido al instalar Java en imagenes "slim" (no traen carpetas de man).
RUN mkdir -p /usr/share/man/man1 \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      default-jdk-headless python3 openssh-server openssh-client \
      curl ca-certificates procps \
 && rm -rf /var/lib/apt/lists/*

# 2) Hadoop: se descarga del CDN de Apache; si esa version ya no esta ahi, del archivo historico.
#    Va en su propia capa para que Docker no lo vuelva a descargar si cambias otra cosa.
RUN set -e; \
    ARCHIVO="hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz"; \
    curl -fSL "https://dlcdn.apache.org/hadoop/common/${ARCHIVO}" -o /tmp/hadoop.tar.gz \
      || curl -fSL "https://archive.apache.org/dist/hadoop/common/${ARCHIVO}" -o /tmp/hadoop.tar.gz; \
    tar -xzf /tmp/hadoop.tar.gz -C /opt; \
    mv "/opt/hadoop-${HADOOP_VERSION}" "${HADOOP_HOME}"; \
    rm -rf /tmp/hadoop.tar.gz "${HADOOP_HOME}/share/doc"

# 3) Hadoop lee JAVA_HOME de hadoop-env.sh cuando se lanza por SSH (pseudo-distribuido).
RUN echo "export JAVA_HOME=${JAVA_HOME}" >> "${HADOOP_HOME}/etc/hadoop/hadoop-env.sh"

# 4) SSH sin contrasena, solo con llaves:
#    - ssh-keygen -N "" crea un par de llaves sin passphrase
#    - la llave publica se agrega a authorized_keys: "quien tenga la privada puede entrar"
#    - accept-new: acepta la huella del servidor la primera vez sin preguntar
#    - sshd: se prohibe el login con contrasena; root solo entra con llave
#    - /run/sshd: carpeta que sshd necesita para arrancar
#    - ssh-keygen -A: crea las llaves del SERVIDOR (su "huella") si no existen
RUN mkdir -p /root/.ssh /run/sshd \
 && ssh-keygen -A \
 && ssh-keygen -t rsa -b 4096 -N "" -f /root/.ssh/id_rsa \
 && cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys \
 && printf 'Host *\n  StrictHostKeyChecking accept-new\n' > /root/.ssh/config \
 && chmod 700 /root/.ssh \
 && chmod 600 /root/.ssh/authorized_keys /root/.ssh/config \
 && printf 'PasswordAuthentication no\nPermitRootLogin prohibit-password\n' \
      > /etc/ssh/sshd_config.d/solo-llaves.conf

# 5) Las variables ENV de Docker NO existen dentro de una sesion SSH (sshd arma un entorno nuevo).
#    /etc/environment las da a comandos como "ssh hadoop hadoop version";
#    /etc/profile.d las da a sesiones interactivas.
RUN printf 'JAVA_HOME=%s\nHADOOP_HOME=%s\nPATH=%s\n' "$JAVA_HOME" "$HADOOP_HOME" "$PATH" >> /etc/environment \
 && printf 'export JAVA_HOME=%s\nexport HADOOP_HOME=%s\nexport PATH=%s\n' "$JAVA_HOME" "$HADOOP_HOME" "$PATH" \
      > /etc/profile.d/hadoop.sh

# 6) Verificacion: si Hadoop o Java quedaron mal, el build falla aqui mismo.
RUN hadoop version

WORKDIR /mapreduce
EXPOSE 22

# Al arrancar el contenedor:
#  - copia la llave privada al volumen compartido /llaves para que el contenedor api pueda entrar por SSH
#  - ejecuta sshd en primer plano (-D); al ser el proceso principal, mantiene vivo el contenedor
CMD ["bash", "-c", "mkdir -p /llaves && cp /root/.ssh/id_rsa /llaves/id_rsa && chmod 600 /llaves/id_rsa && exec /usr/sbin/sshd -D -e"]
