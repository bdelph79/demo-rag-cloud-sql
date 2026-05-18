"""Direct-IP wrapper around run_database_init — bypasses Cloud SQL Python Connector."""
import os
import sys

import pymysql

# Patch the connector before the main module imports it
class _DirectConnector:
    """Minimal Connector-compatible shim that opens a plain pymysql connection."""
    def __enter__(self):
        return self
    def __exit__(self, *a):
        pass
    def connect(self, instance_connection_name, driver, user, password, db):
        host = os.environ["CLOUD_SQL_MYSQL_HOST"]
        return pymysql.connect(host=host, user=user, password=password, database=db)

import google.cloud.sql.connector as _cs_connector
_cs_connector.Connector = _DirectConnector

# Now import and run normally
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.run_database_init import main
main()
