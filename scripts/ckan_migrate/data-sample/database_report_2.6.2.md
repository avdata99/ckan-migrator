# CKAN Database Analysis Report

Generated on: 2025-08-31 15:05:09
Database: old_ckan_db
Total tables: 37

## Tables Summary

### activity
- Rows: 16,094
- Columns: 7

**Columns:**
- `id` (text) NOT NULL
- `timestamp` (timestamp without time zone) NULL
- `user_id` (text) NULL
- `object_id` (text) NULL
- `revision_id` (text) NULL
- `activity_type` (text) NULL
- `data` (text) NULL

### activity_detail
- Rows: 32,576
- Columns: 6

**Columns:**
- `id` (text) NOT NULL
- `activity_id` (text) NULL
- `object_id` (text) NULL
- `object_type` (text) NULL
- `activity_type` (text) NULL
- `data` (text) NULL

### authorization_group
- Rows: 0
- Columns: 3

**Columns:**
- `id` (text) NOT NULL
- `name` (text) NULL
- `created` (timestamp without time zone) NULL

### authorization_group_user
- Rows: 0
- Columns: 3

**Columns:**
- `authorization_group_id` (text) NOT NULL
- `user_id` (text) NOT NULL
- `id` (text) NOT NULL

### dashboard
- Rows: 13
- Columns: 3

**Columns:**
- `user_id` (text) NOT NULL
- `activity_stream_last_viewed` (timestamp without time zone) NOT NULL
- `email_last_sent` (timestamp without time zone) NOT NULL

### group
- Rows: 88
- Columns: 11

**Columns:**
- `id` (text) NOT NULL
- `name` (text) NOT NULL
- `title` (text) NULL
- `description` (text) NULL
- `created` (timestamp without time zone) NULL
- `state` (text) NULL
- `revision_id` (text) NULL
- `type` (text) NOT NULL
- `approval_status` (text) NULL
- `image_url` (text) NULL
- `is_organization` (boolean) NULL

### group_extra
- Rows: 6
- Columns: 6

**Columns:**
- `id` (text) NOT NULL
- `group_id` (text) NULL
- `key` (text) NULL
- `value` (text) NULL
- `state` (text) NULL
- `revision_id` (text) NULL

### group_extra_revision
- Rows: 6
- Columns: 11

**Columns:**
- `id` (text) NOT NULL
- `group_id` (text) NULL
- `key` (text) NULL
- `value` (text) NULL
- `state` (text) NULL
- `revision_id` (text) NOT NULL
- `continuity_id` (text) NULL
- `expired_id` (text) NULL
- `revision_timestamp` (timestamp without time zone) NULL
- `expired_timestamp` (timestamp without time zone) NULL
- `current` (boolean) NULL

### group_revision
- Rows: 273
- Columns: 16

**Columns:**
- `id` (text) NOT NULL
- `name` (text) NOT NULL
- `title` (text) NULL
- `description` (text) NULL
- `created` (timestamp without time zone) NULL
- `state` (text) NULL
- `revision_id` (text) NOT NULL
- `continuity_id` (text) NULL
- `expired_id` (text) NULL
- `revision_timestamp` (timestamp without time zone) NULL
- `expired_timestamp` (timestamp without time zone) NULL
- `current` (boolean) NULL
- `type` (text) NOT NULL
- `approval_status` (text) NULL
- `image_url` (text) NULL
- `is_organization` (boolean) NULL

### member
- Rows: 1,013
- Columns: 7

**Columns:**
- `id` (text) NOT NULL
- `table_id` (text) NOT NULL
- `group_id` (text) NULL
- `state` (text) NULL
- `revision_id` (text) NULL
- `table_name` (text) NOT NULL
- `capacity` (text) NOT NULL

### member_revision
- Rows: 1,585
- Columns: 12

**Columns:**
- `id` (text) NOT NULL
- `table_id` (text) NOT NULL
- `group_id` (text) NULL
- `state` (text) NULL
- `revision_id` (text) NOT NULL
- `continuity_id` (text) NULL
- `expired_id` (text) NULL
- `revision_timestamp` (timestamp without time zone) NULL
- `expired_timestamp` (timestamp without time zone) NULL
- `current` (boolean) NULL
- `table_name` (text) NOT NULL
- `capacity` (text) NOT NULL

### migrate_version
- Rows: 1
- Columns: 3

**Columns:**
- `repository_id` (character varying) NOT NULL
- `repository_path` (text) NULL
- `version` (integer) NULL

### package
- Rows: 296
- Columns: 19

**Columns:**
- `id` (text) NOT NULL
- `name` (character varying) NOT NULL
- `title` (text) NULL
- `version` (character varying) NULL
- `url` (text) NULL
- `notes` (text) NULL
- `license_id` (text) NULL
- `revision_id` (text) NULL
- `author` (text) NULL
- `author_email` (text) NULL
- `maintainer` (text) NULL
- `maintainer_email` (text) NULL
- `state` (text) NULL
- `type` (text) NULL
- `owner_org` (text) NULL
- `private` (boolean) NULL
- `metadata_modified` (timestamp without time zone) NULL
- `creator_user_id` (text) NULL
- `metadata_created` (timestamp without time zone) NULL

