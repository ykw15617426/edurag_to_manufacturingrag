FROM python:3.10.20-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ curl libgl1 libglib2.0-0 libmagic1 zlib1g-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
# Install the pinned CPU torch wheel; no model weights are downloaded.
RUN pip install --no-cache-dir 'pip<24.1' \
    && pip install --no-cache-dir --no-deps torch==2.10.0+cpu --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt
RUN useradd --create-home --uid 10001 --shell /bin/bash app && mkdir -p /app/runtime /app/logs && chown -R app:app /app
COPY --chown=app:app . .
USER app
EXPOSE 8080
CMD ["sh", "-c", "exec python -m uvicorn manufacturing_app:app --host ${HOST:-0.0.0.0} --port ${PORT:-8080}"]
