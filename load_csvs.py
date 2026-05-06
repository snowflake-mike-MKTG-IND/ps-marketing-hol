import os
import csv
import re
from datetime import datetime
import snowflake.connector

DATA_DIR = "/Users/michaelsworklaptop/Downloads/ps-marketing-hol-main/data"
SCHEMA = "PS_DEMO_2.TEST_HOL"
STAGE = "HOL_CSV_STAGE"

conn = snowflake.connector.connect(connection_name=os.getenv("SNOWFLAKE_CONNECTION_NAME") or "default")
cur = conn.cursor()
cur.execute(f"USE SCHEMA {SCHEMA}")

DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
TIMESTAMP_RE = re.compile(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}')
INT_RE = re.compile(r'^-?\d+$')
FLOAT_RE = re.compile(r'^-?\d+\.\d+$')

def infer_type(values):
    clean = [v for v in values if v.strip() != '']
    if not clean:
        return "VARCHAR"
    
    all_date = True
    all_ts = True
    all_int = True
    all_float = True
    all_bool = True

    for v in clean[:200]:
        v_stripped = v.strip().strip('"')
        if not DATE_RE.match(v_stripped):
            all_date = False
        if not TIMESTAMP_RE.match(v_stripped):
            all_ts = False
        if not INT_RE.match(v_stripped):
            all_int = False
        if not FLOAT_RE.match(v_stripped) and not INT_RE.match(v_stripped):
            all_float = False
        if v_stripped.lower() not in ('true', 'false'):
            all_bool = False

    if all_date:
        return "DATE"
    if all_ts:
        return "TIMESTAMP_TZ"
    if all_bool:
        return "BOOLEAN"
    if all_int:
        return "NUMBER"
    if all_float:
        return "NUMBER(18,6)"
    return "VARCHAR"

csv_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith('.csv')])

for csv_file in csv_files:
    table_name = csv_file.replace('.csv', '')
    filepath = os.path.join(DATA_DIR, csv_file)
    
    print(f"\n--- Processing {table_name} ---")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        
        col_samples = {h: [] for h in headers}
        for i, row in enumerate(reader):
            if i >= 200:
                break
            for j, h in enumerate(headers):
                if j < len(row):
                    col_samples[h].append(row[j])
    
    col_defs = []
    for h in headers:
        col_type = infer_type(col_samples[h])
        safe_name = f'"{h}"' if not h.isupper() or ' ' in h or not h.replace('_','').isalnum() else h
        col_defs.append(f"  {safe_name} {col_type}")
    
    create_sql = f"CREATE OR REPLACE TABLE {table_name} (\n" + ",\n".join(col_defs) + "\n)"
    print(f"  Creating table...")
    cur.execute(create_sql)
    
    print(f"  Uploading file to stage...")
    cur.execute(f"PUT 'file://{filepath}' @{STAGE}/{table_name}/ AUTO_COMPRESS=TRUE OVERWRITE=TRUE")
    
    print(f"  Loading data...")
    copy_sql = f"""
    COPY INTO {table_name}
    FROM @{STAGE}/{table_name}/
    FILE_FORMAT = (
        TYPE = CSV
        FIELD_OPTIONALLY_ENCLOSED_BY = '"'
        SKIP_HEADER = 1
        EMPTY_FIELD_AS_NULL = TRUE
        NULL_IF = ('')
        FIELD_DELIMITER = ','
        ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
    )
    ON_ERROR = 'CONTINUE'
    """
    cur.execute(copy_sql)
    result = cur.fetchall()
    for r in result:
        rows_loaded = r[3] if len(r) > 3 else "?"
        errors = r[5] if len(r) > 5 else 0
        print(f"  Loaded: {rows_loaded} rows, Errors: {errors}")

print("\n\n=== VERIFICATION ===")
for csv_file in csv_files:
    table_name = csv_file.replace('.csv', '')
    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cur.fetchone()[0]
    print(f"  {table_name}: {count} rows")

cur.close()
conn.close()
print("\nDone!")
