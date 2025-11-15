FROM python:3.12

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .

RUN useradd -m appuser
USER appuser

CMD ["python", "main.py"]
