#!/bin/bash
# =============================================================
# Database Restore Script for School Management System
# =============================================================
set -euo pipefail

DB_CONTAINER="${DB_CONTAINER:-school_db}"
DB_NAME="${DB_NAME:-school_system_db}"
DB_USER="${DB_USER:-school_admin}"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo ""
    echo "Available backups:"
    ls -lh ./backups/${DB_NAME}_*.sql.gz 2>/dev/null || echo "  No backups found in ./backups/"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "=========================================="
echo "  Database Restore"
echo "=========================================="
echo "  Source: $BACKUP_FILE"
echo "  Target: $DB_NAME"
echo ""
read -p "  WARNING: This will overwrite the current database. Continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "  Restore cancelled."
    exit 0
fi

echo ""
echo "[1/3] Dropping existing database..."
docker exec "$DB_CONTAINER" dropdb -U "$DB_USER" --if-exists "$DB_NAME"

echo "[2/3] Creating fresh database..."
docker exec "$DB_CONTAINER" createdb -U "$DB_USER" "$DB_NAME"

echo "[3/3] Restoring from backup..."
gunzip -c "$BACKUP_FILE" | docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" "$DB_NAME"

echo ""
echo "=========================================="
echo "  Restore Complete!"
echo "=========================================="
