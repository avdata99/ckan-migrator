"""
We have a really old PSQL instance running on docker (port 9133).
This Python script allows you to connect and extract all tables information
and data.
"""

import argparse
import logging
import psycopg2.extras
from db import PSQL
from ckan_migrate import import_users, import_groups

# Configure logging to output to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)


def parse_args():
    """
    Parse command line arguments for database connection.
    """
    parser = argparse.ArgumentParser(
        description=(
            'CKAN Database Migrator\n'
            'Extract data from old CKAN PostgreSQL database and migrate to new database\n'
            'The "mode" parameter defines if you want to migrate to a new CKAN DB instance '
            'or just extract the old database data or structure.\n'
        )
    )

    parser.add_argument('--mode', choices=['migrate', 'structure', 'all'], default='migrate',
                        help='Migration mode (default: migrate)')

    parser.add_argument('--old-host', default='localhost', help='Old database host (default: localhost)')
    parser.add_argument('--old-port', type=int, default=9133, help='Old database port (default: 9133)')
    parser.add_argument('--old-dbname', default='old_ckan_db', help='Old database name (default: old_ckan_db)')
    parser.add_argument('--old-user', default='postgres', help='Old database user (default: postgres)')
    parser.add_argument('--old-password', default='password', help='Old database password (default: password)')

    parser.add_argument('--new-host', default='localhost', help='New database host (default: localhost)')
    parser.add_argument('--new-port', type=int, default=5432, help='New database port (default: 5432)')
    parser.add_argument('--new-dbname', default='ckan', help='New database name (default: ckan)')
    parser.add_argument('--new-user', default='ckan', help='New database user (default: ckan)')
    parser.add_argument('--new-password', default='password', help='New database password (default: password)')

    parser.add_argument(
        '--steps',
        default='users,organizations,groups',
        help='Comma-separated steps to run in migrate mode. Options: users,organizations,groups'
    )

    # sample
    # python migrate.py --mode migrate --new-host localhost --new-port 8012 --new-dbname ckan_test
    # --new-user ckan_default --new-password pass
    return parser.parse_args()


def main():
    """
    Main function to run the database extraction.
    """
    args = parse_args()

    print("CKAN Database Migrator")
    print("======================")
    print(f"Connecting to OLD_DB: {args.old_user}@{args.old_host}:{args.old_port}/{args.old_dbname}")
    # Create old_db instance with provided arguments
    old_db = PSQL(
        host=args.old_host,
        port=args.old_port,
        dbname=args.old_dbname,
        user=args.old_user,
        password=args.old_password
    )
    # Test connection first
    if not old_db.connect():
        print("Failed to connect to database.")
        return

    # Configure cursor to return dictionaries
    old_db.cursor = old_db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    print("Old database connection established.")

    # Handle extraction mode
    if args.mode == 'structure':
        old_db.extract_all_data(save_data=False)
        print("Database structure extracted successfully.")
        return
    elif args.mode == 'all':
        old_db.extract_all_data(save_data=True)
        print("All database data extracted successfully.")
        return

    # The user wants to migrate to a new db
    print(f"Connecting to NEW_DB: {args.new_user}@{args.new_host}:{args.new_port}/{args.new_dbname}")
    # Create new_db instance with provided arguments
    new_db = PSQL(
        host=args.new_host,
        port=args.new_port,
        dbname=args.new_dbname,
        user=args.new_user,
        password=args.new_password
    )

    if not new_db.connect():
        print("Failed to connect to the new database.")
        return

    # Configure cursor to return dictionaries
    new_db.cursor = new_db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    print("New database connection established.")

    # Capture all logs for all migrations
    allowed_steps = {'users', 'organizations', 'groups'}
    steps = [s.strip().lower() for s in (args.steps or '').split(',') if s.strip()]
    unknown = [s for s in steps if s not in allowed_steps]
    if unknown:
        raise ValueError(f"Unknown steps: {unknown}. Allowed: {sorted(allowed_steps)}")

    final_logs = {}

    # Ejecuta y falla temprano si algo sale mal; no atrapamos excepciones aquí
    try:
        if 'users' in steps:
            final_logs['users'] = import_users(old_db, new_db)
            print("Users migrated.")

        if 'groups' in steps:
            # import_groups ya migra organizaciones & grupos
            final_logs['groups_orgs'] = import_groups(old_db, new_db)
            print("Organizations & Groups migrated.")
    finally:
        try:
            if new_db and new_db.conn:
                new_db.disconnect()
        finally:
            if old_db and old_db.conn:
                old_db.disconnect()

    print(f"Migration finished: {final_logs}")

if __name__ == "__main__":
    main()
