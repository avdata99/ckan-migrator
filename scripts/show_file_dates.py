#!/usr/bin/env python3
"""
Quick file dates comparison - minimal size output.
Shows which files in backup changed compared to production.
"""

import os
import hashlib
from datetime import datetime

backup_dir = "../Back_up_original/var/lib/ckan/datosgestionabierta/resources"

print("\n" + "="*70)
print("ANÁLISIS DE FECHAS DE ARCHIVOS EN BACKUP")
print("="*70 + "\n")

if not os.path.exists(backup_dir):
    print(f"❌ Directorio no encontrado: {backup_dir}")
    exit(1)

# Collect file info
file_stats = {}
total_size = 0
total_files = 0

for root, dirs, files in os.walk(backup_dir):
    for file in files:
        filepath = os.path.join(root, file)
        stat = os.stat(filepath)
        mtime = datetime.fromtimestamp(stat.st_mtime)
        
        if 'dates' not in file_stats:
            file_stats['dates'] = {}
        
        date_key = mtime.strftime('%Y-%m-%d')
        if date_key not in file_stats['dates']:
            file_stats['dates'][date_key] = {'count': 0, 'size': 0, 'files': []}
        
        file_stats['dates'][date_key]['count'] += 1
        file_stats['dates'][date_key]['size'] += stat.st_size
        file_stats['dates'][date_key]['files'].append({
            'name': os.path.basename(filepath),
            'size': stat.st_size,
            'mtime': mtime.isoformat()
        })
        
        total_files += 1
        total_size += stat.st_size

print(f"📁 Archivos encontrados: {total_files}")
print(f"📊 Tamaño total: {total_size / (1024*1024):.2f} MB\n")

# Show by date
print("Archivos por fecha de modificación:")
print("-" * 70)

for date in sorted(file_stats['dates'].keys(), reverse=True):
    info = file_stats['dates'][date]
    size_mb = info['size'] / (1024*1024)
    print(f"\n📅 {date}: {info['count']} archivos ({size_mb:.2f} MB)")
    
    for f in sorted(info['files'], key=lambda x: x['size'], reverse=True)[:3]:
        print(f"   • {f['name'][:50]:50} {f['size']:>12} bytes")
    
    if len(info['files']) > 3:
        print(f"   ... + {len(info['files'])-3} más")

print("\n" + "="*70)
print("CONCLUSIÓN:")
print("="*70)

# Find oldest and newest files
dates = list(file_stats['dates'].keys())
dates_sorted = sorted(dates)

if dates_sorted:
    oldest = dates_sorted[0]
    newest = dates_sorted[-1]
    oldest_count = file_stats['dates'][oldest]['count']
    newest_count = file_stats['dates'][newest]['count']
    
    print(f"\n✓ Archivos más antiguos: {oldest} ({oldest_count} archivos)")
    print(f"✓ Archivos más nuevos:  {newest} ({newest_count} archivos)")
    
    if oldest != newest:
        print(f"\n📌 RANGO DE FECHAS: ~{oldest} a ~{newest}")
    else:
        print(f"\n📌 Todos los archivos de la misma fecha: {oldest}")
