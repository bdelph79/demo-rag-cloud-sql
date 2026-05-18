import os
import pymysql
from google.cloud.sql.connector import Connector

def test_amenities_query():
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
            test_query = "coffee"
            
            # Test 1: Simple select without vector search
            print("\nTest 1: Simple SELECT")
            try:
                cursor.execute("SELECT name, description, location, terminal, category, hour FROM amenities LIMIT 3")
                results = cursor.fetchall()
                print(f"Success! Got {len(results)} rows")
                for row in results:
                    print(f"  {row[0]}")
            except Exception as e:
                print(f"Failed: {e}")
            
            # Test 2: Check if embedding column exists
            print("\nTest 2: Check embedding column")
            try:
                cursor.execute("SELECT embedding FROM amenities LIMIT 1")
                result = cursor.fetchone()
                print(f"Success! Embedding exists, type: {type(result[0])}, length: {len(result[0])}")
            except Exception as e:
                print(f"Failed: {e}")
            
            # Test 3: Try vector search with string_to_vector
            print("\nTest 3: Vector search with string_to_vector")
            try:
                query = """SELECT name, description, location, terminal, category, hour, 
                          (1 - (embedding <=> string_to_vector(embedding('gemini-embedding-001', %s)))) as score
                          FROM amenities
                          HAVING score > 0.5
                          ORDER BY score DESC
                          LIMIT 5"""
                cursor.execute(query, (test_query,))
                results = cursor.fetchall()
                print(f"Success! Got {len(results)} rows")
                for row in results:
                    print(f"  {row[0]} (score: {row[6]})")
            except Exception as e:
                print(f"Failed: {e}")
            
            # Test 4: Try without HAVING clause
            print("\nTest 4: Vector search without HAVING")
            try:
                query = """SELECT name, description, location, terminal, category, hour, 
                          (1 - (embedding <=> string_to_vector(embedding('gemini-embedding-001', %s)))) as score
                          FROM amenities
                          ORDER BY score DESC
                          LIMIT 5"""
                cursor.execute(query, (test_query,))
                results = cursor.fetchall()
                print(f"Success! Got {len(results)} rows")
                for row in results:
                    print(f"  {row[0]} (score: {row[6]})")
            except Exception as e:
                print(f"Failed: {e}")

if __name__ == "__main__":
    test_amenities_query()
