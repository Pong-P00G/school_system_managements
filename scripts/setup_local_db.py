#!/usr/bin/env python3
"""
setup_local_db.py — Run once after cloning to set up the local PostgreSQL database.
Usage: python scripts/setup_local_db.py
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"


def ask(prompt, default=""):
    value = input(f"{prompt} [{default}]: ").strip()
    return value or default


def run(cmd, cwd=None, env=None):
    result = subprocess.run(cmd, cwd=cwd, env=env)
    if result.returncode != 0:
        print(f"\nERROR: Command failed: {' '.join(cmd)}")
        sys.exit(1)


def main():
    print("=" * 44)
    print("  School System — Local Database Setup")
    print("=" * 44)

    user     = ask("PostgreSQL username", "postgres")
    password = ask("PostgreSQL password", "")
    host     = ask("Host", "localhost")
    port     = ask("Port", "5432")
    db_name  = ask("Database name", "school_system_db_v2")

    sync_url  = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    async_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}"

    # 1. Create database
    print(f"\n[1/4] Creating database '{db_name}'...")
    env = {**os.environ, "PGPASSWORD": password}
    subprocess.run(
        ["psql", "-U", user, "-h", host, "-p", port, "-c", f"CREATE DATABASE {db_name};"],
        env=env, capture_output=True
    )  # ignore error if DB already exists

    # 2. Write .env
    print("[2/4] Writing backend/.env ...")
    env_content = f"""DATABASE_URL={async_url}
DATABASE_URL_SYNC={sync_url}
APP_NAME=School Management System API
APP_VERSION=1.0.0
DEBUG=true
SECRET_KEY=change-this-to-a-secure-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
PROMETHEUS_ENABLED=true
"""
    (BACKEND / ".env").write_text(env_content)

    # 3. Patch alembic.ini
    print("[3/4] Updating alembic.ini ...")
    alembic_ini = BACKEND / "alembic.ini"
    lines = alembic_ini.read_text().splitlines()
    patched = [
        f"sqlalchemy.url = {sync_url}" if line.startswith("sqlalchemy.url") else line
        for line in lines
    ]
    alembic_ini.write_text("\n".join(patched) + "\n")

    # 4. Run migrations
    print("[4/4] Running Alembic migrations...")
    run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND)

    print("\n" + "=" * 44)
    print(f"  Done! Database '{db_name}' is ready.")
    print("  Next: cd backend && uvicorn app.main:app --reload")
    print("=" * 44)


if __name__ == "__main__":
    main()
