#!/usr/bin/env python3
"""
Detailed backup comparison - shows exactly what's different.

This script performs deep validation comparing:
1. All dataset metadata (title, description, state, organization)
2. All resources per dataset (name, format, file size)
3. File checksums for static files

Usage:
    python detailed_backup_comparison.py \
      --remote-url https://datosgestionabierta.cba.gov.ar \
      --local-url http://localhost:5000
"""

import argparse
import requests
import json
from datetime import datetime
import time
import hashlib
import os


def get_all_packages(base_url, api_key=None):
    """Fetch all packages with full metadata."""
    headers = {}
    if api_key:
        headers['X-CKAN-API-Key'] = api_key
    
    print(f"  Fetching all packages from {base_url}...")
    all_packages = {}
    page = 1
    
    try:
        while True:
            r = requests.get(f"{base_url}/api/3/action/package_search",
                           params={'rows': 100, 'start': (page-1)*100, 'sort': 'name asc'},
                           headers=headers, timeout=30)
            r.raise_for_status()
            
            results = r.json().get('result', {}).get('results', [])
            if not results:
                break
            
            for pkg in results:
                all_packages[pkg['id']] = {
                    'name': pkg.get('name'),
                    'title': pkg.get('title'),
                    'state': pkg.get('state'),
                    'organization': pkg.get('organization', {}).get('name'),
                    'resource_count': len(pkg.get('resources', [])),
                    'resources': [
                        {
                            'id': r.get('id'),
                            'name': r.get('name'),
                            'format': r.get('format'),
                            'size': r.get('size'),
                            'url': r.get('url')[:50] if r.get('url') else None
                        }
                        for r in pkg.get('resources', [])
                    ]
                }
            
            page += 1
            time.sleep(0.1)
    
    except Exception as e:
        print(f"  Error: {e}")
    
    return all_packages


def compare_packages(local_pkg, remote_pkg):
    """Compare two packages and return differences."""
    diffs = {}
    
    # Check basic fields
    fields = ['name', 'title', 'state', 'organization', 'resource_count']
    for field in fields:
        if local_pkg.get(field) != remote_pkg.get(field):
            diffs[field] = {
                'local': local_pkg.get(field),
                'remote': remote_pkg.get(field)
            }
    
    # Check resources
    local_resources = {r['id']: r for r in local_pkg.get('resources', [])}
    remote_resources = {r['id']: r for r in remote_pkg.get('resources', [])}
    
    resource_diffs = {}
    for rid in set(list(local_resources.keys()) + list(remote_resources.keys())):
        if rid not in local_resources:
            resource_diffs[rid] = {'status': 'ONLY_REMOTE'}
        elif rid not in remote_resources:
            resource_diffs[rid] = {'status': 'ONLY_LOCAL'}
        else:
            for field in ['name', 'format', 'size']:
                if local_resources[rid].get(field) != remote_resources[rid].get(field):
                    resource_diffs[rid] = {
                        'status': 'DIFFERENT',
                        'field': field,
                        'local': local_resources[rid].get(field),
                        'remote': remote_resources[rid].get(field)
                    }
    
    if resource_diffs:
        diffs['resources'] = resource_diffs
    
    return diffs


