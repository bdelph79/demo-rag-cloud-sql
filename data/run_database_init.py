# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import csv
import os
from datetime import datetime, time

import pymysql
from google.cloud.sql.connector import Connector

# Import from models subdirectory
from models.models import Airport, Amenity, Flight, Policy


def load_dataset(
    airports_ds_path: str,
    amenities_ds_path: str,
    flights_ds_path: str,
    policies_ds_path: str,
) -> tuple[
    list[Airport],
    list[Amenity],
    list[Flight],
    list[Policy],
]:
    airports: list[Airport] = []
    with open(airports_ds_path, "r") as f:
        reader = csv.DictReader(f, delimiter=",")
        airports = [Airport.model_validate(line) for line in reader]

    amenities: list[Amenity] = []
    with open(amenities_ds_path, "r") as f:
        reader = csv.DictReader(f, delimiter=",")
        amenities = [Amenity.model_validate(line) for line in reader]

    flights: list[Flight] = []
    with open(flights_ds_path, "r") as f:
        reader = csv.DictReader(f, delimiter=",")
        flights = [Flight.model_validate(line) for line in reader]

    policies: list[Policy] = []
    with open(policies_ds_path, "r") as f:
        reader = csv.DictReader(f, delimiter=",")
        policies = [Policy.model_validate(line) for line in reader]

    return airports, amenities, flights, policies


def __escape_sql(value):
    if value is None:
        return "NULL"
    if isinstance(value, str):
        # Handle double-escaped quotes from CSV (e.g. \')
        value = value.replace("\\'", "'")
        escaped_value = value.replace("'", "''")
        return f"'{escaped_value}'"
    if isinstance(value, list):
        return f"'{value}'"
    if isinstance(value, (time, datetime)):
        return f"'{value}'"
    return str(value)


