FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock README.md ./
COPY main.py parser.py insert_event.py auth.py config.py get_token.py ./
COPY token.json ./
COPY credentials.json ./
COPY .env ./

RUN poetry install --no-root --no-interaction --no-ansi

CMD ["poetry", "run", "python", "main.py"]
