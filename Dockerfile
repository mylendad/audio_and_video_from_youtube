FROM python:3.12

WORKDIR /app

COPY pyproject.toml .
RUN pip install .

COPY . .

RUN useradd -m appuser
USER appuser

CMD ["python", "main.py"]
