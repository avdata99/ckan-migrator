#!/usr/bin/env python3
"""
Compare file dates and checksums between backup and remote/local CKAN.

Shows:
- File modification dates
- File sizes
- MD5 checksums
- Which files changed and when

Usage:
    python compare_file_dates.py \
      --remote-url https://datosgestionabierta.cba.gov.ar \
      --backup-dir Back_up_original/var/lib/ckan/datosgestionabierta/resources
"""

import argparse
import os
import hashlib
import json
from datetime import datetime
import requests
import time


def get_file_info(filepath):
    """Get file info: size, mtime, MD5."""
    if not os.path.exists(filepath):
        return None
    
    stat = os.stat(filepath)
    mtime = datetime.fromtimestamp(stat.st_mtime).isoformat()
    size = stat.st_size
    
    # Calculate MD5
    md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            md5.update(chunk)
    
    return {
        'size': size,
        'mtime': mtime,
        'md5': md5.hexdigest(),
        'exists': True
    }


def get_all_resource_files(backup_dir):
    """Get all resource files from backup directory."""
    resources = {}
    
    if not os.path.exists(backup_dir):
        print(f"Backup directory not found: {backup_dir}")
        return resources
    
    for root, dirs, files in os.walk(backup_dir):
        for file in files:
            filepath = os.path.join(root, file)
            resource_id = os.path.basename(root)
            
            if resource_id not in resources:
                resources[resource_id] = {
                    'files': {},
                    'paths': []
                }
            
            filename = os.path.basename(filepath)
            resources[resource_id]['files'][filename] = get_file_info(filepath)
            resources[resource_id]['paths'].append(filepath)
    
    return resources


def get_remote_resource_files(remote_url, api_key=None):
    """Get all resources from remote CKAN API with download info."""
    headers = {}
    if api_key:
        headers['X-CKAN-API-Key'] = api_key
    
    print(f"  Fetching resources from {remote_url}...")
    resources = {}
    page = 1
    
    try:
        while True:
            r = requests.get(f"{remote_url}/api/3/action/package_search",
                           params={'rows': 100, 'start': (page-1)*100},
                           headers=headers, timeout=30)
            r.raise_for_status()
            
            results = r.json().get('result', {}).get('results', [])
            if not results:
                break
            
            for pkg in results:
                for res in pkg.get('resources', []):
                    resource_id = res.get('id')
                    
                    if resource_id not in resources:
                        resources[resource_id] = {
                            'package_name': pkg.get('name'),
                            'resource_name': res.get('name'),
                            'size': res.get('size'),
                            'url': res.get('url'),
                            'format': res.get('format'),
                            'last_modified': res.get('last_modified'),
                            'created': res.get('created'),
                        }
            
            page += 1
            time.sleep(0.1)
    
    except Exception as e:
        print(f"  Error: {e}")
    
    return resources


def get_local_api_resource_files(local_url, api_key=None):
    """Get all resources from local CKAN API."""
    headers = {}
    if api_key:
        headers['X-CKAN-API-Key'] = api_key
    
    print(f"  Fetching resources from {local_url}...")
    resources = {}
    page = 1
    
    try:
        while True:
            r = requests.get(f"{local_url}/api/3/action/package_search",
                           params={'rows': 100, 'start': (page-1)*100},
                           headers=headers, timeout=30)
            r.raise_for_status()
            
            results = r.json().get('result', {}).get('results', [])
            if not results:
                break
            
            for pkg in results:
                for res in pkg.get('resources', []):
                    resource_id = res.get('id')
                    
                    if resource_id not in resources:
                        resources[resource_id] = {
                            'package_name': pkg.get('name'),
                            'resource_name': res.get('name'),
                            'size': res.get('size'),
                            'url': res.get('url'),
                            'format': res.get('format'),
                            'last_modified': res.get('last_modified'),
                            'created': res.get('created'),
                        }
            
            page += 1
            time.sleep(0.1)
    
    except Exception as e:
        print(f"  Error: {e}")
    
    return resources


