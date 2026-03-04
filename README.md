# 📦 s3-file-service

> **S3 File Service — End-to-End Architecture** — A layered FastAPI backend for file uploads, storing objects in AWS S3 and metadata in MySQL via SQLAlchemy ORM.

[![Stack](https://img.shields.io/badge/stack-FastAPI%20%7C%20SQLAlchemy%20%7C%20Boto3-1a56db?style=flat-square)](/)
[![Storage](https://img.shields.io/badge/storage-AWS%20S3%20%2B%20MySQL-0e9f6e?style=flat-square)](/)
[![Pattern](https://img.shields.io/badge/pattern-Router%20→%20Service%20→%20Repository-7c3aed?style=flat-square)](/)
[![Version](https://img.shields.io/badge/version-1.0-yellow?style=flat-square)](/)
[![License: MIT](https://img.shields.io/badge/License-MIT-gray?style=flat-square)](LICENSE)

---

## 📑 Table of Contents

- [Overview](#overview)
- [Architecture Layers](#architecture-layers)
- [End-to-End Runtime Flow](#end-to-end-runtime-flow)
- [Project Structure](#project-structure)
- [Data Model](#data-model)
- [S3 Key Format](#s3-key-format)
- [API Reference](#api-reference)
- [External Dependencies](#external-dependencies)
- [Gaps & Risks](#gaps--risks)
- [Next Implementation Steps](#next-implementation-steps)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)

---

## Overview

`s3-file-service` is a clean, layered **FastAPI** backend for handling file uploads in fintech and enterprise applications.

Uploaded files are persisted as objects in **AWS S3**, while structured metadata (filename, size, owner, path, soft-delete flag, timestamps) is stored in a **MySQL** database via the **SQLAlchemy ORM**.

The codebase is organised into four principal layers — API, Service, Repository, and Data — each with a single, well-defined responsibility. **Alembic** handles schema migrations and **python-dotenv** loads runtime configuration from `.env`.

---

## Architecture Layers

```
┌──────────────────────────────────────────────────────┐
│                   ENTRY LAYER                        │
│   app/main.py                                        │
│   Creates FastAPI app · Registers upload router      │
│   Sets global middleware / CORS                      │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│                   API LAYER                          │
│   app/api/v1/s3_routes.py                            │
│   POST /api/v1/files/upload                          │
│   Accepts user_id · module_name · file               │
│   Injects DB session via Depends(get_db)             │
│   Delegates to FileService                           │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│                SERVICE LAYER                         │
│   app/services/file_service.py                       │
│   Validates file size vs MAX_FILE_SIZE               │
│   Builds S3 key · Uploads via S3Repository           │
│   Persists metadata via FileRepository               │
└────────────┬──────────────────────┬──────────────────┘
             │                      │
┌────────────▼──────────┐  ┌────────▼──────────────────┐
│   REPOSITORY LAYER    │  │   REPOSITORY LAYER         │
│   FileRepository      │  │   S3Repository             │
│   file_repository.py  │  │   s3_repository.py         │
│   insert · fetch ·    │  │   upload · delete ·        │
│   soft delete         │  │   presigned URL            │
└────────────┬──────────┘  └────────┬──────────────────┘
             │                      │
┌────────────▼──────────┐  ┌────────▼──────────────────┐
│   MySQL               │  │   AWS S3                   │
│   files table         │  │   Object Storage           │
└───────────────────────┘  └────────────────────────────┘
```

---

## End-to-End Runtime Flow

```
Client
    │
    │  POST /api/v1/files/upload
    │  multipart: user_id · module_name · file
    ▼
FastAPI Router
    │  parse request · inject DB session via Depends(get_db)
    ▼
FileService.upload_file(user_id, module_name, file)
    │
    ├─► Seek to EOF → measure stream size
    │       │
    │       ├── size > MAX_FILE_SIZE?  →  raise HTTP 413
    │       └── OK  →  reset stream seek(0)
    │
    ├─► Extract file extension
    │
    ├─► Build S3 key:
    │       S3_service/{year}/{month}/{user_id}/{module_name}/{filename}
    │
    ├─► S3Repository.upload_file(stream, bucket, key)
    │       └── boto3.upload_fileobj → AWS S3  →  success / ETag
    │
    ├─► Build File ORM entity (all metadata fields)
    │
    ├─► FileRepository.create(file_obj)
    │       └── db.add → db.commit → db.refresh → persisted row
    │
    └─► Serialise via FileResponse Pydantic schema
            │
            ▼
    HTTP 200 JSON  →  Client
```

---

## Project Structure

```
s3-file-service/
│
├── README.md
│
├── app/
│   ├── main.py                          ← FastAPI app entry point
│   │
│   ├── api/
│   │   └── v1/
│   │       └── s3_routes.py             ← Upload router & endpoint
│   │
│   ├── services/
│   │   └── file_service.py              ← Business logic, orchestration
│   │
│   ├── repositories/
│   │   ├── file_repository.py           ← MySQL CRUD operations
│   │   └── s3_repository.py             ← AWS S3 operations
│   │
│   ├── models/
│   │   └── file.py                      ← SQLAlchemy ORM model
│   │
│   ├── schemas/
│   │   └── file_schema.py               ← Pydantic request/response schemas
│   │
│   ├── core/
│   │   ├── config.py                    ← Loads .env configuration
│   │   └── database.py                  ← SQLAlchemy engine & SessionLocal
│   │
│   └── dependencies.py                  ← get_db() session generator ⚠️ (to be created)
│
├── alembic/
│   ├── env.py                           ← Migration environment config
│   ├── alembic.ini                      ← Alembic configuration
│   └── versions/                        ← Migration revision files
│
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Data Model

### `files` table (MySQL via SQLAlchemy ORM)

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | INT PK AUTO_INCREMENT | No | Auto-incrementing primary key |
| `user_id` | INT | No | Owner user identifier |
| `module_name` | VARCHAR | No | Source module / context (e.g. `invoices`) |
| `filenames` | VARCHAR | No | Original uploaded filename |
| `extension` | VARCHAR | Yes | File extension (e.g. `pdf`, `png`) |
| `size` | BIGINT | Yes | File size in bytes |
| `s3_path` | TEXT | No | Full S3 object key path |
| `bucket_name` | VARCHAR | No | Target S3 bucket name |
| `is_deleted` | BOOLEAN | No | Soft-delete flag (default `FALSE`) |
| `created_at` | DATETIME | No | Row creation timestamp (UTC) |
| `updated_at` | DATETIME | No | Last update timestamp (UTC) |

---

## S3 Key Format

Object keys follow a structured, date-partitioned path:

```
S3_service/{year}/{month}/{user_id}/{module_name}/{original_filename}
```

**Example:**

```
S3_service/2025/06/42/invoices/receipt_q2.pdf
```

---

## API Reference

### `POST /api/v1/files/upload`

Upload a file to S3 and persist its metadata to MySQL.

**Request** — `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `user_id` | integer | Yes | ID of the uploading user |
| `module_name` | string | Yes | Source module context (e.g. `invoices`, `kyc`) |
| `file` | binary | Yes | File content (multipart upload) |

**Response** — `HTTP 200 OK`

```json
{
  "id": 1,
  "user_id": 42,
  "module_name": "invoices",
  "filenames": "receipt_q2.pdf",
  "extension": "pdf",
  "size": 204800,
  "s3_path": "S3_service/2025/06/42/invoices/receipt_q2.pdf",
  "bucket_name": "my-app-files",
  "created_at": "2025-06-15T10:32:00Z"
}
```

**Error responses**

| Code | Condition |
|---|---|
| `413 Payload Too Large` | File exceeds `MAX_FILE_SIZE` |
| `500 Internal Server Error` | S3 upload failure or DB commit failure |

---

## External Dependencies

```
fastapi
uvicorn
sqlalchemy
pymysql
alembic
boto3
python-dotenv
pydantic
python-multipart   # required for multipart uploads
cryptography       # required by pymysql
```

> `python-multipart` and `cryptography` are implicit FastAPI/pymysql requirements — add them explicitly to `requirements.txt`.

Install:

```bash
pip install -r requirements.txt
```

---

## Gaps & Risks

### 🔴 HIGH — Missing `app/dependencies.py`

`s3_routes.py` imports `app.dependencies.get_db`, but the file does not exist. The application will fail to start with an `ImportError` on any environment. **Must be created before first run.**

### 🔴 HIGH — No HTTP exception handling

Unhandled S3 errors (`NoCredentialsError`, `BucketNotFound`) or DB errors will surface as unformatted `500` responses. Proper `HTTPException` wrappers are missing throughout the service and repository layers.

### 🟡 MED — Alembic `target_metadata = None`

`alembic/env.py` has no reference to `Base.metadata`. Auto-generated migrations will be empty, meaning schema drift will go undetected.

### 🟡 MED — Alembic DB URL is a placeholder

`alembic.ini` still contains `driver://user:pass@localhost/dbname`. Migrations will not run until this is replaced or dynamically read from `.env`.

### 🟡 MED — No initial migration version

`alembic/versions/` has no migration files. The `files` table must be tracked via an initial revision before deploying to any environment.

### 🟢 LOW — No API tests

No unit or integration tests exist for upload success or failure paths.

### 🟢 LOW — S3 orphan on DB rollback

If the file uploads to S3 successfully but the DB commit fails, the orphaned S3 object is never cleaned up. A compensating delete call should be added in the exception handler.

---

## Next Implementation Steps

**Step 1 — Create `app/dependencies.py`**

```python
from app.core.database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 2 — Wire Alembic to `Base.metadata`**

In `alembic/env.py`:

```python
from app.core.database import Base
target_metadata = Base.metadata
```

**Step 3 — Configure Alembic DB URL from env**

```python
from app.core.config import settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
```

**Step 4 — Generate initial migration**

```bash
alembic revision --autogenerate -m "create_files_table"
alembic upgrade head
```

**Step 5 — Add structured error handling**

```python
try:
    s3_repo.upload_file(stream, bucket, key)
except Exception:
    raise HTTPException(status_code=500, detail="S3 upload failed")

try:
    file_repo.create(file_obj)
except Exception:
    s3_repo.delete_file(bucket, key)   # compensating delete
    raise HTTPException(status_code=500, detail="Database error")
```

**Step 6 — Write API tests**

```bash
pip install pytest moto httpx
pytest tests/
```

Use `pytest` + `TestClient` with a mocked S3 (`moto`) and an in-memory SQLite DB to cover upload success, file-too-large, and S3 failure paths.

---

## Getting Started

### Prerequisites

- Python 3.10+
- MySQL 8+
- AWS credentials (or LocalStack for local development)
- Docker & Docker Compose *(optional but recommended)*

### Install & Run

```bash
# 1. Clone
git clone https://github.com/your-org/s3-file-service.git
cd s3-file-service

# 2. Configure environment
cp .env.example .env

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
alembic upgrade head

# 5. Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# API docs  →  http://localhost:8000/docs
# Redoc     →  http://localhost:8000/redoc
```

---

## Environment Variables

### `.env`

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy connection string | `mysql+pymysql://user:pass@localhost/s3_service` |
| `AWS_ACCESS_KEY_ID` | AWS credentials | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `wJalrXUtnFEMI/K7MDENG/...` |
| `AWS_DEFAULT_REGION` | AWS region | `ap-south-1` |
| `S3_BUCKET_NAME` | Target S3 bucket | `my-app-files` |
| `MAX_FILE_SIZE` | Max upload size in bytes | `10485760` *(10 MB)* |

---

## License

[MIT](LICENSE) © Your Organization

---

<p align="center">
  <code>FastAPI · SQLAlchemy · Boto3 · MySQL · AWS S3 · Alembic</code><br/>
  <sub>S3 File Service Architecture v1.0 — Production Reference</sub>
</p>
