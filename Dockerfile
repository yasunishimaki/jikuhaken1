FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-jpn && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Render 等が渡す PORT を使う。無ければ 8000 を既定に。
CMD ["sh","-c","gunicorn -w 2 -b 0.0.0.0:${PORT:-8000} backend.server:app"]
