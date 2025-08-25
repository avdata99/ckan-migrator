DROP TABLE IF EXISTS "user" CASCADE;
DROP TABLE IF EXISTS "group" CASCADE;

CREATE TABLE "user"(
  id uuid PRIMARY KEY,
  name text UNIQUE,
  fullname text,
  email text,
  about text,
  created timestamp,
  sysadmin boolean default false,
  state text
);

CREATE TABLE "group"(
  id uuid PRIMARY KEY,
  name text UNIQUE,
  title text,
  description text,
  created timestamp,
  state text,
  type text,
  approval_status text,
  image_url text,
  is_organization boolean
);
