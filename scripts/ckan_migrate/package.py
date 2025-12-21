import logging


log = logging.getLogger(__name__)


def import_packages(old_packages, new_db, valid_users_ids=None):
    """ Get all old packages from CSV and import them
        Return a list of errors and warnings for the general log
    """
    log.info("Importing packages...")
    ret = {
        'total_rows': 0,
        'migrated_rows': 0,
        'skipped_rows': 0,
        'warnings': [],
        'errors': [],
        'valid_packages_ids': [],
    }

    # Handle potential duplicate names
    names_in_use = []
    for package in old_packages:
        ret['total_rows'] += 1
        log.info(f"Importing package: {package['name']}")
        new_package = transform_package(package)
        if not new_package:
            log.warning(f" - Skipping package {package['name']}.")
            ret['skipped_rows'] += 1
            continue

        if new_package['name'] in names_in_use:
            # Add a suffix to the name
            original_name = new_package['name']
            new_package['name'] = f"{original_name}_{hash(package['id'])}"
            ret['errors'].append(
                f" - Package '{original_name}' has a duplicate name."
                f" New name: {new_package['name']} (old: {original_name})"
            )

        if valid_users_ids and new_package['creator_user_id'] not in valid_users_ids:
            ret['errors'].append(
                f" - Package '{new_package['name']}' ignored, has a creator_user_id '{new_package['creator_user_id']}'"
                " that does not exist in the new database. Setting it to None."
            )
            ret['skipped_rows'] += 1
            continue

        fields = new_package.keys()
        placeholders = ', '.join(['%s'] * len(fields))
        # Check if the package ID exists
        sql = 'SELECT * FROM "package" WHERE id = %s'
        new_db.cursor.execute(sql, (package["id"],))
        if new_db.cursor.fetchone():
            log.warning(f" - Package {package['name']} already exists, updating the record")
            sql = f'UPDATE "package" SET ({", ".join(fields)}) = ({placeholders}) WHERE id= %s'
            new_db.cursor.execute(sql, tuple(new_package[field] for field in fields) + (package["id"],))
        else:
            sql = f'INSERT INTO "package" ({", ".join(fields)}) VALUES ({placeholders})'
            new_db.cursor.execute(sql, tuple(new_package[field] for field in fields))
        log.info(f" - Package {package['name']} imported successfully.")
        names_in_use.append(new_package['name'])
        ret['migrated_rows'] += 1
        ret['valid_packages_ids'].append(new_package['id'])

    new_db.conn.commit()
    return ret


def transform_package(package, migrate_deleted=True):
    """ Get an old db object and return a dict for the new DB object
        Old packages looks like:
          {
            "id":"package-id",
            "name":"package-name",
            "title":"Package Title",
            "version":"1.0",
            "url":"http://example.com",
            "notes":"Package description",
            "license_id":"cc-by",
            "revision_id":"revision-id",  # DEPRECATED - removed in new CKAN
            "author":"Author Name",
            "author_email":"author@example.com",
            "maintainer":"Maintainer Name",
            "maintainer_email":"maintainer@example.com",
            "state":"active",
            "type":"dataset",
            "owner_org":"org-id",
            "private":false,
            "metadata_modified":"2017-03-21 18:23:56.055936",
            "creator_user_id":"user-id",
            "metadata_created":"2017-03-21 18:23:56.055936"
        },
    """
    if not migrate_deleted and package['state'] == 'deleted':
        return None

    new_package = {
        'id': package['id'],
        'name': package['name'],
        'title': package['title'],
        'version': package['version'],
        'url': package['url'],
        'notes': package['notes'],
        'license_id': package['license_id'],
        'author': package['author'],
        'author_email': package['author_email'],
        'maintainer': package['maintainer'],
        'maintainer_email': package['maintainer_email'],
        'state': package['state'],
        'type': package['type'],
        'owner_org': package['owner_org'],
        'private': package['private'],
        'metadata_modified': package['metadata_modified'],
        'creator_user_id': package['creator_user_id'],
        'metadata_created': package['metadata_created']
    }

    # Note: revision_id is deprecated in new CKAN - we skip it
    # Note: plugin_data is a new field in CKAN 2.11 but we don't have data for it

    return new_package
