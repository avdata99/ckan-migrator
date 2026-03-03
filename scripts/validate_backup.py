#!/usr/bin/env python3
"""
Validate backup integrity by comparing local CKAN API and remote CKAN instance.

Usage:
    python validate_backup.py --remote-url https://datosgestionabierta.cba.gov.ar

This script compares via API:
- Package counts (datasets)
- Organization/group counts
- Resource counts
- Sample of package IDs and titles
"""

import argparse
import requests
import json
from datetime import datetime
import time


def get_api_stats(base_url, api_key=None):
    """Fetch comprehensive statistics from CKAN API."""
    headers = {}
    if api_key:
        headers['X-CKAN-API-Key'] = api_key
    
    stats = {
        'url': base_url,
        'timestamp': datetime.now().isoformat()
    }
    
    # Package search (count)
    try:
        r = requests.get(f"{base_url}/api/3/action/package_search", 
                        params={'rows': 0}, headers=headers, timeout=30)
        r.raise_for_status()
        stats['packages_total'] = r.json().get('result', {}).get('count', 0)
    except Exception as e:
        stats['packages_total'] = f"ERROR: {str(e)[:60]}"
    
    # Get all packages with details (paginated)
    print(f"  Fetching packages from {base_url}...")
    all_packages = []
    active_packages = 0
    total_resources = 0
    page = 1
    
    try:
        while len(all_packages) < 1000:  # Safely limit pagination
            r = requests.get(f"{base_url}/api/3/action/package_search",
                           params={'rows': 100, 'start': (page-1)*100},
                           headers=headers, timeout=30)
            r.raise_for_status()
            
            results = r.json().get('result', {}).get('results', [])
            if not results:
                break
            
            all_packages.extend(results)
            
            # Count active packages and resources
            for pkg in results:
                if pkg.get('state') == 'active':
                    active_packages += 1
                total_resources += len(pkg.get('resources', []))
            
            page += 1
            time.sleep(0.1)  # Rate limit
            
    except Exception as e:
        print(f"  Warning: Error fetching packages: {e}")
    
    stats['packages_active'] = active_packages
    stats['package_ids_sample'] = [p.get('name', p.get('id')) for p in all_packages[:20]]
    stats['resources_total'] = total_resources
    
    # Organizations
    try:
        r = requests.get(f"{base_url}/api/3/action/organization_list",
                        params={}, headers=headers, timeout=30)
        r.raise_for_status()
        orgs = r.json().get('result', [])
        stats['organizations_total'] = len(orgs)
        stats['organizations_sample'] = [o.get('name', o.get('id')) for o in orgs[:5]]
    except Exception as e:
        stats['organizations_total'] = f"ERROR: {str(e)[:60]}"
        stats['organizations_sample'] = []
    
    # Groups
    try:
        r = requests.get(f"{base_url}/api/3/action/group_list",
                        params={}, headers=headers, timeout=30)
        r.raise_for_status()
        groups = r.json().get('result', [])
        stats['groups_total'] = len(groups)
        stats['groups_sample'] = [g.get('name', g.get('id')) for g in groups[:5]]
    except Exception as e:
        stats['groups_total'] = f"ERROR: {str(e)[:60]}"
        stats['groups_sample'] = []
    
    return stats


def compare_stats(local, remote):
    """Compare local and remote statistics."""
    comparison = {
        'timestamp': datetime.now().isoformat(),
        'differences': []
    }
    
    # Compare package counts
    if isinstance(local.get('packages_total'), int) and isinstance(remote.get('packages_total'), int):
        if local['packages_total'] != remote['packages_total']:
            comparison['differences'].append({
                'field': 'packages_total',
                'local': local['packages_total'],
                'remote': remote['packages_total']
            })
    
    # Compare active packages
    if isinstance(local.get('packages_active'), int) and isinstance(remote.get('packages_active'), int):
        if local['packages_active'] != remote['packages_active']:
            comparison['differences'].append({
                'field': 'packages_active',
                'local': local['packages_active'],
                'remote': remote['packages_active']
            })
    
    # Compare organizations
    if isinstance(local.get('organizations_total'), int) and isinstance(remote.get('organizations_total'), int):
        if local['organizations_total'] != remote['organizations_total']:
            comparison['differences'].append({
                'field': 'organizations',
                'local': local['organizations_total'],
                'remote': remote['organizations_total']
            })
    
    # Compare groups
    if isinstance(local.get('groups_total'), int) and isinstance(remote.get('groups_total'), int):
        if local['groups_total'] != remote['groups_total']:
            comparison['differences'].append({
                'field': 'groups',
                'local': local['groups_total'],
                'remote': remote['groups_total']
            })
    
    # Compare resource counts
    if isinstance(local.get('resources_total'), int) and isinstance(remote.get('resources_total'), int):
        if local['resources_total'] != remote['resources_total']:
            comparison['differences'].append({
                'field': 'resources',
                'local': local['resources_total'],
                'remote': remote['resources_total']
            })
    
    # Compare sample IDs
    local_ids = set(local.get('package_ids_sample', []))
    remote_ids = set(remote.get('package_ids_sample', []))
    
    if local_ids and remote_ids:
        common_ids = local_ids & remote_ids
        comparison['sample_match'] = {
            'common_count': len(common_ids),
            'local_only_count': len(local_ids - remote_ids),
            'remote_only_count': len(remote_ids - local_ids),
            'local_only_sample': list(local_ids - remote_ids)[:5],
            'remote_only_sample': list(remote_ids - local_ids)[:5],
            'common_sample': list(common_ids)[:5]
        }
    
    return comparison