def main():
    parser = argparse.ArgumentParser(
        description='Compare file dates and checksums between backup and remote'
    )
    parser.add_argument('--backup-dir', required=True,
                       help='Local backup resources directory')
    parser.add_argument('--remote-url', default=None,
                       help='Remote CKAN URL for API comparison')
    parser.add_argument('--local-url', default='http://localhost:5000',
                       help='Local CKAN API URL for comparison')
    parser.add_argument('--output', default='file_dates_comparison.json',
                       help='Output JSON file')
    parser.add_argument('--api-key', default=None)
    
    args = parser.parse_args()
    
    print(f"\n{'='*70}")
    print(f"{'FILE DATES AND CHECKSUMS COMPARISON':^70}")
    print(f"{'='*70}\n")
    
    # Get backup files
    print("Step 1: Reading backup files...")
    backup_files = get_all_resource_files(args.backup_dir)
    print(f"  ✓ Found {len(backup_files)} resource directories with files")
    
    # Get local API metadata
    print("\nStep 2: Fetching local API resource metadata...")
    local_api = get_local_api_resource_files(args.local_url, args.api_key)
    print(f"  ✓ Found {len(local_api)} resources in local CKAN")
    
    # Get remote API metadata if provided
    remote_api = {}
    if args.remote_url:
        print("\nStep 3: Fetching remote API resource metadata...")
        remote_api = get_remote_resource_files(args.remote_url, args.api_key)
        print(f"  ✓ Found {len(remote_api)} resources in remote CKAN")
    
    # Compare
    print("\nStep 4: Comparing files and dates...")
    
    comparison = {
        'timestamp': datetime.now().isoformat(),
        'backup_dir': args.backup_dir,
        'backup_file_count': len(backup_files),
        'local_api_resources': len(local_api),
        'files_in_backup_only': [],
        'files_different_dates': [],
        'files_same': []
    }
    
    # Check each resource in backup
    for resource_id, backup_info in backup_files.items():
        local_res = local_api.get(resource_id, {})
        remote_res = remote_api.get(resource_id, {}) if remote_api else {}
        
        # Skip if no files in this resource
        if not backup_info['files']:
            continue
        
        # Aggregate backup file info
        backup_total_size = sum(f['size'] for f in backup_info['files'].values() if f)
        backup_total_md5 = hashlib.md5(
            ''.join(f['md5'] for f in sorted(backup_info['files'].values(), 
                  key=lambda x: str(x)) if f).encode()
        ).hexdigest()
        
        backup_mtime = max(f['mtime'] for f in backup_info['files'].values() if f) if backup_info['files'] else None
        
        comparison_item = {
            'resource_id': resource_id,
            'resource_name': local_res.get('resource_name') or remote_res.get('resource_name'),
            'package_name': local_res.get('package_name') or remote_res.get('package_name'),
            'backup': {
                'files_count': len(backup_info['files']),
                'total_size': backup_total_size,
                'latest_mtime': backup_mtime,
                'combined_md5': backup_total_md5,
            }
        }
        
        # Local API info
        if local_res:
            comparison_item['local_api'] = {
                'size': local_res.get('size'),
                'last_modified': local_res.get('last_modified'),
                'created': local_res.get('created'),
            }
            
            # Check if dates match
            if local_res.get('last_modified') and backup_mtime:
                local_date = local_res.get('last_modified')[:10]  # YYYY-MM-DD
                backup_date = backup_mtime[:10]
                
                if local_date == backup_date:
                    comparison['files_same'].append(comparison_item)
                else:
                    comparison_item['date_diff'] = f"{backup_date} (backup) vs {local_date} (local)"
                    comparison['files_different_dates'].append(comparison_item)
        
        # Remote API info
        if remote_res:
            comparison_item['remote_api'] = {
                'size': remote_res.get('size'),
                'last_modified': remote_res.get('last_modified'),
                'created': remote_res.get('created'),
            }
        
        if resource_id not in [x['resource_id'] for x in comparison['files_same'] + 
                                comparison['files_different_dates']]:
            comparison['files_in_backup_only'].append(comparison_item)
    
    # Save report
    with open(args.output, 'w') as f:
        json.dump(comparison, f, indent=2)
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"{'RESULTS':^70}")
    print(f"{'='*70}\n")
    
    print(f"Backup file count:      {len(backup_files)}")
    print(f"Local API resources:    {len(local_api)}")
    print(f"Remote API resources:   {len(remote_api) if remote_api else 'N/A'}")
    
    print(f"\nFile Status:")
    print(f"  ✓ Same dates:         {len(comparison['files_same'])}")
    print(f"  ⚠️  Different dates:    {len(comparison['files_different_dates'])}")
    print(f"  ❌ Only in backup:     {len(comparison['files_in_backup_only'])}")
    
    if comparison['files_different_dates']:
        print(f"\n⚠️  FILES WITH DIFFERENT DATES:")
        for item in comparison['files_different_dates'][:10]:
            print(f"\n  [{item['resource_id']}] {item['resource_name']}")
            print(f"    Package: {item['package_name']}")
            print(f"    {item.get('date_diff', 'N/A')}")
            if 'backup' in item:
                print(f"    Backup:     {item['backup']['total_size']} bytes, modified: {item['backup']['latest_mtime']}")
            if 'local_api' in item:
                print(f"    Local API:  {item['local_api'].get('size')} bytes, modified: {item['local_api'].get('last_modified')}")
            if 'remote_api' in item:
                print(f"    Remote API: {item['remote_api'].get('size')} bytes, modified: {item['remote_api'].get('last_modified')}")
        
        if len(comparison['files_different_dates']) > 10:
            print(f"\n  ... and {len(comparison['files_different_dates'])-10} more")
    
    print(f"\n✓ Full report saved to: {args.output}")


if __name__ == '__main__':
    main()
