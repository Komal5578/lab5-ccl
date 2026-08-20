# Lab 5 – Assignment 1: Deploy and Connect AWS RDS to Lab 4 EC2 Application

## Overview
This assignment deploys an AWS RDS PostgreSQL instance and connects it to the Gitea
application from Lab 4 (previously running on local PostgreSQL on the same EC2 instance).
All CRUD operations are demonstrated through the live Gitea application after migration.

- **Application**: Gitea (self-hosted Git server)
- **EC2 instance**: `gitea-server` (t3.micro, Ubuntu)
- **Database**: AWS RDS PostgreSQL (`db.t3.micro`)
- **EC2 Public URL**: `http://<ec2-public-ip>` *(update with current IP before submission)*

---

## Architecture

```
        Internet
            │  HTTP :80
            ▼
   ┌────────────────────┐
   │   EC2 Instance      │
   │  ┌───────────────┐  │
   │  │ Nginx (proxy)  │  │
   │  └───────┬───────┘  │
   │          │ :3000     │
   │  ┌───────▼───────┐  │
   │  │ Gitea (systemd)│  │
   │  └───────┬───────┘  │
   └──────────┼──────────┘
              │ :5432 (SSL)
              ▼
   ┌────────────────────┐
   │  AWS RDS PostgreSQL │
   │  gitea-rds-db       │
   │  (private, no       │
   │   public access)    │
   └────────────────────┘
```

- Only port 80 is publicly exposed (via the EC2 security group).
- Gitea (port 3000) and RDS (port 5432) are never exposed to the internet.
- RDS inbound rule allows traffic **only from the EC2 security group** — no `0.0.0.0/0`.

---

## RDS Database Setup

| Setting | Value |
|---|---|
| Engine | PostgreSQL |
| Instance class | db.t3.micro (Free Tier) |
| Storage | 20 GiB, General Purpose SSD (gp2) |
| Multi-AZ | No (single-AZ) |
| DB instance identifier | `gitea-rds-db` |
| Initial database name | `gitea` |
| Master username | `giteauser` |
| Public access | **No** |
| VPC | Same VPC as EC2 instance |
| Connectivity | Set up via "Connect to an EC2 compute resource" (auto-configures security groups) |

### Security configuration
AWS automatically created two paired security groups when connecting RDS to the EC2 instance:

- **`ec2-rds-1`** — attached to the EC2 instance, allows outbound to RDS
- **`rds-ec2-1`** — attached to the RDS instance, allows inbound **only** from the EC2 instance's
  security group (`sg-...` — not an IP address, not `0.0.0.0/0`)

Inbound rule on `rds-ec2-1`:

| Type | Protocol | Port | Source |
|---|---|---|---|
| PostgreSQL | TCP | 5432 | EC2 security group ID (not `0.0.0.0/0`) |

This satisfies the lab's mandatory rule: *"RDS inbound must allow DB access only from the EC2
Security Group."*

---

## Migration Steps (Local PostgreSQL → RDS)

1. **Took a backup** of the existing local Gitea database:
   ```bash
   sudo -u postgres pg_dump gitea > /tmp/gitea_db_backup.sql
   ```

2. **Tested connectivity** from EC2 to RDS before migrating:
   ```bash
   psql -h <rds-endpoint> -U giteauser -d gitea
   ```

3. **Restored the backup** into the RDS `gitea` database:
   ```bash
   psql -h <rds-endpoint> -U giteauser -d gitea < /tmp/gitea_db_backup.sql
   ```

4. **Verified the migration** — confirmed 116 tables present in RDS matching the local schema:
   ```sql
   \dt
   ```

5. **Updated Gitea's configuration** (`/etc/gitea/app.ini`) to point at RDS:
   ```ini
   [database]
   DB_TYPE  = postgres
   HOST     = <rds-endpoint>:5432
   NAME     = gitea
   USER     = giteauser
   PASSWD   = ******** (redacted)
   SSL_MODE = require
   ```

6. **Restarted the Gitea service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart gitea
   sudo systemctl status gitea
   ```

7. **Verified end-to-end**: opened the app in the browser and confirmed all pre-existing
   repositories (`viva-repo`, `test-repo`, `test-org-repo`, `private-test-repo`) loaded
   correctly from RDS.

---

## CRUD Demonstration (via the live Gitea application)

All CRUD operations were performed through Gitea's UI, which in turn issues SQL operations
against the RDS `gitea` database (verified at the database layer with direct queries).

| Operation | Action in Gitea UI | Verified via |
|---|---|---|
| **Create** | Created a new repository | Repository appeared in UI and in `repository` table on RDS |
| **Read** | Viewed the repository page | Repository loaded correctly from RDS |
| **Update** | Edited the repository description in Settings | Change persisted and reflected on reload |
| **Delete** | Deleted the repository via Settings → Danger Zone | Repository removed from UI and from `repository` table on RDS |

Database-level confirmation query:
```sql
SELECT name, owner_name, created_unix FROM repository;
```

---

## Notable Issue & Fix (Troubleshooting)

After pointing Gitea's config at RDS, the service entered a crash-restart loop
(`Main process exited, code=exited, status=1/FAILURE`). Root cause was isolated by:

1. Confirming network connectivity from the EC2 instance to RDS on port 5432 (successful).
2. Running Gitea manually in the foreground to capture direct output.
3. Testing the database login independently with `psql`, which returned:
   ```
   FATAL: password authentication failed for user "giteauser"
   ```

**Fix**: Reset the RDS master password via RDS Console → Modify → Credentials settings,
updated `app.ini` to match, and confirmed login with `psql` before restarting Gitea.
This isolated the failure to an authentication mismatch rather than a networking or
configuration issue.

---

## Evidence

See the accompanying PDF report and screenshots folder for:
- RDS instance creation and configuration screens
- Security group inbound rules (proof of EC2-only access)
- Migration output (backup, restore, table verification)
- Updated `app.ini` configuration
- Gitea service status (`active (running)`) after successful reconnection
- CRUD proof (Create/Read/Update/Delete) via the live application
- Final database query confirming CRUD lifecycle

---

## Deliverables Checklist

- [x] AWS RDS PostgreSQL deployed
- [x] Schema with 2+ related tables (116 tables migrated from Gitea's schema)
- [x] EC2 application (Gitea) connected to RDS
- [x] All CRUD operations demonstrated from the running EC2 application
- [x] RDS inbound restricted to EC2 security group only (no `0.0.0.0/0`)
- [x] README with deployment + connection steps
- [ ] 1–2 page PDF report *(separate file)*v
