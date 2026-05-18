import csv
from datetime import datetime, time

def __escape_sql(value):
    if value is None:
        return "NULL"
    if isinstance(value, str):
        # Fix double-escaped quotes from CSV (e.g. "Port O\'Connor" -> "Port O'Connor")
        clean_value = value.replace("\\'", "'")
        return f"""'{clean_value.replace("'", "''")}'"""
    if isinstance(value, list):
        return f"""'{value}'"""
    if isinstance(value, time) or isinstance(value, datetime):
        return f"""'{value}'"""
    return value

# Simulate the problematic line from the CSV
# 3847,\N,Port O'Connor Private Heliport,Port O\'Connor,United States
csv_line = "3847,\\N,Port O'Connor Private Heliport,Port O\\'Connor,United States"
print(f"Raw CSV line: {csv_line}")

# Parse it like the script does
reader = csv.reader([csv_line], delimiter=",")
row = next(reader)
print(f"Parsed row: {row}")

# The city is at index 3
city = row[3]
print(f"City value: {city}")

escaped_city = __escape_sql(city)
print(f"Escaped city: {escaped_city}")

# Simulate the SQL construction
sql_fragment = f"INSERT INTO airports VALUES (..., {escaped_city}, ...)"
print(f"SQL Fragment: {sql_fragment}")
