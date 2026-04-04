#!/bin/bash
# =============================================================
# Database Backup Script for School Management System
# =============================================================
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_CONTAINER="${DB_CONTAINER:-school_db}"
DB_NAME="${DB_NAME:-school_system_db}"
DB_USER="${DB_USER:-school_admin}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

echo "=========================================="
echo "  Database Backup - $TIMESTAMP"
echo "=========================================="

# Create backup directory
mkdir -p "$BACKUP_DIR"

BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "[1/3] Creating database dump..."
docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "  Backup saved: $BACKUP_FILE ($BACKUP_SIZE)"

echo ""
echo "[2/3] Verifying backup integrity..."
if gzip -t "$BACKUP_FILE" 2>/dev/null; then
    echo "  Backup integrity: OK"
else
    echo "  ERROR: Backup file is corrupted!"
    exit 1
fi

echo ""
echo "[3/3] Cleaning old backups (older than $RETENTION_DAYS days)..."
DELETED=$(find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
echo "  Removed $DELETED old backup(s)"

echo ""
echo "=========================================="
echo "  Backup Complete!"
echo "=========================================="
echo "  File: $BACKUP_FILE"
echo "  Size: $BACKUP_SIZE"
echo ""
echo "  To restore: ./scripts/restore.sh $BACKUP_FILE"
echo "=========================================="