def initialize_data(
    airports: list[Airport],
    amenities: list[Amenity],
    flights: list[Flight],
    policies: list[Policy],
) -> None:
    project = os.environ["CLOUD_SQL_MYSQL_PROJECT"]
    region = os.environ["CLOUD_SQL_MYSQL_REGION"]
    instance = os.environ["CLOUD_SQL_MYSQL_INSTANCE"]
    user = os.environ["CLOUD_SQL_MYSQL_USER"]
    password = os.environ["CLOUD_SQL_MYSQL_PASSWORD"]
    db_name = os.environ["CLOUD_SQL_MYSQL_DATABASE"]

    instance_connection_name = f"{project}:{region}:{instance}"

    # Use synchronous connector
    with Connector() as connector:
        conn = connector.connect(
            instance_connection_name,
            "pymysql",
            user=user,
            password=password,
            db=db_name,
        )
        
        with conn.cursor() as cursor:
            # Helper to execute SQL
            def execute_sql(query):
                print(f"Executing SQL: {query[:100]}...")
                cursor.execute(query)

            # If the table already exists, drop it to avoid conflicts
            execute_sql("DROP TABLE IF EXISTS airports CASCADE")
            # Create a new table
            execute_sql(
                """
                CREATE TABLE airports(
                    id INT PRIMARY KEY,
                    iata TEXT,
                    name TEXT,
                    city TEXT,
                    country TEXT
                )
            """
            )
            # Insert all the data
            values = [
                f"""(
                {__escape_sql(a.id)},
                {__escape_sql(a.iata)},
                {__escape_sql(a.name)},
                {__escape_sql(a.city)},
                {__escape_sql(a.country)}
            )"""
                for a in airports
            ]
            if values:
                execute_sql(f"""INSERT INTO airports VALUES {", ".join(values)}""")
            print("Airports table initialized")

            # Initialize Amenities
            execute_sql("DROP TABLE IF EXISTS amenities CASCADE")
            execute_sql(
                """
                CREATE TABLE amenities(
                    id INT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    location TEXT,
                    terminal TEXT,
                    category TEXT,
                    hour TEXT,
                    sunday_start_hour TIME,
                    sunday_end_hour TIME,
                    monday_start_hour TIME,
                    monday_end_hour TIME,
                    tuesday_start_hour TIME,
                    tuesday_end_hour TIME,
                    wednesday_start_hour TIME,
                    wednesday_end_hour TIME,
                    thursday_start_hour TIME,
                    thursday_end_hour TIME,
                    friday_start_hour TIME,
                    friday_end_hour TIME,
                    saturday_start_hour TIME,
                    saturday_end_hour TIME,
                    content TEXT NOT NULL,
                    embedding VARBINARY(12288) NOT NULL
                )
            """
            )
            values = [
                f"""(
                {__escape_sql(a.id)},
                {__escape_sql(a.name)},
                {__escape_sql(a.description)},
                {__escape_sql(a.location)},
                {__escape_sql(a.terminal)},
                {__escape_sql(a.category)},
                {__escape_sql(a.hour)},
                {__escape_sql(a.sunday_start_hour)},
                {__escape_sql(a.sunday_end_hour)},
                {__escape_sql(a.monday_start_hour)},
                {__escape_sql(a.monday_end_hour)},
                {__escape_sql(a.tuesday_start_hour)},
                {__escape_sql(a.tuesday_end_hour)},
                {__escape_sql(a.wednesday_start_hour)},
                {__escape_sql(a.wednesday_end_hour)},
                {__escape_sql(a.thursday_start_hour)},
                {__escape_sql(a.thursday_end_hour)},
                {__escape_sql(a.friday_start_hour)},
                {__escape_sql(a.friday_end_hour)},
                {__escape_sql(a.saturday_start_hour)},
                {__escape_sql(a.saturday_end_hour)},
                {__escape_sql(a.content)},
                string_to_vector({__escape_sql(str(a.embedding))})
            )"""
                for a in amenities
            ]
            if values:
                execute_sql(f"""INSERT INTO amenities VALUES {", ".join(values)}""")
            print("Amenities table initialized")

            # Initialize Flights
            execute_sql("DROP TABLE IF EXISTS flights CASCADE")
            execute_sql(
                """
                CREATE TABLE flights(
                    id INT PRIMARY KEY,
                    airline TEXT,
                    flight_number TEXT,
                    departure_airport TEXT,
                    arrival_airport TEXT,
                    departure_time DATETIME,
                    arrival_time DATETIME,
                    departure_gate TEXT,
                    arrival_gate TEXT
                )
            """
            )
            values = [
                f"""(
                {__escape_sql(f.id)},
                {__escape_sql(f.airline)},
                {__escape_sql(f.flight_number)},
                {__escape_sql(f.departure_airport)},
                {__escape_sql(f.arrival_airport)},
                {__escape_sql(f.departure_time)},
                {__escape_sql(f.arrival_time)},
                {__escape_sql(f.departure_gate)},
                {__escape_sql(f.arrival_gate)}
            )"""
                for f in flights
            ]
            if values:
                execute_sql(f"""INSERT INTO flights VALUES {", ".join(values)}""")
            print("Flights table initialized")

            # Initialize Policies
            execute_sql("DROP TABLE IF EXISTS policies CASCADE")
            execute_sql(
                """
                CREATE TABLE policies(
                    id INT PRIMARY KEY,
                    content TEXT,
                    embedding VARBINARY(12288)
                )
            """
            )
            values = [
                f"""(
                {__escape_sql(p.id)},
                {__escape_sql(p.content)},
                string_to_vector({__escape_sql(str(p.embedding))})
            )"""
                for p in policies
            ]
            if values:
                execute_sql(f"""INSERT INTO policies VALUES {", ".join(values)}""")
            print("Policies table initialized")

            # Initialize Tickets
            execute_sql("DROP TABLE IF EXISTS tickets CASCADE")
            execute_sql(
                """
                CREATE TABLE tickets(
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(255),
                    user_name VARCHAR(255),
                    user_email VARCHAR(255),
                    airline VARCHAR(8),
                    flight_number VARCHAR(8),
                    departure_airport VARCHAR(8),
                    departure_time DATETIME,
                    arrival_airport VARCHAR(8),
                    arrival_time DATETIME
                )
            """
            )
            print("Tickets table initialized")

            conn.commit()


def main() -> None:
    airports_ds_path = "data/airport_dataset.csv"
    amenities_ds_path = "data/amenity_dataset.csv"
    flights_ds_path = "data/flights_dataset.csv"
    policies_ds_path = "data/cymbalair_policy.csv"

    airports, amenities, flights, policies = load_dataset(
        airports_ds_path, amenities_ds_path, flights_ds_path, policies_ds_path
    )
    initialize_data(airports, amenities, flights, policies)

    print("database init done.")


if __name__ == "__main__":
    main()
