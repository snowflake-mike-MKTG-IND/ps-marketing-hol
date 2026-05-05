# Marketing MMM Hands-On Lab - Setup Guide

## Pre-Lab Checklist (30 minutes before start)

### 1. Snowflake Account Access
- Account: `SIE_ICDS_SANDBOX`
- Role: `SNOWFLAKE_LEARNING_ROLE` (or a dedicated HOL role with grants below)
- Warehouse: Any XS warehouse will work for this lab (Section 4 Python cells run locally, not on warehouse)

### 1b. Python Environment (for Section 4)
- Participants need local Python 3.10+ with: `pandas`, `numpy`, `statsmodels`, `snowflake-connector-python`
- Or use Snowflake Notebooks with a Python kernel
- Quick install: `pip install pandas numpy statsmodels snowflake-connector-python`

### 2. Cortex Code Access
- Verify Cortex Code is available in your Snowflake sidebar
- If not visible: Settings > Features > Enable Cortex Code

### 3. Load Data from CSVs
Participants load the data themselves using Cortex Code. Each participant receives the `data/` folder containing 37 CSV files.

**Method A: Cortex Code file attachment (preferred)**
1. Open Cortex Code in Snowsight
2. Click the attachment (+) button in the chat input
3. Select all CSV files from the `data/` folder
4. Prompt: "Create tables from each CSV in my schema. Use the filename as the table name. Infer column types."

**Method B: Stage + COPY INTO (fallback)**
```sql
CREATE OR REPLACE STAGE PS_DEMO.YOUR_NAME_HOL.HOL_STAGE;
-- Upload CSVs via Snowsight stage browser, then:
-- Prompt Cortex Code: "Load all files from @PS_DEMO.YOUR_NAME_HOL.HOL_STAGE into tables using infer_schema"
```

**Verification:**
```sql
SHOW TABLES IN SCHEMA PS_DEMO.YOUR_NAME_HOL; -- Should show ~37 tables
SELECT COUNT(*) FROM PS_DEMO.YOUR_NAME_HOL.DIM_CAMPAIGN; -- Should return 14
SELECT COUNT(*) FROM PS_DEMO.YOUR_NAME_HOL.RAW_META_ADS_INSIGHTS; -- Should return ~23k
```

### 4. Create Your Workspace Schema
```sql
CREATE SCHEMA IF NOT EXISTS PS_DEMO.YOUR_NAME_HOL;
USE SCHEMA PS_DEMO.YOUR_NAME_HOL;
```

### 5. Open the Notebook
- Import `ps_marketing_hol.ipynb` into Snowsight Notebooks
- Or follow along with the prompts on screen

---

## If using a dedicated HOL role (facilitator setup)

```sql
CREATE ROLE IF NOT EXISTS PS_HOL_ROLE;
GRANT USAGE ON DATABASE PS_DEMO TO ROLE PS_HOL_ROLE;
GRANT USAGE ON SCHEMA PS_DEMO.HOL_DEMOS TO ROLE PS_HOL_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA PS_DEMO.HOL_DEMOS TO ROLE PS_HOL_ROLE;
GRANT SELECT ON ALL VIEWS IN SCHEMA PS_DEMO.HOL_DEMOS TO ROLE PS_HOL_ROLE;
GRANT CREATE SCHEMA ON DATABASE PS_DEMO TO ROLE PS_HOL_ROLE;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE PS_HOL_ROLE;

-- Grant to each participant
GRANT ROLE PS_HOL_ROLE TO USER <participant_username>;
```

---

## File Inventory

| File | Purpose |
|------|---------|
| `ps_marketing_hol.html` | 22-slide presentation deck (open in Chrome, arrow keys to navigate, N for speaker notes) |
| `ps_marketing_hol.ipynb` | Participant notebook with pre-filled Cortex Code prompts + validation SQL |
| `ps_mmm_dashboard.py` | Reference Streamlit app — MMM budget optimizer (Section 4 deliverable) |
| `data/` | 37 CSV files — participants load these into Snowflake during setup |
| `SETUP.md` | This file |

---

## Data Architecture

- **CSV source files**: `data/` folder — 37 CSV files representing raw platform ingestion + dimensions + internal metrics + social intelligence
- **Participant workspace**: `PS_DEMO.<YOUR_NAME>_HOL` — each participant loads CSVs into their own schema, then builds on top
- **Dry-run reference**: `PS_HOL_BUILD.HOL_DRYRUN` — facilitator's completed walkthrough (do not share with participants until after lab)

## Timing

| Block | Duration | Content |
|-------|----------|---------|
| Setup | 30 min | Login, Cortex Code check, schema creation, data inventory |
| Section 1 | 30 min | Reorganize raw platform data |
| Section 2 | 30 min | Build reporting views |
| Section 3 | 30 min | AI sentiment, classification, intent |
| Section 4 | 20 min | Build real MMM model (OLS + adstock) + Streamlit dashboard |
| Debrief | 10 min | Recap + next steps |
