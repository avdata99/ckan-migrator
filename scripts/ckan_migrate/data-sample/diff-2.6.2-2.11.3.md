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
   - ❌ **Will be dropped**: This table is completely removed in CKAN 2.11.3

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
    - ⚠️ **Deprecated fields**: `revision_id` (removed in new CKAN)
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

### Tables No Longer Required (Skip These)
❌ **Completely Removed Tables** - These tables exist in old CKAN but not in new CKAN:

#### Authorization System (Removed)
- **authorization_group** Authorization system was removed
- **authorization_group_user** Authorization system was removed

#### Revision System (Removed in CKAN 2.11.3)
- **revision** (6,230 rows) - Revision tracking system completely removed
- **package_revision** (1,135 rows) - Package revision history removed
- **resource_revision** (7,518 rows) - Resource revision history removed
- **package_extra_revision** (1,230 rows) - Package extra revision history removed
- **package_tag_revision** (629 rows) - Package tag revision history removed
- **member_revision** (1,585 rows) - Member revision history removed
- **group_revision** (273 rows) - Group revision history removed
- **group_extra_revision** (6 rows) - Group extra revision history removed
- **system_info_revision** (38 rows) - System info revision history removed
- **package_relationship_revision** (0 rows) - Package relationship revision history removed

#### Legacy Migration
- **migrate_version** (1 row) - Old migration metadata, replaced by alembic, Do not import

### Empty/Legacy Tables (Optional - Low Priority)
These tables contain no data or are legacy but still exist in new CKAN:
21. **package_relationship** (0 rows)
22. **rating** (0 rows)
23. **term_translation** (0 rows)
24. **tracking_raw** (0 rows)
25. **tracking_summary** (0 rows) This is built by the raw data, do not import

### New Tables in CKAN 2.11 (Will be created automatically)
These tables exist in the new CKAN but not in the old one:
- **api_token** - API token management
- **package_member** - Package membership system
- **announcements** - Site announcements
- **jobs**, **logs**, **metadata** - Background job system
- **tracking_usage** - Enhanced tracking
- Multiple **alembic_version** tables - Migration management

### Summary of Changes
- **12 tables completely removed**: All revision tables + authorization tables + migrate_version
- **1 field removed from user**: openid
- **revision_id fields removed** from main tables (revision system completely removed)
- **webstore fields removed** from resource table
- **Several new tables added** for enhanced functionality

### ⚠️ Important Migration Notes

1. **Revision System Removal**: CKAN 2.11.3 completely removes the revision tracking system. All `revision_id` fields in main tables should be ignored during migration.

2. **No Historical Data**: Since revision tables are completely removed, historical change tracking will be lost in the migration. Only current data from main tables will be preserved.

3. **Activity System**: The activity table is now the primary way CKAN tracks changes, replacing the old revision system.

**Migration Strategy:** 
- Import only the main tables (user, group, package, resource, etc.)
- Skip all `*_revision` tables entirely
- Remove `revision_id` fields from transforms
- Skip the `revision` table itself
- This significantly reduces migration complexity and data volume
