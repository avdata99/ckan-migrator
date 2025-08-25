CREATE TABLE "user"(
  id uuid PRIMARY KEY,
  name text UNIQUE,
  fullname text,
  email text,
  created timestamp,
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
