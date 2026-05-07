import psycopg
import sys

def check_or_create_db():
    try:
        # Connect to default postgres database
        conn = psycopg.connect(
            "host=localhost user=postgres password=123 dbname=postgres",
            autocommit=True
        )
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'school_system_db_v2'")
        exists = cur.fetchone()
        
        if not exists:
            print("Database school_system_db_v2 does not exist. Creating...")
            cur.execute("CREATE DATABASE school_system_db_v2")
            print("Database created successfully.")
        else:
            print("Database school_system_db_v2 already exists.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_or_create_db()
