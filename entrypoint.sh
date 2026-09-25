#!/bin/sh
set -e

# SSH-ключ для SFTP-хранилища монтируется из docker-compose (read-only) и может
# принадлежать другому UID хоста, из-за чего appuser не может его прочитать.
# Копируем ключ в /tmp с владельцем appuser, после чего опускаем права процесса.
if [ -f /app/id_ed25519 ] && [ ! -f /tmp/id_ed25519 ]; then
    cp /app/id_ed25519 /tmp/id_ed25519
    chmod 600 /tmp/id_ed25519
    chown appuser:appuser /tmp/id_ed25519
fi

exec su appuser -s /bin/sh -c 'exec "$@"' appuser "$@"