def main():
    parser = argparse.ArgumentParser(
        description='Validate backup by comparing local CKAN API vs remote CKAN API'
    )
    parser.add_argument('--remote-url', required=True,
                       help='Remote CKAN base URL (e.g., https://datosgestionabierta.cba.gov.ar)')
    parser.add_argument('--local-url', default='http://localhost:5000',
                       help='Local CKAN base URL (default: http://localhost:5000)')
    parser.add_argument('--local-host', default='localhost',
                       help='(Deprecated) Local DB host')
    parser.add_argument('--local-port', type=int, default=9133,
                       help='(Deprecated) Local DB port')
    parser.add_argument('--local-dbname', default='old_ckan_db',
                       help='(Deprecated) Local DB name')
    parser.add_argument('--local-user', default='postgres',
                       help='(Deprecated) Local DB user')
    parser.add_argument('--local-password', default='password',
                       help='(Deprecated) Local DB password')
    parser.add_argument('--api-key', default=None,
                       help='Optional CKAN API key for authenticated requests')
    parser.add_argument('--output', default='backup_validation.json',
                       help='Output JSON file (default: backup_validation.json)')
    
    args = parser.parse_args()
    
    print(f"Fetching remote API statistics from {args.remote_url}...")
    remote_stats = get_api_stats(args.remote_url, args.api_key)
    
    print(f"Fetching local API statistics from {args.local_url}...")
    local_stats = get_api_stats(args.local_url, args.api_key)
    
    print("Comparing statistics...")
    comparison = compare_stats(local_stats, remote_stats)
    
    # Build final report
    report = {
        'local': local_stats,
        'remote': remote_stats,
        'comparison': comparison
    }
    
    # Save to file
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"{'Backup Validation Report':^50}")
    print(f"{'='*50}")
    print(f"\nLocal API:  {local_stats.get('url')}")
    print(f"Remote API: {remote_stats.get('url')}")
    
    print(f"\nLocal Statistics:")
    print(f"  - Total packages:   {local_stats.get('packages_total')}")
    print(f"  - Active packages:  {local_stats.get('packages_active')}")
    orgs_local = local_stats.get('organizations_total')
    if isinstance(orgs_local, int):
        print(f"  - Organizations:    {orgs_local}")
    groups_local = local_stats.get('groups_total')
    if isinstance(groups_local, int):
        print(f"  - Groups:           {groups_local}")
    print(f"  - Total resources:  {local_stats.get('resources_total')}")
    
    print(f"\nRemote Statistics:")
    print(f"  - Total packages:   {remote_stats.get('packages_total')}")
    print(f"  - Active packages:  {remote_stats.get('packages_active')}")
    orgs_remote = remote_stats.get('organizations_total')
    if isinstance(orgs_remote, int):
        print(f"  - Organizations:    {orgs_remote}")
    groups_remote = remote_stats.get('groups_total')
    if isinstance(groups_remote, int):
        print(f"  - Groups:           {groups_remote}")
    print(f"  - Total resources:  {remote_stats.get('resources_total')}")
    
    differences = comparison.get('differences', [])
    print(f"\nDifferences Found: {len(differences)}")
    if differences:
        for diff in differences:
            print(f"  [{diff['field']}] Local: {diff['local']}, Remote: {diff['remote']}")
    else:
        print("  ✓ All counts match!")
    
    if 'sample_match' in comparison:
        sm = comparison['sample_match']
        print(f"\nSample Dataset ID Comparison (first 20):")
        print(f"  - Matching IDs:     {sm['common_count']}")
        print(f"  - Local only:       {sm['local_only_count']}")
        print(f"  - Remote only:      {sm['remote_only_count']}")
        if sm['common_count'] > 0:
            print(f"  - Sample matches:   {sm['common_sample']}")
    
    print(f"\nFull report saved to: {args.output}")


if __name__ == '__main__':
    main()
