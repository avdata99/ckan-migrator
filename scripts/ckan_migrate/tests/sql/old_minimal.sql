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

/* Datos de ejemplo */
INSERT INTO "user"(id,name,fullname,email,created,state)
VALUES
('00000000-0000-0000-0000-000000000001','admin','Admin','admin@example.com','2010-01-01','active'),
('00000000-0000-0000-0000-000000000002','user1','User 1','u1@example.com','2011-01-01','active');

INSERT INTO "group"(id,name,title,description,created,state,type,approval_status,image_url,is_organization)
VALUES
('10000000-0000-0000-0000-000000000001','planificacion','Planificación','','2012-01-01','active','group','approved','',false),
('20000000-0000-0000-0000-000000000001','min-salud','Ministerio de Salud','','2012-02-01','active','organization','approved','',true);
