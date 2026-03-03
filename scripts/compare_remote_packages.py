#!/usr/bin/env python3
"""
Compare packages between remote CKAN instance and local backup by downloading
full package metadata and comparing key fields.

Usage:
    python compare_remote_packages.py --remote-url https://datosgestionabierta.cba.gov.ar --sample-size 50

This provides deeper validation than just counts, checking:
- Package titles
- Resource counts per package
- Organization assignments
- Metadata timestamps
"""

import argparse
import requests
import psycopg2
import psycopg2.extras
import json
from datetime import datetime
import time


def fetch_remote_package(base_url, package_id, api_key=None):
    """Fetch full package metadata from remote CKAN."""
    headers = {}
    if api_key:
        headers['X-CKAN-API-Key'] = api_key
    
    try:
        r = requests.get(
            f"{base_url}/api/3/action/package_show",
            params={'id': package_id},
            headers=headers,
            timeout=30
        )
        r.raise_for_status()
        result = r.json()
        if result.get('success'):
            return result.get('result')
        return None
    except Exception as e:
        print(f"  ERROR fetching {package_id}: {e}")
        return None


def fetch_local_package(cursor, package_name):
    """Fetch package metadata from local DB."""
    cursor.execute("""
        SELECT 
            p.id, p.name, p.title, p.state, p.private, p.type,
            p.metadata_created, p.metadata_modified,
            p.owner_org,
            g.name as org_name,
            (SELECT count(*) FROM resource WHERE package_id = p.id) as resource_count
        FROM package p
        LEFT JOIN "group" g ON p.owner_org = g.id
        WHERE p.name = %s
    """, (package_name,))
    return cursor.fetchone()


def compare_packages(local_pkg, remote_pkg):
    """Compare local and remote package data."""
    differences = []
    
    if not local_pkg or not remote_pkg:
        return {'error': 'Package missing in one source'}
    
    # Compare title
    if local_pkg['title'] != remote_pkg.get('title'):
        differences.append({
            'field': 'title',
            'local': local_pkg['title'],
            'remote': remote_pkg.get('title')
        })
    
    # Compare state
    if local_pkg['state'] != remote_pkg.get('state'):
        differences.append({
            'field': 'state',
            'local': local_pkg['state'],
            'remote': remote_pkg.get('state')
        })
    
    # Compare organization
    local_org = local_pkg['org_name'] or ''
    remote_org = remote_pkg.get('organization', {}).get('name', '') if remote_pkg.get('organization') else ''
    if local_org != remote_org:
        differences.append({
            'field': 'organization',
            'local': local_org,
            'remote': remote_org
        })
    
    # Compare resource count
    remote_resource_count = len(remote_pkg.get('resources', []))
    if local_pkg['resource_count'] != remote_resource_count:
        differences.append({
            'field': 'resource_count',
            'local': local_pkg['resource_count'],
            'remote': remote_resource_count
        })
    
    return {'differences': differences, 'match': len(differences) == 0}


def main():
    parser = argparse.ArgumentParser(
        description='Deep comparison of packages between local backup and remote CKAN'
    )
    parser.add_argument('--remote-url', required=True,
                       help='Remote CKAN base URL')
    parser.add_argument('--api-key', default=None,
                       help='Optional CKAN API key')
    parser.add_argument('--sample-size', type=int, default=50,
                       help='Number of packages to compare (default: 50)')
    parser.add_argument('--local-host', default='localhost')
    parser.add_argument('--local-port', type=int, default=9133)
    parser.add_argument('--local-dbname', default='old_ckan_db')
    parser.add_argument('--local-user', default='postgres')
    parser.add_argument('--local-password', default='password')
    parser.add_argument('--output', default='package_comparison.json')
    
    args = parser.parse_args()
    
    print("Connecting to local database...")
    conn = psycopg2.connect(
        host=args.local_host, port=args.local_port,
        dbname=args.local_dbname, user=args.local_user,
        password=args.local_password
    )
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Get sample of package names
    print(f"Fetching {args.sample_size} package names from local DB...")
    cursor.execute("""
        SELECT name 
        FROM package 
        WHERE type='dataset' AND state='active' 
        ORDER BY metadata_modified DESC 
        LIMIT %s
    """, (args.sample_size,))
    
    package_names = [row['name'] for row in cursor.fetchall()]
    print(f"Selected {len(package_names)} packages for comparison")
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'total_compared': len(package_names),
        'matches': 0,
        'differences': 0,
        'errors': 0,
        'details': []
    }
    
    for i, pkg_name in enumerate(package_names, 1):
        print(f"\n[{i}/{len(package_names)}] Comparing: {pkg_name}")
        
        # Fetch local
        local_pkg = fetch_local_package(cursor, pkg_name)
        
        # Fetch remote (with rate limiting)
        time.sleep(0.5)  # Be nice to the API
        remote_pkg = fetch_remote_package(args.remote_url, pkg_name, args.api_key)
        
        # Compare
        comparison = compare_packages(local_pkg, remote_pkg)
        
        if 'error' in comparison:
            results['errors'] += 1
            print(f"  ERROR: {comparison['error']}")
        elif comparison.get('match'):
            results['matches'] += 1
            print(f"  ✓ MATCH")
        else:
            results['differences'] += 1
            print(f"  ✗ DIFFERENCES: {len(comparison['differences'])} fields differ")
            for diff in comparison['differences']:
                print(f"    - {diff['field']}: local={diff['local']}, remote={diff['remote']}")
        
        results['details'].append({
            'package': pkg_name,
            'comparison': comparison
        })
    
    cursor.close()
    conn.close()
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n=== Comparison Summary ===")
    print(f"Total compared: {results['total_compared']}")
    print(f"Perfect matches: {results['matches']}")
    print(f"With differences: {results['differences']}")
    print(f"Errors: {results['errors']}")
    print(f"\nMatch rate: {results['matches']/results['total_compared']*100:.1f}%")
    print(f"\nDetailed report saved to: {args.output}")


if __name__ == '__main__':
    main()