### package_extra
- Rows: 731
- Columns: 6

**Columns:**
- `id` (text) NOT NULL
- `package_id` (text) NULL
- `key` (text) NULL
- `value` (text) NULL
- `revision_id` (text) NULL
- `state` (text) NULL

### package_extra_revision
- Rows: 1,230
- Columns: 11

**Columns:**
- `id` (text) NOT NULL
- `package_id` (text) NULL
- `key` (text) NULL
- `value` (text) NULL
- `revision_id` (text) NOT NULL
- `continuity_id` (text) NULL
- `state` (text) NULL
- `expired_id` (text) NULL
- `revision_timestamp` (timestamp without time zone) NULL
- `expired_timestamp` (timestamp without time zone) NULL
- `current` (boolean) NULL

### package_relationship
- Rows: 0
- Columns: 7

**Columns:**
- `id` (text) NOT NULL
- `subject_package_id` (text) NULL
- `object_package_id` (text) NULL
- `type` (text) NULL
- `comment` (text) NULL
- `revision_id` (text) NULL
- `state` (text) NULL

### package_relationship_revision
- Rows: 0
- Columns: 12

**Columns:**
- `id` (text) NOT NULL
- `subject_package_id` (text) NULL
- `object_package_id` (text) NULL
- `type` (text) NULL
- `comment` (text) NULL
- `revision_id` (text) NOT NULL
- `continuity_id` (text) NULL
- `state` (text) NULL
- `expired_id` (text) NULL
- `revision_timestamp` (timestamp without time zone) NULL
- `expired_timestamp` (timestamp without time zone) NULL
- `current` (boolean) NULL

### package_revision
- Rows: 1,135
- Columns: 24

**Columns:**
- `id` (text) NOT NULL
- `name` (character varying) NOT NULL
- `title` (text) NULL
- `version` (character varying) NULL
- `url` (text) NULL
- `notes` (text) NULL
- `license_id` (text) NULL
- `revision_id` (text) NOT NULL
- `continuity_id` (text) NULL
- `author` (text) NULL
- `author_email` (text) NULL
- `maintainer` (text) NULL
- `maintainer_email` (text) NULL
- `state` (text) NULL
- `expired_id` (text) NULL
- `revision_timestamp` (timestamp without time zone) NULL
- `expired_timestamp` (timestamp without time zone) NULL
- `current` (boolean) NULL
- `type` (text) NULL
- `owner_org` (text) NULL
- `private` (boolean) NULL
- `metadata_modified` (timestamp without time zone) NULL
- `creator_user_id` (text) NULL
- `metadata_created` (timestamp without time zone) NULL

### package_tag
- Rows: 459
- Columns: 5

**Columns:**
- `id` (text) NOT NULL
- `package_id` (text) NULL
- `tag_id` (text) NULL
- `revision_id` (text) NULL
- `state` (text) NULL

### package_tag_revision
- Rows: 629
- Columns: 10

**Columns:**
- `id` (text) NOT NULL
- `package_id` (text) NULL
- `tag_id` (text) NULL
- `revision_id` (text) NOT NULL
- `continuity_id` (text) NULL
- `state` (text) NULL
- `expired_id` (text) NULL
- `revision_timestamp` (timestamp without time zone) NULL
- `expired_timestamp` (timestamp without time zone) NULL
- `current` (boolean) NULL

### rating
- Rows: 0
- Columns: 6

**Columns:**
- `id` (text) NOT NULL
- `user_id` (text) NULL
- `user_ip_address` (text) NULL
- `package_id` (text) NULL
- `rating` (double precision) NULL
- `created` (timestamp without time zone) NULL

### resource
- Rows: 1,814
- Columns: 22

**Columns:**
- `id` (text) NOT NULL
- `url` (text) NOT NULL
- `format` (text) NULL
- `description` (text) NULL
- `position` (integer) NULL
- `revision_id` (text) NULL
- `hash` (text) NULL
- `state` (text) NULL
- `extras` (text) NULL
- `name` (text) NULL
- `resource_type` (text) NULL
- `mimetype` (text) NULL
- `mimetype_inner` (text) NULL
- `size` (bigint) NULL
- `last_modified` (timestamp without time zone) NULL
- `cache_url` (text) NULL
- `cache_last_updated` (timestamp without time zone) NULL
- `webstore_url` (text) NULL
- `webstore_last_updated` (timestamp without time zone) NULL
- `created` (timestamp without time zone) NULL
- `url_type` (text) NULL
- `package_id` (text) NOT NULL

### resource_revision
- Rows: 7,518
- Columns: 27

