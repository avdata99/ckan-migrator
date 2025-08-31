"""
We have a really old PSQL instance running on docker (port 9133).
This Python script allows you to connect and extract all tables information
and data.
"""

import argparse
import logging
import psycopg2.extras
from db import PSQL
from ckan_migrate.user import import_users
from ckan_migrate.group import import_groups
from ckan_migrate.vocabulary import import_vocabularies
from ckan_migrate.tag import import_tags
from ckan_migrate.package import import_packages
from ckan_migrate.resource import import_resources
from ckan_migrate.package_extra import import_package_extras
from ckan_migrate.package_tag import import_package_tags
from ckan_migrate.member import import_members
from ckan_migrate.group_extra import import_group_extras
from ckan_migrate.resource_view import import_resource_views
from ckan_migrate.activity import import_activities
from ckan_migrate.activity_detail import import_activity_details
from ckan_migrate.dashboard import import_dashboards
from ckan_migrate.system_info import import_system_info
from ckan_migrate.task_status import import_task_status
from ckan_migrate.user_following_group import import_user_following_groups
from ckan_migrate.user_following_dataset import import_user_following_datasets
from ckan_migrate.package_relationship import import_package_relationships
from ckan_migrate.rating import import_ratings

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

    parser.add_argument(
        '--mode', choices=['migrate', 'structure', 'all'], default='migrate', help='Migration mode (default: migrate)'
    )

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

    # sample
    # python migrate.py --mode migrate --new-host localhost --new-port 8012 --new-dbname ckan_test \
    #   --new-user ckan_default --new-password pass
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
        print("Old database structure extracted successfully.")

        # Check if new database parameters are provided for structure comparison
        if any([args.new_host != 'localhost', args.new_port != 5432, args.new_dbname != 'ckan',
                args.new_user != 'ckan', args.new_password != 'password']):
            new_db = PSQL(
                host=args.new_host,
                port=args.new_port,
                dbname=args.new_dbname,
                user=args.new_user,
                password=args.new_password
            )

            if new_db.connect():
                new_db.cursor = new_db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                print("New database connection established.")
                new_db.extract_all_data(save_data=False, filename_prefix="new_")
                print("New database structure extracted successfully.")
                new_db.disconnect()
            else:
                print("Failed to connect to new database for structure analysis.")

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
    final_logs = {}
    final_logs['users'] = import_users(old_db, new_db)
    final_logs['groups'] = import_groups(old_db, new_db)
    final_logs['vocabularies'] = import_vocabularies(old_db, new_db)
    final_logs['tags'] = import_tags(old_db, new_db)
    final_logs['packages'] = import_packages(old_db, new_db)
    final_logs['resources'] = import_resources(old_db, new_db)
    final_logs['package_extras'] = import_package_extras(old_db, new_db)
    final_logs['package_tags'] = import_package_tags(old_db, new_db)
    final_logs['members'] = import_members(old_db, new_db)
    final_logs['group_extras'] = import_group_extras(old_db, new_db)
    final_logs['resource_views'] = import_resource_views(old_db, new_db)
    final_logs['activities'] = import_activities(old_db, new_db)
    final_logs['activity_details'] = import_activity_details(old_db, new_db)
    final_logs['dashboards'] = import_dashboards(old_db, new_db)
    final_logs['system_info'] = import_system_info(old_db, new_db)
    final_logs['task_status'] = import_task_status(old_db, new_db)
    final_logs['user_following_groups'] = import_user_following_groups(old_db, new_db)
    final_logs['user_following_datasets'] = import_user_following_datasets(old_db, new_db)
    final_logs['package_relationships'] = import_package_relationships(old_db, new_db)
    final_logs['ratings'] = import_ratings(old_db, new_db)

    print(f'Migration finished: {final_logs}')


if __name__ == "__main__":
    main()
