FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==2.1.2

# `<regra_obrigatoria id="usuario-nao-root">`: container roda com usuário
# dedicado ao projeto, nunca root.
RUN groupadd --system anki_generator \
    && useradd --system --gid anki_generator --create-home --home-dir /home/anki_generator anki_generator

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-interaction --no-ansi

COPY . .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \
    && chown -R anki_generator:anki_generator /app \
    && mkdir -p /var/lib/celery \
    && chown -R anki_generator:anki_generator /var/lib/celery

USER anki_generator

# `<regra_obrigatoria id="entrypoint">`: inicialização via script entrypoint.
ENTRYPOINT ["/entrypoint.sh"]
CMD ["web"]
