import os
import sys
import io
import psycopg2

EXTERNAL_DB_URL = "postgresql://sewasetu:jJy4Xcj5GLJmtAlySz8Sk5hcNihhPgxY@dpg-dbccval9fdbs73ckaiug-a.oregon-postgres.render.com/sewasetu_i8h0"

def main():
    db_url = sys.argv[1] if len(sys.argv) > 1 else EXTERNAL_DB_URL
    print(f"Connecting to Render PostgreSQL database...")
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        print("Connected successfully!\n")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    # Step 1: Run schema.sql
    print("Step 1/2: Applying app/schema.sql...")
    with open("app/schema.sql", "r", encoding="utf-8") as f:
        schema_sql = f.read()
    cur.execute(schema_sql)
    print("Schema applied successfully!\n")

    # Step 2: Run seed.sql with copy_expert
    print("Step 2/2: Loading seed/seed.sql (~200,000 records)...")
    with open("seed/seed.sql", "r", encoding="utf-8") as f:
        in_copy = False
        copy_sql = ""
        buffer = io.StringIO()
        count = 0

        for line in f:
            if line.startswith("COPY "):
                in_copy = True
                copy_sql = line.strip().rstrip(";")
                buffer = io.StringIO()
                count = 0
                print(f"  Streaming data for: {copy_sql[:60]}...")
            elif in_copy and line.strip() == r"\.":
                in_copy = False
                buffer.seek(0)
                # Ensure COPY command uses STDIN for copy_expert
                if "FROM stdin" not in copy_sql and "FROM STDIN" not in copy_sql:
                    copy_sql += " FROM STDIN"
                cur.copy_expert(copy_sql, buffer)
                print(f"  Loaded {count:,} rows into table.")
                buffer = io.StringIO()
            elif in_copy:
                buffer.write(line)
                count += 1
            elif line.strip() and not line.startswith("--"):
                cur.execute(line.strip())
                print(f"  Executed query: {line.strip()[:60]}")

    cur.close()
    conn.close()
    print("\nDatabase initialization complete! All schema and seed data loaded.")

if __name__ == "__main__":
    main()
