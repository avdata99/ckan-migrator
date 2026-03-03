#!/bin/bash
#
# Validate static files integrity by comparing checksums
#
# Usage:
#   ./validate_files.sh /path/to/backup/resources /path/to/backup/uploads
#
# This script:
# 1. Generates checksums for local resources and uploads
# 2. Can be compared with remote server checksums via rsync --dry-run or manual transfer
#

set -e

BACKUP_BASE=${1:-"Back_up_original/var/lib/ckan/datosgestionabierta"}
OUTPUT_DIR="file_validation"

mkdir -p "$OUTPUT_DIR"

echo "=== File Validation Tool ==="
echo "Backup base: $BACKUP_BASE"
echo ""

# Generate checksums for resources
if [ -d "$BACKUP_BASE/resources" ]; then
    echo "Generating checksums for resources..."
    find "$BACKUP_BASE/resources" -type f -exec md5sum {} \; | sort -k2 > "$OUTPUT_DIR/resources_checksums.txt"
    RESOURCE_COUNT=$(wc -l < "$OUTPUT_DIR/resources_checksums.txt")
    echo "  - Found $RESOURCE_COUNT resource files"
    echo "  - Checksums saved to: $OUTPUT_DIR/resources_checksums.txt"
else
    echo "WARNING: Resources directory not found at $BACKUP_BASE/resources"
fi

echo ""

# Generate checksums for uploads
if [ -d "$BACKUP_BASE/storage/uploads" ]; then
    echo "Generating checksums for uploads..."
    find "$BACKUP_BASE/storage/uploads" -type f -exec md5sum {} \; | sort -k2 > "$OUTPUT_DIR/uploads_checksums.txt"
    UPLOAD_COUNT=$(wc -l < "$OUTPUT_DIR/uploads_checksums.txt")
    echo "  - Found $UPLOAD_COUNT upload files"
    echo "  - Checksums saved to: $OUTPUT_DIR/uploads_checksums.txt"
else
    echo "WARNING: Uploads directory not found at $BACKUP_BASE/storage/uploads"
fi

echo ""
echo "=== Summary ==="
echo "Resource files: ${RESOURCE_COUNT:-0}"
echo "Upload files: ${UPLOAD_COUNT:-0}"
echo ""
echo "To compare with remote server:"
echo "1. Run this script on the server with the same backup structure"
echo "2. Compare the checksum files:"
echo "   diff $OUTPUT_DIR/resources_checksums.txt server_resources_checksums.txt"
echo ""
echo "Alternative: use rsync --dry-run to compare directories:"
echo "   rsync -avnc $BACKUP_BASE/resources/ server:/path/to/ckan/storage/resources/"
echo ""
echo "Files with different checksums will be listed."
