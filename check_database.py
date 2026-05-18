import os
import pymysql
from google.cloud.sql.connector import Connector

def check_database():
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
            # Check airports table
            cursor.execute("SELECT COUNT(*) FROM airports")
            airport_count = cursor.fetchone()[0]
            print(f"Airports: {airport_count} rows")
            
            # Check amenities table
            try:
                cursor.execute("SELECT COUNT(*) FROM amenities")
                amenity_count = cursor.fetchone()[0]
                print(f"Amenities: {amenity_count} rows")
            except Exception as e:
                print(f"Amenities table error: {e}")
            
            # Check flights table
            try:
                cursor.execute("SELECT COUNT(*) FROM flights")
                flight_count = cursor.fetchone()[0]
                print(f"Flights: {flight_count} rows")
            except Exception as e:
                print(f"Flights table error: {e}")
            
            # Check policies table
            try:
                cursor.execute("SELECT COUNT(*) FROM policies")
                policy_count = cursor.fetchone()[0]
                print(f"Policies: {policy_count} rows")
            except Exception as e:
                print(f"Policies table error: {e}")
            
            # Show sample data
            if airport_count > 0:
                cursor.execute("SELECT * FROM airports LIMIT 3")
                print("\nSample airports:")
                for row in cursor.fetchall():
                    print(f"  {row}")

if __name__ == "__main__":
    check_database()
