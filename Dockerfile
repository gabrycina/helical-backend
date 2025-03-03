FROM python:3.12.2

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    gfortran \
    libopenblas-dev \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Create directories and set permissions
RUN mkdir -p /code/uploads /code/results && \
    chmod 777 /code/uploads /code/results

COPY ./app /code/app

# Create mount points for external volumes
VOLUME /code/uploads
VOLUME /code/results

# Set environment variables
ENV PYTHONPATH=/code
ENV UPLOAD_DIR=/code/uploads
ENV RESULTS_DIR=/code/results

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]