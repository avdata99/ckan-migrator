"""
We have a really old PSQL instance running on docker (port 9133).
This Python script allows you to connect and extract all tables information
and data.
"""

import argparse
import json
import logging
import os
import pandas as pd
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
from ckan_migrate.term_translation import import_term_translations
from ckan_migrate.tracking_raw import import_tracking_raw


# Configure logging to output to both stdout and file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('migration.log')
    ]
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
        '--mode', choices=['migrate', 'structure', 'extract'], default='migrate', help='Migration mode (default: migrate)'
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


def get_old_db_connection(args):
    """
    Establish connection to the old database.
    """
    print(f"Connecting to OLD_DB: {args.old_user}@{args.old_host}:{args.old_port}/{args.old_dbname}")
    old_db = PSQL(
        host=args.old_host,
        port=args.old_port,
        dbname=args.old_dbname,
        user=args.old_user,
        password=args.old_password
    )
    if not old_db.connect():
        raise ConnectionError("Failed to connect to the old database.")
    print("Old database connection established.")
    old_db.cursor = old_db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return old_db


def load_from_csv(csv_path):
    """ Load CSV files like the ones extracted with extract mode
        and return a list of dicts similar to the ones returned by
        RealDictCursor.
    """
    extracted_data_folder = 'extracted_data'
    csv_path = f"{extracted_data_folder}/{csv_path}"
    if os.path.exists(csv_path) is False:
        print(f"CSV file not found: {csv_path}")
        return []
    df = pd.read_csv(csv_path)

    # Convert DataFrame to list of dicts (similar to RealDictCursor output)
    records = df.to_dict('records')

    # Handle type conversions from CSV strings
    for record in records:
        # Convert ANY boolean strings to actual booleans
        for key, value in record.items():
            if isinstance(value, str):
                if value.lower() == 'true':
                    record[key] = True
                elif value.lower() == 'false':
                    record[key] = False

        # Handle NaN values (pandas represents NULL as NaN)
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None

    return records


def main():
    """
    Main function to run the database extraction.
    """
    args = parse_args()

    print("CKAN Database Migrator")
    print("======================")

    # Handle extraction mode
    if args.mode == 'structure':
        # Just extract the old database structure
        # and optionally compare with new database structure
        old_db = get_old_db_connection(args)
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
    elif args.mode == 'extract':
        # Just extract all data from old database and save to files
        old_db = get_old_db_connection(args)
        old_db.extract_all_data(save_data=True)
        print("All database data extracted successfully.")
        return
    elif args.mode != 'migrate':
        print(f"Unknown mode: {args.mode}")
        return

    f = open('migration.log', 'w')
    f.write("CKAN Database Migrator Log\n")
    f.write("===========================\n\n")

    # The user wants to migrate to a new db
    # We'll use the CSV files extracted previously with extract mode
    print(f"Connecting to NEW_DB: {args.new_user}@{args.new_host}:{args.new_port}/{args.new_dbname}")
    f.write(f"Connecting to NEW_DB: {args.new_user}@{args.new_host}:{args.new_port}/{args.new_dbname}\n")
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
        f.write("Failed to connect to the new database.\n")
        f.close()
        return

    # Configure cursor to return dictionaries
    new_db.cursor = new_db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    print("New database connection established.")
    f.write("New database connection established.\n\n")

    # Capture all logs for all migrations
    final_logs = {}
    final_logs['users'] = import_users(load_from_csv("user.csv"), new_db)
    valid_users_ids = final_logs['users']['valid_users_ids']

    final_logs['groups'] = import_groups(load_from_csv("group.csv"), new_db)
    final_logs['vocabularies'] = import_vocabularies(load_from_csv("vocabulary.csv"), new_db)
    final_logs['tags'] = import_tags(load_from_csv("tag.csv"), new_db)

    # Do not migrate packages with creator_user_id that does not exist in the new DB
    final_logs['packages'] = import_packages(load_from_csv("package.csv"), new_db, valid_users_ids=valid_users_ids)
    valid_packages_ids = final_logs['packages']['valid_packages_ids']
    final_logs['resources'] = import_resources(load_from_csv("resource.csv"), new_db, valid_packages_ids=valid_packages_ids)
    final_logs['package_extras'] = import_package_extras(load_from_csv("package_extra.csv"), new_db)
    final_logs['package_tags'] = import_package_tags(load_from_csv("package_tag.csv"), new_db)
    # Do not migrate members from non valid users
    final_logs['members'] = import_members(load_from_csv("member.csv"), new_db, valid_users_ids=valid_users_ids)
    final_logs['group_extras'] = import_group_extras(load_from_csv("group_extra.csv"), new_db)
    final_logs['resource_views'] = import_resource_views(load_from_csv("resource_view.csv"), new_db)
    final_logs['activities'] = import_activities(load_from_csv("activity.csv"), new_db, valid_users_ids=valid_users_ids)
    valid_activities_ids = final_logs['activities']['valid_activities_ids']
    final_logs['activity_details'] = import_activity_details(load_from_csv("activity_detail.csv"), new_db, valid_activities_ids=valid_activities_ids)

    final_logs['dashboards'] = import_dashboards(load_from_csv("dashboard.csv"), new_db, valid_users_ids=valid_users_ids)
    final_logs['system_info'] = import_system_info(load_from_csv("system_info.csv"), new_db)
    final_logs['task_status'] = import_task_status(load_from_csv("task_status.csv"), new_db)
    final_logs['user_following_groups'] = import_user_following_groups(load_from_csv("user_following_group.csv"), new_db, valid_users_ids=valid_users_ids)
    final_logs['user_following_datasets'] = import_user_following_datasets(load_from_csv("user_following_dataset.csv"), new_db, valid_users_ids=valid_users_ids)
    final_logs['package_relationships'] = import_package_relationships(load_from_csv("package_relationship.csv"), new_db)
    final_logs['ratings'] = import_ratings(load_from_csv("rating.csv"), new_db)
    final_logs['term_translations'] = import_term_translations(load_from_csv("term_translation.csv"), new_db)
    final_logs['tracking_raw'] = import_tracking_raw(load_from_csv("tracking_raw.csv"), new_db)

    f.write('Migration finished\n')
    f.close()

    f = open('migration.log.json', 'w')
    final_logs_nice = json.dumps(final_logs, indent=4)
    f.write(final_logs_nice)
    f.close()

    print(f'Migration finished: {final_logs_nice}')


if __name__ == "__main__":
    main()