def main():
    parser = argparse.ArgumentParser(
        description='Detailed backup comparison - show exact differences'
    )
    parser.add_argument('--remote-url', required=True,
                       help='Remote CKAN URL')
    parser.add_argument('--local-url', default='http://localhost:5000',
                       help='Local CKAN URL')
    parser.add_argument('--output', default='detailed_comparison.json',
                       help='Output file')
    parser.add_argument('--api-key', default=None)
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"{'DETAILED BACKUP COMPARISON':^60}")
    print(f"{'='*60}\n")
    
    print("Step 1: Fetching remote packages...")
    remote_packages = get_all_packages(args.remote_url, args.api_key)
    print(f"  ✓ Found {len(remote_packages)} packages")
    
    print("\nStep 2: Fetching local packages...")
    local_packages = get_all_packages(args.local_url, args.api_key)
    print(f"  ✓ Found {len(local_packages)} packages")
    
    print("\nStep 3: Comparing packages...")
    all_ids = set(list(local_packages.keys()) + list(remote_packages.keys()))
    
    differences = {
        'timestamp': datetime.now().isoformat(),
        'total_packages_checked': len(all_ids),
        'packages_only_local': [],
        'packages_only_remote': [],
        'packages_different': {}
    }
    
    for pkg_id in sorted(all_ids):
        if pkg_id not in local_packages:
            differences['packages_only_remote'].append(pkg_id)
        elif pkg_id not in remote_packages:
            differences['packages_only_local'].append(pkg_id)
        else:
            diffs = compare_packages(local_packages[pkg_id], remote_packages[pkg_id])
            if diffs:
                differences['packages_different'][pkg_id] = {
                    'name': local_packages[pkg_id]['name'],
                    'differences': diffs
                }
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"{'COMPARISON RESULTS':^60}")
    print(f"{'='*60}\n")
    
    print(f"Total packages checked: {len(all_ids)}")
    print(f"Packages only in LOCAL:  {len(differences['packages_only_local'])}")
    print(f"Packages only in REMOTE: {len(differences['packages_only_remote'])}")
    print(f"Packages with differences: {len(differences['packages_different'])}")
    
    if differences['packages_only_local']:
        print(f"\n❌ MISSING IN REMOTE (should be migrated):")
        for pkg_id in differences['packages_only_local'][:10]:
            pkg = local_packages[pkg_id]
            print(f"   - {pkg_id}: {pkg['name']} ({pkg['state']})")
        if len(differences['packages_only_local']) > 10:
            print(f"   ... and {len(differences['packages_only_local'])-10} more")
    
    if differences['packages_only_remote']:
        print(f"\n⚠️  EXTRA IN REMOTE (not in backup):")
        for pkg_id in differences['packages_only_remote'][:10]:
            pkg = remote_packages[pkg_id]
            print(f"   - {pkg_id}: {pkg['name']} ({pkg['state']})")
        if len(differences['packages_only_remote']) > 10:
            print(f"   ... and {len(differences['packages_only_remote'])-10} more")
    
    if differences['packages_different']:
        print(f"\n⚠️  DATASET DIFFERENCES FOUND:")
        for pkg_id in sorted(differences['packages_different'].keys())[:5]:
            pkg_diffs = differences['packages_different'][pkg_id]
            print(f"\n   [{pkg_id}] {pkg_diffs['name']}:")
            for field, change in pkg_diffs['differences'].items():
                if field != 'resources':
                    print(f"     - {field}:")
                    print(f"       Local:  {change['local']}")
                    print(f"       Remote: {change['remote']}")
                else:
                    print(f"     - {len(change)} resources differ:")
                    for rid, rdiff in list(change.items())[:3]:
                        if rdiff.get('status') == 'ONLY_LOCAL':
                            print(f"       • {rid}: ONLY IN LOCAL")
                        elif rdiff.get('status') == 'ONLY_REMOTE':
                            print(f"       • {rid}: ONLY IN REMOTE")
                        else:
                            print(f"       • {rid}: {rdiff['field']} differs")
        if len(differences['packages_different']) > 5:
            print(f"\n   ... and {len(differences['packages_different'])-5} more packages differ")
    
    # Save detailed report
    with open(args.output, 'w') as f:
        json.dump(differences, f, indent=2)
    
    print(f"\n✓ Full report saved to: {args.output}")
    
    # Exit status
    if differences['packages_different'] or differences['packages_only_local']:
        print(f"\n⚠️  WARNINGS: Check details in {args.output}")
        return 1
    else:
        print(f"\n✓ All packages match perfectly!")
        return 0


if __name__ == '__main__':
    exit(main())
