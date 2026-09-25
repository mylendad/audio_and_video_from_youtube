FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg curl unzip && \
    rm -rf /var/lib/apt/lists/*

# JavaScript runtime для yt-dlp (анти-бот проверки YouTube)
RUN curl -fsSL "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-unknown-linux-gnu.zip" -o /tmp/deno.zip && \
    unzip -o /tmp/deno.zip -d /usr/local/bin && \
    rm /tmp/deno.zip && \
    deno --version

COPY pyproject.toml .
RUN pip install --no-cache-dir setuptools wheel && \
    pip install --no-cache-dir --timeout=300 .

RUN useradd -u 10001 -m appuser

COPY . .
RUN chown -R appuser:appuser /app

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Запуск через entrypoint от root: копирует SSH-ключ storage-сервера в /tmp
# (appuser не может читать host-маунт), затем опускает права до appuser.
ENTRYPOINT ["/entrypoint.sh"]

CMD ["python", "main.py"]