**Columns:**
- `id` (text) NOT NULL
- `url` (text) NOT NULL
- `format` (text) NULL
- `description` (text) NULL
- `position` (integer) NULL
- `revision_id` (text) NOT NULL
- `continuity_id` (text) NULL
- `hash` (text) NULL
- `state` (text) NULL
- `extras` (text) NULL
- `expired_id` (text) NULL
- `revision_timestamp` (timestamp without time zone) NULL
- `expired_timestamp` (timestamp without time zone) NULL
- `current` (boolean) NULL
- `name` (text) NULL
- `resource_type` (text) NULL
- `mimetype` (text) NULL
- `mimetype_inner` (text) NULL
- `size` (bigint) NULL
- `last_modified` (timestamp without time zone) NULL
- `cache_url` (text) NULL
- `cache_last_updated` (timestamp without time zone) NULL
- `webstore_url` (text) NULL
- `webstore_last_updated` (timestamp without time zone) NULL
- `created` (timestamp without time zone) NULL
- `url_type` (text) NULL
- `package_id` (text) NOT NULL

### resource_view
- Rows: 116
- Columns: 7

**Columns:**
- `id` (text) NOT NULL
- `resource_id` (text) NULL
- `title` (text) NULL
- `description` (text) NULL
- `view_type` (text) NOT NULL
- `order` (integer) NOT NULL
- `config` (text) NULL

### revision
- Rows: 6,230
- Columns: 6

**Columns:**
- `id` (text) NOT NULL
- `timestamp` (timestamp without time zone) NULL
- `author` (character varying) NULL
- `message` (text) NULL
- `state` (text) NULL
- `approved_timestamp` (timestamp without time zone) NULL

### system_info
- Rows: 9
- Columns: 5

**Columns:**
- `id` (integer) NOT NULL
- `key` (character varying) NOT NULL
- `value` (text) NULL
- `revision_id` (text) NULL
- `state` (text) NOT NULL

### system_info_revision
- Rows: 38
- Columns: 10

**Columns:**
- `id` (integer) NOT NULL
- `key` (character varying) NOT NULL
- `value` (text) NULL
- `revision_id` (text) NOT NULL
- `continuity_id` (integer) NULL
- `state` (text) NOT NULL
- `expired_id` (text) NULL
- `revision_timestamp` (timestamp without time zone) NULL
- `expired_timestamp` (timestamp without time zone) NULL
- `current` (boolean) NULL

### tag
- Rows: 271
- Columns: 3

**Columns:**
- `id` (text) NOT NULL
- `name` (character varying) NOT NULL
- `vocabulary_id` (character varying) NULL

### task_status
- Rows: 530
- Columns: 9

**Columns:**
- `id` (text) NOT NULL
- `entity_id` (text) NOT NULL
- `entity_type` (text) NOT NULL
- `task_type` (text) NOT NULL
- `key` (text) NOT NULL
- `value` (text) NOT NULL
- `state` (text) NULL
- `error` (text) NULL
- `last_updated` (timestamp without time zone) NULL

### term_translation
- Rows: 0
- Columns: 3

**Columns:**
- `term` (text) NOT NULL
- `term_translation` (text) NOT NULL
- `lang_code` (text) NOT NULL

### tracking_raw
- Rows: 0
- Columns: 4

**Columns:**
- `user_key` (character varying) NOT NULL
- `url` (text) NOT NULL
- `tracking_type` (character varying) NOT NULL
- `access_timestamp` (timestamp without time zone) NULL

### tracking_summary
- Rows: 0
- Columns: 7

**Columns:**
- `url` (text) NOT NULL
- `package_id` (text) NULL
- `tracking_type` (character varying) NOT NULL
- `count` (integer) NOT NULL
- `running_total` (integer) NOT NULL
- `recent_views` (integer) NOT NULL
- `tracking_date` (date) NULL

### user
- Rows: 22
- Columns: 13

**Columns:**
- `id` (text) NOT NULL
- `name` (text) NOT NULL
- `apikey` (text) NULL
- `created` (timestamp without time zone) NULL
- `about` (text) NULL
- `openid` (text) NULL
- `password` (text) NULL
- `fullname` (text) NULL
- `email` (text) NULL
- `reset_key` (text) NULL
- `sysadmin` (boolean) NULL
- `activity_streams_email_notifications` (boolean) NULL
- `state` (text) NOT NULL

### user_following_dataset
- Rows: 0
- Columns: 3

**Columns:**
- `follower_id` (text) NOT NULL
- `object_id` (text) NOT NULL
- `datetime` (timestamp without time zone) NOT NULL

### user_following_group
- Rows: 1
- Columns: 3

**Columns:**
- `follower_id` (text) NOT NULL
- `object_id` (text) NOT NULL
- `datetime` (timestamp without time zone) NOT NULL

### user_following_user
- Rows: 0
- Columns: 3

**Columns:**
- `follower_id` (text) NOT NULL
- `object_id` (text) NOT NULL
- `datetime` (timestamp without time zone) NOT NULL

### vocabulary
- Rows: 0
- Columns: 2

**Columns:**
- `id` (text) NOT NULL
- `name` (character varying) NOT NULL


## Summary Statistics
- Total rows across all tables: 72,684
- Average rows per table: 1,964