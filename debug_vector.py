import os
import pymysql
from google.cloud.sql.connector import Connector

def debug_vector():
    project = os.environ["CLOUD_SQL_MYSQL_PROJECT"]
    region = os.environ["CLOUD_SQL_MYSQL_REGION"]
    instance = os.environ["CLOUD_SQL_MYSQL_INSTANCE"]
    user = os.environ["CLOUD_SQL_MYSQL_USER"]
    password = os.environ["CLOUD_SQL_MYSQL_PASSWORD"]
    db_name = os.environ["CLOUD_SQL_MYSQL_DATABASE"]

    instance_connection_name = f"{project}:{region}:{instance}"

    print(f"Connecting to {instance_connection_name}...")
    with Connector() as connector:
        conn = connector.connect(
            instance_connection_name,
            "pymysql",
            user=user,
            password=password,
            db=db_name,
        )
        
        with conn.cursor() as cursor:
            # Check version
            cursor.execute("SELECT VERSION()")
            print(f"MySQL Version: {cursor.fetchone()}")

            # Check variables
            cursor.execute("SHOW VARIABLES LIKE 'cloudsql_vector'")
            print(f"cloudsql_vector: {cursor.fetchone()}")

            # Try to create table with vector
            try:
                cursor.execute("DROP TABLE IF EXISTS test_vector")
                print("Creating table with vector(3)...")
                cursor.execute("CREATE TABLE test_vector (id INT PRIMARY KEY, v vector(3))")
                print("Success: Created table with vector(3)")
            except Exception as e:
                print(f"Failed to create table with vector(3): {e}")

            # Try to create table with VARBINARY(3072)
            try:
                cursor.execute("DROP TABLE IF EXISTS test_varbinary")
                print("Creating table with VARBINARY(3072)...")
                cursor.execute("CREATE TABLE test_varbinary (id INT PRIMARY KEY, v VARBINARY(3072))")
                print("Success: Created table with VARBINARY(3072)")
                
                # Try inserting vector data
                print("Inserting vector data...")
                cursor.execute("INSERT INTO test_varbinary VALUES (1, string_to_vector('[0.1, 0.2, 0.3]'))")
                print("Success: Inserted vector data")
            except Exception as e:
                print(f"Failed with VARBINARY: {e}")

if __name__ == "__main__":
    debug_vector()
