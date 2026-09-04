# ============================================
# ETAPA 1: BUILDER
# ============================================
# Usamos Python 3.12 sobre una imagen Debian "slim".
# Esta etapa se utiliza para instalar las dependencias
# de Python dentro de un entorno virtual aislado.
FROM python:3.12-slim AS builder

# Directorio de trabajo dentro del contenedor.
WORKDIR /app

# --------------------------------------------
# Actualización de paquetes del sistema
# --------------------------------------------
# Actualizamos la lista de paquetes disponibles
# y posteriormente instalamos las versiones corregidas
# de los paquetes del sistema operativo.
#
# Esto es importante para reducir vulnerabilidades
# detectadas por herramientas como Trivy.
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------
# Creación del entorno virtual
# --------------------------------------------
# Creamos un entorno virtual independiente del Python
# del sistema.
RUN python -m venv /opt/venv

# Hacemos que los comandos python y pip utilizados
# posteriormente correspondan al entorno virtual.
ENV PATH="/opt/venv/bin:$PATH"

# Copiamos únicamente el archivo de dependencias.
COPY requirements.txt .

# --------------------------------------------
# Instalación de dependencias
# --------------------------------------------
# Instalamos las dependencias necesarias para producción.
#
# Después:
# - Eliminamos __pycache__, porque Python puede regenerarlo.
# - Eliminamos pip, setuptools y wheel del entorno final,
#   porque únicamente son necesarios durante la instalación.
RUN pip install --no-cache-dir -r requirements.txt \
    && find /opt/venv -type d -name "__pycache__" -exec rm -rf {} + \
    && rm -rf /opt/venv/lib/python3.12/site-packages/pip \
              /opt/venv/lib/python3.12/site-packages/pip-*.dist-info \
              /opt/venv/lib/python3.12/site-packages/setuptools \
              /opt/venv/lib/python3.12/site-packages/setuptools-*.dist-info \
              /opt/venv/lib/python3.12/site-packages/wheel \
              /opt/venv/lib/python3.12/site-packages/wheel-*.dist-info \
              /opt/venv/bin/pip*


# ============================================
# ETAPA 2: PRODUCCIÓN
# ============================================
# Volvemos a utilizar una imagen Python 3.12-slim
# limpia para construir la imagen que realmente
# ejecutará nuestra API.
FROM python:3.12-slim

# Directorio de trabajo de la aplicación.
WORKDIR /app

# --------------------------------------------
# Actualización de paquetes del sistema
# --------------------------------------------
# Actualizamos los paquetes Debian de la imagen final
# para obtener las versiones que contienen las
# correcciones de seguridad disponibles.
#
# Esta parte es especialmente importante porque
# Trivy analiza también las librerías del sistema
# operativo dentro de la imagen.
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------
# Copiar el entorno Python
# --------------------------------------------
# Copiamos desde la etapa builder el entorno virtual
# que contiene las dependencias de producción.
COPY --from=builder /opt/venv /opt/venv

# Indicamos que los ejecutables y paquetes del entorno
# virtual deben utilizarse por defecto.
ENV PATH="/opt/venv/bin:$PATH"

# --------------------------------------------
# Código de la aplicación
# --------------------------------------------
# Copiamos únicamente las partes necesarias para
# ejecutar la API.
COPY app/ app/

# Copiamos las migraciones de Alembic.
COPY alembic/ alembic/


# Copiamos la configuración de Alembic.
COPY alembic.ini .

# Puerto donde escuchará la API.
EXPOSE 8000

# --------------------------------------------
# Arranque de la aplicación
# --------------------------------------------
# Primero ejecutamos las migraciones pendientes.
#
# Después iniciamos Uvicorn con FastAPI.
#
# Se utiliza formato JSON para evitar el warning
# de Docker relacionado con CMD y permitir un
# manejo correcto de señales del proceso.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]