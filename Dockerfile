
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt ./

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

CMD ["python", "app.py"]
