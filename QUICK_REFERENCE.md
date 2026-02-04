# 📋 QUICK REFERENCE - Torre Control

## Copy-Paste Commands

### **Run Everything (15 minutes)**
```bash
make install && make setup-docker && make run
```

### **Step-by-Step**
```bash
make install          # Install deps
make setup-docker     # Start PostgreSQL  
make load-raw        # CSV → database
make transform       # Star Schema
make export          # → CSVs
make validate        # QA checks
```

### **Diagnostics**
```bash
make health          # System check
make logs            # See errors
make clean           # Remove outputs
```

---

## Database Credentials

```
Server:   localhost:5433
Database: supply_chain_dw
User:     admin
Password: adminpassword
```

---

## Troubleshooting Matrix

| Problem | Cause | Solution |
|---------|-------|----------|
| "Connection refused" | PostgreSQL not running | `make setup-docker` |
| "ModuleNotFoundError" | Python deps missing | `make install` |
| "No such file" `Data/Raw/...` | Raw data missing | Check `Data/Raw/` has CSVs |
| "Data/Processed/ empty" | Export failed | `make logs` to see error |
| Power BI can't see data | CSVs not generated | `make export` then `make validate` |
| Docker port conflict | Port 5433 in use | `netstat -ano \| findstr 5433` (Windows) or `lsof -i :5433` (Mac/Linux) |

---

## File Locations

| What | Path |
|------|------|
| Raw data | `Data/Raw/DataCoSupplyChainDataset.csv` |
| Processed CSVs | `Data/Processed/*.csv` |
| Python scripts | `scripts/load_data.py` + `src/etl/export_star_schema.py` |
| Database setup | `config/docker-compose.yml` |
| Logs | `logs/` |
| Power BI | `PBIX/TorreControl_v0.1.pbix` |

---

## Expected Row Counts (Validation)

```
fact_orders.csv:     186,638 rows
dim_customer.csv:      5,000 rows
dim_product.csv:       1,800 rows
dim_geography.csv:       150 rows
dim_date.csv:            365 rows
```

---

## Power BI Integration (3 steps)

1. **Get Data** → Folder → `Data/Processed/`
2. **Import** all 5 CSVs
3. **Model** → Relationships: fact_orders ← dim_*

---

## Help

```bash
make help            # Show all commands
```

**For more details:**
- Setup? → `QUICK_START.md`
- Architecture? → `AUDITORIA_ARQUITECTURA.md`
- Power BI? → `docs/guides/POWER_BI_CONNECTION_COMPLETE_GUIDE.md`
