#!/bin/bash
# Azure App Service Startup Script for SmartShop Django Application

set -euo pipefail

export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_NO_INPUT=1

echo "========================================"
echo "Starting SmartShop Deployment Process"
echo "========================================"

# Determine application directory (Oryx may run from an extracted /tmp folder)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR=""

pick_app_dir() {
    for candidate in \
        "${APP_PATH:-}" \
        "${ORYX_APP_PATH:-}" \
        "$SCRIPT_DIR" \
        "/home/site/wwwroot" \
        "/site/wwwroot"; do
        if [ -n "$candidate" ] && [ -f "$candidate/manage.py" ] && [ -f "$candidate/smartshop/settings.py" ]; then
            echo "$candidate"
            return 0
        fi
    done

    # Last resort: look for an extracted app under /tmp (kept shallow to avoid slow startup)
    for candidate in /tmp/*; do
        if [ -d "$candidate" ] && [ -f "$candidate/manage.py" ] && [ -f "$candidate/smartshop/settings.py" ]; then
            echo "$candidate"
            return 0
        fi
    done

    return 1
}

APP_DIR="$(pick_app_dir || true)"
if [ -z "$APP_DIR" ]; then
    # Fall back to script dir or conventional wwwroot, even if smartshop/settings.py isn't found
    if [ -f "$SCRIPT_DIR/manage.py" ]; then
        APP_DIR="$SCRIPT_DIR"
    elif [ -f "/home/site/wwwroot/manage.py" ]; then
        APP_DIR="/home/site/wwwroot"
    elif [ -f "/site/wwwroot/manage.py" ]; then
        APP_DIR="/site/wwwroot"
    else
        APP_DIR="$SCRIPT_DIR"
    fi
fi

echo "Script directory: $SCRIPT_DIR"
echo "App directory: $APP_DIR"
echo "Contents of app directory (top-level):"
ls -la "$APP_DIR" || true
echo "SmartShop package dir check:"
ls -la "$APP_DIR/smartshop" 2>/dev/null || true

if [ ! -f "$APP_DIR/smartshop/settings.py" ]; then
    echo "ERROR: Could not find $APP_DIR/smartshop/settings.py"
    echo "This usually means the 'smartshop/' folder wasn't uploaded to the server."
    exit 1
fi

# Ensure project root is importable (fixes ModuleNotFoundError: smartshop)
export PYTHONPATH="$APP_DIR${PYTHONPATH:+:$PYTHONPATH}"

# Ensure settings module is set for management commands
export DJANGO_SETTINGS_MODULE="smartshop.settings"

# Resolve Python executable (Kudu/SCM shells often don't have `python` on PATH)
PYTHON_BIN="$(command -v python 2>/dev/null || true)"
if [ -z "$PYTHON_BIN" ]; then
    for candidate in /opt/python/*/bin/python /opt/python/*/bin/python3 /opt/python/*/bin/python3.11; do
        if [ -x "$candidate" ]; then
            PYTHON_BIN="$candidate"
            break
        fi
    done
fi

if [ -z "$PYTHON_BIN" ]; then
    echo "ERROR: Python runtime not found. Ensure App Service is configured for Python 3.11."
    exit 1
fi

echo "Using Python: $PYTHON_BIN"
$PYTHON_BIN -V

# Navigate to the application directory
cd "$APP_DIR"

# Create/use a virtual environment in wwwroot (persisted under /home)
VENV_DIR="$APP_DIR/antenv"
resolve_venv_python() {
    for candidate in \
        "$VENV_DIR/bin/python" \
        "$VENV_DIR/bin/python3" \
        "$VENV_DIR/bin/python3.11"; do
        if [ -x "$candidate" ]; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

create_venv() {
    echo "Creating virtual environment: $VENV_DIR"
    rm -rf "$VENV_DIR" 2>/dev/null || true
    # Azure wwwroot can have limited symlink support; --copies avoids broken 'bin/python' links
    $PYTHON_BIN -m venv --copies "$VENV_DIR"
}

VENV_PY="$(resolve_venv_python || true)"
if [ -z "$VENV_PY" ]; then
    create_venv
    VENV_PY="$(resolve_venv_python || true)"
fi

if [ -z "$VENV_PY" ]; then
    echo "ERROR: Virtual environment was created but no python executable was found."
    echo "Contents of $VENV_DIR (top-level):"
    ls -la "$VENV_DIR" || true
    echo "Contents of $VENV_DIR/bin:"
    ls -la "$VENV_DIR/bin" || true
    exit 1
fi

echo "Using venv python: $VENV_PY"
"$VENV_PY" -V

# Install dependencies
echo "[1/6] Installing Python dependencies..."
"$VENV_PY" -m pip install --upgrade pip

# Avoid reinstalling on every restart (helps container start within probe timeout)
REQ_HASH_FILE="$VENV_DIR/.requirements.sha256"
NEW_REQ_HASH="$(sha256sum requirements.txt | awk '{print $1}')"
OLD_REQ_HASH="$(cat "$REQ_HASH_FILE" 2>/dev/null || true)"
if [ "$NEW_REQ_HASH" != "$OLD_REQ_HASH" ]; then
    echo "Installing requirements (this may take a few minutes on first run)..."
    "$VENV_PY" -m pip install -r requirements.txt
    echo "$NEW_REQ_HASH" > "$REQ_HASH_FILE"
else
    echo "Requirements unchanged; skipping pip install."
fi

# Run database migrations (AUTOMATIC)
echo "[2/6] Running database migrations..."
echo "Database env sanity (secrets omitted):"
echo "  DB_HOST=${DB_HOST:-<not set>}"
echo "  DB_PORT=${DB_PORT:-<not set>}"
echo "  DB_NAME=${DB_NAME:-<not set>}"
echo "  DB_USER=${DB_USER:-<not set>}"

if [ -f "$APP_DIR/.env" ]; then
    echo "NOTE: Found a .env file in the app directory."
    echo "      For Azure deployments, prefer App Service Configuration settings and avoid uploading .env."
fi

# On Azure, require DB_USER to be set via App Settings to avoid silently
# falling back to values from an uploaded .env (commonly 'root').
if [ -n "${WEBSITE_SITE_NAME:-}" ] && [ -z "${DB_USER:-}" ]; then
    echo "ERROR: DB_USER is not set in App Service Configuration."
    echo "Fix: App Service → Configuration → Application settings → add DB_USER=smartshopadmin (or your MySQL admin user), Save, then Restart."
    echo "Also: remove the uploaded .env file from /home/site/wwwroot to avoid accidental overrides."
    exit 1
fi

if [ -n "${DB_HOST:-}" ]; then
    echo "Preflight: testing TCP connectivity to ${DB_HOST}:${DB_PORT:-3306} ..."
    "$VENV_PY" - <<'PY'
import os
import socket
import time

host = os.environ.get("DB_HOST")
port_str = os.environ.get("DB_PORT", "3306")
port = int(port_str) if port_str else 3306

for attempt in range(1, 4):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    try:
        sock.connect((host, port))
        print(f"TCP OK: {host}:{port}")
        break
    except Exception as exc:
        print(f"TCP attempt {attempt}/3 failed: {exc}")
        if attempt == 3:
            raise SystemExit(
                "ERROR: Cannot reach MySQL from this App Service instance. "
                "Check MySQL Networking/Firewall (or VNet integration/private endpoint)."
            )
        time.sleep(2)
    finally:
        try:
            sock.close()
        except Exception:
            pass
PY
fi

"$VENV_PY" manage.py migrate --noinput

# Populate categories if not exists (AUTOMATIC)
echo "[3/6] Setting up initial data..."
"$VENV_PY" manage.py populate_categories --noinput 2>/dev/null || echo "Categories already exist or skipped"

# Collect static files (AUTOMATIC)
echo "[4/6] Collecting static files..."
"$VENV_PY" manage.py collectstatic --noinput

# Create default superuser if needed (using environment variables)
echo "[5/6] Checking for superuser..."
"$VENV_PY" manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@smartshop.com', 'SmartShop2026!');
    print('Default superuser created: admin / SmartShop2026!');
else:
    print('Superuser already exists');
" || echo "Superuser check completed"

# Start Gunicorn server
echo "[6/6] Starting Gunicorn server..."
echo "========================================"
PORT_TO_BIND="${PORT:-8000}"
echo "Binding to port: $PORT_TO_BIND"
"$VENV_PY" -m gunicorn smartshop.wsgi:application \
    --bind "0.0.0.0:${PORT_TO_BIND}" \
    --workers 4 \
    --timeout 600 \
    --access-logfile '-' \
    --error-logfile '-' \
    --log-level info
