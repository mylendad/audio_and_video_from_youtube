# FROM python:3.12-slim-buster
FROM python:3.12

WORKDIR /app

RUN pip install --no-cache-dir setuptools wheel

COPY pyproject.toml .

RUN pip install --no-cache-dir .

COPY . .

RUN useradd -m appuserapp
RUN chown -R appuser:appuser /app
USER appuser

CMD ["python", "main.py"]