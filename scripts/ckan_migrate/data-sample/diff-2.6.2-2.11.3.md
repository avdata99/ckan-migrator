# Migration sample

To import from CKAN 2.6.2 to CKAN 2.11.3 this is diff and proposed migration order.  

## Suggested Import Order

Based on foreign key dependencies and table relationships, the following order is recommended for migration:

### Core Tables (Import First)
1. **user** Independent table, referenced by many others
   - ⚠️ **Deprecated fields**: `openid` (removed in new CKAN)
   - ✅ **New fields**: `plugin_extras`, `image_url`, `last_active`

2. **group** Independent table for organizations/groups
   - ⚠️ **Deprecated fields**: `revision_id` (removed in new CKAN)

3. **vocabulary** Referenced by tags

4. **tag** Uses vocabulary_id

5. **revision** Referenced by most versioned tables

### Primary Content Tables
6. **package** Core datasets, references user (creator_user_id) and group (owner_org)
   - ⚠️ **Deprecated fields**: `revision_id` (removed in new CKAN)
   - ✅ **New fields**: `plugin_data`

7. **resource** Belongs to packages
   - ⚠️ **Deprecated fields**: `revision_id`, `webstore_url`, `webstore_last_updated` (removed in new CKAN)
   - ✅ **New fields**: `metadata_modified`

8. **package_extra** Additional package metadata
   - ⚠️ **Deprecated fields**: `revision_id` (removed in new CKAN)

### Relationship Tables
9. **package_tag** Links packages to tags
   - ⚠️ **Deprecated fields**: `revision_id` (removed in new CKAN)

10. **member** Links packages/users to groups
    - ⚠️ **Deprecated fields**: `revision_id` (removed in new CKAN)

11. **group_extra** Additional group metadata
    - ⚠️ **Deprecated fields**: `revision_id` (removed in new CKAN)

### View and Activity Tables
12. **resource_view** Visualization configs for resources

13. **activity** Activity stream, references users and objects
    - ✅ **New fields**: `permission_labels`

14. **activity_detail** Activity details, references activities

### User Experience Tables
15. **dashboard** User dashboard settings

16. **system_info** System configuration
    - ⚠️ **Deprecated fields**: `revision_id` (removed in new CKAN)

17. **task_status** Background task status

18. **user_following_group** User follows relationships

19. **user_following_dataset** User follows relationships

20. **user_following_user** User follows relationships

### Revision Tables (Import after main tables)
These tables store historical versions and should be imported after their main counterparts:

21. **package_revision** (1,135 rows)
22. **resource_revision** (7,518 rows)
23. **package_extra_revision** (1,230 rows)
24. **package_tag_revision** (629 rows)
25. **member_revision** (1,585 rows)
26. **group_revision** (273 rows)
27. **group_extra_revision** (6 rows)
28. **system_info_revision** (38 rows)

### Tables No Longer Required (Skip These)
❌ **Completely Removed Tables** - These tables exist in old CKAN but not in new CKAN:
- **authorization_group** Authorization system was removed
- **authorization_group_user** Authorization system was removed
- **migrate_version** (1 row) - Old migration metadata, replaced by alembic

### Empty/Legacy Tables (Optional - Low Priority)
These tables contain no data or are legacy but still exist in new CKAN:
29. **package_relationship** (0 rows)
30. **package_relationship_revision** (0 rows)
31. **rating** (0 rows)
32. **term_translation** (0 rows)
33. **tracking_raw** (0 rows)
34. **tracking_summary** (0 rows)

### New Tables in CKAN 2.11 (Will be created automatically)
These tables exist in the new CKAN but not in the old one:
- **api_token** - API token management
- **package_member** - Package membership system
- **announcements** - Site announcements
- **jobs**, **logs**, **metadata** - Background job system
- **tracking_usage** - Enhanced tracking
- Multiple **alembic_version** tables - Migration management

### Summary of Changes
- **3 tables completely removed**: authorization_group, authorization_group_user, migrate_version
- **1 field removed from user**: openid
- **revision_id fields removed** from main tables (moved to revision tables only)
- **webstore fields removed** from resource table
- **Several new tables added** for enhanced functionality

**Note:** Start with tables that have no foreign key dependencies and work your way up to tables that reference other tables. Always import revision tables after their corresponding main tables to maintain referential integrity. Skip completely removed tables to avoid errors.
