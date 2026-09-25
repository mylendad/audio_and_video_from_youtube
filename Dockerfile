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

USER appuser

CMD ["python", "main.py"]