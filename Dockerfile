FROM python:3.8-slim

WORKDIR /app

RUN pip install poetry==1.1.4

COPY pyproject.toml poetry.lock /app/
RUN POETRY_VIRTUALENVS_IN_PROJECT=true poetry install --no-dev --no-root
COPY . .

RUN poetry build && pip install dist/*.whl
CMD kcctl sync