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

COPY ./app /code/app

# Create required directories
RUN mkdir -p /code/uploads /code/results

# Set environment variables
ENV PYTHONPATH=/code
ENV UPLOAD_DIR=/code/uploads
ENV RESULTS_DIR=/code/results

EXPOSE 8000

CMD ["fastapi", "run", "app/main.py", "--port", "80"]