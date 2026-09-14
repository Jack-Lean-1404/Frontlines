import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


def get_units():
    """
    Return all active units from the database.

    Returns:
        [
            {
                "unit_id": 1,
                "unit_name": "Motorised Infantry",
                "unit_class": "Infantry",
                "strength": 4,
                "defence": 4
            },
            ...
        ]
    """

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                unit_id,
                unit_name,
                unit_class,
                strength,
                defence
            FROM units
            WHERE is_active = 1
            ORDER BY unit_id
        """)

        units = cursor.fetchall()

        return units

    finally:
        cursor.close()
        connection.close()

def get_unit_by_name(unit_name):

    units = get_units()
    for unit in units:
        if unit["unit_name"].lower() == unit_name.lower():
            return unit

    return None