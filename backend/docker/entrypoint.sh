#!/bin/sh
set -e

if [ -n "$DB_HOST" ]; then
  python - <<'PY'
import os
import socket
import time

host = os.environ["DB_HOST"]
port = int(os.environ.get("DB_PORT", "5432"))
deadline = time.time() + int(os.environ.get("DB_WAIT_TIMEOUT", "60"))

while True:
    try:
        with socket.create_connection((host, port), timeout=3):
            break
    except OSError:
        if time.time() >= deadline:
            raise
        time.sleep(1)
PY
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
