FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system document_generator \
    && useradd --system --gid document_generator --create-home --home-dir /home/document_generator document_generator

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh \
    && chown -R document_generator:document_generator /app \
    && mkdir -p /data/anki_audio \
    && chown -R document_generator:document_generator /data

USER document_generator

ENTRYPOINT ["./entrypoint.sh"]
