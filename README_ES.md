# CKAN Migrator (ES)

Herramienta para migrar instancias **CKAN antiguas** a versiones nuevas, permitiendo extraer y transferir datos desde una base PostgreSQL vieja a otra más reciente.  

Incluye:
- Exportación completa de datos y estructura (CSV/JSON).
- Migración de entidades clave (`users`, `organizations`, `groups`).
- Soporte para extender la migración a más tablas (`tags`, `packages`, `resources`, etc.).

## 📦 Preparación

### 1. Importar la base de datos vieja

Colocar tu dump en:

```
docker/dump/db.dump
```

Levantar los contenedores:

```bash
cd docker
docker compose up -d
```

Restaurar el dump en `postgres-old`:

```bash
docker compose exec postgres-old     pg_restore --verbose --clean     --if-exists --no-owner --no-acl     --dbname=old_ckan_db     --username=postgres     /dump/db.dump
```

Esto deja lista la DB **`old_ckan_db`** en el puerto `9133`.

---

### 2. Configurar el entorno de migración

```bash
cd scripts
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Dependencias principales:
- `psycopg2-binary`
- `pandas`
- `numpy`

---

## ⚙️ Modos de uso

### 1. Exportar todos los datos del CKAN viejo (solo lectura)

```bash
python migrate.py --mode all
```

Esto genera:

- **`database_report.md`** → Reporte completo de tablas, filas y columnas.
- **`tables_info.json`** → Metadata estructural de todas las tablas.
- **`extracted_data/`** → CSV + JSON de cada tabla.

---

### 2. Exportar solo la estructura (sin datos)

```bash
python migrate.py --mode structure
```

---

### 3. Migración hacia una nueva base CKAN

Ejemplo con un CKAN nuevo corriendo en el puerto **8012**:

```bash
python migrate.py --mode migrate   --new-host localhost   --new-port 8012   --new-dbname ckan_test   --new-user ckan_default   --new-password pass
```

---

## 🔀 Pasos de migración

El parámetro `--steps` define qué entidades migrar.  
Por defecto: `users,organizations,groups`

### Migrar usuarios

```bash
python migrate.py --mode migrate --steps users ...
```

### Migrar organizaciones

```bash
python migrate.py --mode migrate --steps organizations ...
```

### Migrar grupos

```bash
python migrate.py --mode migrate --steps groups ...
```

### Migrar múltiples pasos

```bash
python migrate.py --mode migrate --steps users,organizations,groups ...
```

---

## 🧩 Extender con nuevos módulos

Cada entidad migrada se implementa en un archivo dentro de `scripts/ckan_migrate/`.  
Ejemplos actuales:
- `user.py` → migración de usuarios
- `organization.py` → migración de organizaciones
- `groups.py` → migración de grupos

Para agregar nuevas tablas (ej. `tags`):
1. Crear `tags.py` en `scripts/ckan_migrate/`.
2. Implementar `import_tags(old_db, new_db)`.
3. Importar en `migrate.py` y habilitar en `--steps`.

---

## 📝 Notas importantes

- Algunas fechas corruptas en bases viejas pueden generar warnings de pandas (`Overflow in npy_datetimestruct_to_datetime`). El script las maneja y genera JSON de *fallback*.
- La migración está pensada para CKAN ≥2.11 en destino.
- Es recomendable correr primero `--mode all` para inspeccionar los datos exportados.

---

## ✅ Estado actual

- Exportación completa funcionando.
- Migración parcial (`users`, `organizations`, `groups`) implementada.
- Listo para extender hacia `tags`, `packages`, `resources`.
