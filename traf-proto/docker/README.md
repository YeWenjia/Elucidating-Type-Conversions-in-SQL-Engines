# Docker setup for MSSQL and Oracle on Apple Silicon

ARM64-native containers for running the spider test suite against MSSQL and Oracle from a Mac M-series chip. Credentials match `test/config.yml`.

## Services

| Service | Image | Port | Credentials |
|---|---|---|---|
| `traf_mssql` | `mcr.microsoft.com/azure-sql-edge:latest` (ARM64) | 1433 | `sa` / `reallyStrongPwd123` |
| `mssql-init` | `mcr.microsoft.com/mssql-tools:latest` (one-shot, emulated amd64) | — | creates the `traf_spider` database |
| `traf_oracle` | `gvenzl/oracle-free:latest` (ARM64) | 1521 | `myuser` / `password` on PDB `FREEPDB1` |

`azure-sql-edge` is SQL Server's engine over the same wire protocol, so ODBC Driver 17 and the T-SQL the harness emits (`CREATE SCHEMA`, `DATETIME2`, `sp_rename`, etc.) work. If a feature it lacks shows up, swap to `mcr.microsoft.com/mssql/server:2022-latest` with `platform: linux/amd64` (slower, emulated).

The Oracle user is auto-created on first boot via `APP_USER` with `CONNECT`, `RESOURCE`, and unlimited tablespace — matching what the spider harness needs.

## Run

```bash
cd docker
docker compose up -d

# Oracle first boot takes ~60-90s. Wait until healthy:
docker compose ps
docker compose logs -f oracle   # wait for "DATABASE IS READY TO USE!"
```

## Host prerequisites for the Python clients

- **MSSQL**: install the ODBC driver the config points at.
  ```bash
  brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
  HOMEBREW_ACCEPT_EULA=Y brew install msodbcsql17 unixodbc
  ```
- **Oracle**: `python-oracledb` runs in thin mode on ARM Macs out of the box. No Instant Client needed.

## Run the tests

```bash
# from repo root, after `docker compose up -d`
python -m pytest test/spider/test_spider_folders.py -k mssql -v
python -m pytest test/spider/test_spider_folders.py -k oracle -v
```

## Reset

```bash
docker compose down -v   # wipes both volumes
```
