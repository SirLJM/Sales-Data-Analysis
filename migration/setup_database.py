import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


def main():
    load_dotenv(Path(__file__).parent.parent / '.env')
    connection_string = os.environ.get('DATABASE_URL')

    if not connection_string:
        print("=" * 60)
        print("ERROR: DATABASE_URL not found in .env file")
        print("=" * 60)
        print("\nPlease create a .env file in the project root with:")
        print("DATABASE_URL=postgresql://inventory_user:password@localhost:5432/inventory_db")
        print("\nSee INSTALL_POSTGRESQL.md for detailed setup instructions")
        return 1

    print("=" * 60)
    print("PostgreSQL Database Setup")
    print("=" * 60)

    print("\n1. Testing database connection...")
    engine = create_engine(connection_string)

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print("   Connected successfully!")
            print(f"   PostgreSQL version: {version.split(',')[0]}")
    except Exception as e:
        print(f"   Connection failed: {e}")
        print("\nPlease verify:")
        print("  1. PostgreSQL is installed and running")
        print("  2. Database 'inventory_db' exists")
        print("  3. User 'inventory_user' exists with correct password")
        print("  4. .env file has correct DATABASE_URL")
        return 1

    print("\n2. Running schema.sql...")
    schema_file = Path(__file__).parent / 'schema.sql'

    if not schema_file.exists():
        print(f"   File not found: {schema_file}")
        return 1

    with open(schema_file, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    try:
        with engine.connect() as conn:
            conn.execute(text(schema_sql))
            conn.commit()
        print("   Schema created successfully")
    except Exception as e:
        print(f"   Schema creation failed: {e}")
        print("\n   This is normal if tables already exist. Continuing...")

    print("\n3. Running triggers.sql...")
    triggers_file = Path(__file__).parent / 'triggers.sql'

    if not triggers_file.exists():
        print(f"   File not found: {triggers_file}")
        return 1

    with open(triggers_file, 'r', encoding='utf-8') as f:
        triggers_sql = f.read()

    try:
        with engine.connect() as conn:
            conn.execute(text(triggers_sql))
            conn.commit()
        print("   Triggers created successfully")
    except Exception as e:
        print(f"   Trigger creation failed: {e}")
        print("   Continuing...")

    print("\n4. Running materialized_views.sql...")
    views_file = Path(__file__).parent / 'materialized_views.sql'

    if not views_file.exists():
        print(f"   File not found: {views_file}")
        return 1

    with open(views_file, 'r', encoding='utf-8') as f:
        views_sql = f.read()

    try:
        with engine.connect() as conn:
            conn.execute(text(views_sql))
            conn.commit()
        print("   Materialized views created successfully")
    except Exception as e:
        print(f"   Materialized view creation failed: {e}")
        print("   Continuing...")

    print("\n5. Verifying database structure...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                                       SELECT tablename
                                       FROM pg_tables
                                       WHERE schemaname = 'public'
                                       ORDER BY tablename
                                       """))
            tables = [row[0] for row in result]

            print(f"   Found {len(tables)} tables:")
            for table in tables:
                print(f"      - {table}")

            result = conn.execute(text("""
                                       SELECT matviewname
                                       FROM pg_matviews
                                       WHERE schemaname = 'public'
                                       ORDER BY matviewname
                                       """))
            views = [row[0] for row in result]

            if views:
                print(f"\n   Found {len(views)} materialized views:")
                for view in views:
                    print(f"      - {view}")

            result = conn.execute(text("""
                                       SELECT COUNT(*)
                                       FROM pg_trigger
                                       WHERE tgname LIKE 'trg_%'
                                       """))
            trigger_count = result.fetchone()[0]
            print(f"\n   Found {trigger_count} triggers")

    except Exception as e:
        print(f"   Verification failed: {e}")
        return 1

    print("\n" + "=" * 60)
    print("Database setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Import data: python migration/initial_populate.py")
    print("  2. Test app in file mode first")
    print("  3. Switch to database mode in data_source_config.json")
    print("  4. Run app: cd src && py -m streamlit run app.py")

    engine.dispose()
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
