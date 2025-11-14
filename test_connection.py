# test_connection.py

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

def test_database_connection():
    """
    Tests the connection to the PostgreSQL database using the URL from the .env file.
    """
    # 1. Load environment variables from .env file
    print("Attempting to load environment variables from .env file...")
    load_dotenv()
    
    db_url = os.getenv("DATABASE_URL")
    
    # 2. Check if DATABASE_URL is set
    if not db_url:
        print("❌ ERROR: DATABASE_URL is not set in the .env file.")
        print("Please make sure your .env file contains a line like:")
        print("DATABASE_URL=postgresql://user:password@host/dbname")
        return

    if "localhost" in db_url:
        print("⚠️ WARNING: Your DATABASE_URL seems to be pointing to a local database.")
        print(f"   URL: {db_url}")
        print("   Please ensure this is correct. If you want to connect to Neon, update it with your Neon connection string.")

    try:
        # 3. Create a SQLAlchemy engine
        print("\nCreating SQLAlchemy engine...")
        engine = create_engine(db_url)
        
        # 4. Connect to the database and execute a simple query
        print("Attempting to connect to the database...")
        with engine.connect() as connection:
            print("✅ Connection successful!")
            
            # Execute a query to get the PostgreSQL version
            result = connection.execute(text("SELECT version();"))
            db_version = result.scalar()
            
            print(f"🎉 Successfully connected to your database.")
            print(f"   PostgreSQL Version: {db_version}")

    except OperationalError as e:
        print("\n❌ CONNECTION FAILED: An OperationalError occurred.")
        print("This usually means the database server is not running, the host is incorrect, or the port is wrong.")
        print(f"DETAILS: {e}")
        
    except ProgrammingError as e:
        print("\n❌ CONNECTION FAILED: A ProgrammingError occurred.")
        print("This often indicates incorrect credentials (username/password) or that the database does not exist.")
        print(f"DETAILS: {e}")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    test_database_connection()
