
import os
import random

import mysql.connector
from dotenv import load_dotenv

from battle import resolve_battle


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

NUMBER_OF_TESTS = 20
MIN_FORMATION_SIZE = 1
MAX_FORMATION_SIZE = 5


# ============================================================
# DATABASE
# ============================================================

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", "3306"))
    )


def load_ground_units(cursor):
    """
    Load real unit definitions from the database.
    Only active land units with valid combat values are used.
    """

    cursor.execute("""
        SELECT
            unit_id,
            unit_name,
            unit_class,
            unit_group,
            strength,
            defence
        FROM units
        WHERE unit_class = 'land'
          AND is_active = 1
          AND strength IS NOT NULL
          AND defence IS NOT NULL
    """)

    units = cursor.fetchall()

    if len(units) < 2:
        raise RuntimeError(
            "At least two active land unit definitions "
            "with strength and defence values are required."
        )

    return units


# ============================================================
# BUILD COMBAT REQUEST
# ============================================================

def build_combatant(unit, formation_size):
    return {
        "unit_id": unit["unit_id"],
        "unit_name": unit["unit_name"],
        "unit_class": unit["unit_class"],
        "unit_type": unit["unit_group"],
        "strength": int(unit["strength"]),
        "defence": int(unit["defence"]),
        "formation_size": formation_size,
        "capabilities": {}
    }


def build_random_battle(units, battle_number):
    attacker_unit, defender_unit = random.sample(units, 2)

    attacker_size = random.randint(
        MIN_FORMATION_SIZE,
        MAX_FORMATION_SIZE
    )

    defender_size = random.randint(
        MIN_FORMATION_SIZE,
        MAX_FORMATION_SIZE
    )

    request = {
        "combat_type": "standard",

        "attacker": build_combatant(
            attacker_unit,
            attacker_size
        ),

        "defender": build_combatant(
            defender_unit,
            defender_size
        ),

        "context": {
            "attacker": {},
            "defender": {}
        }
    }

    return request


# ============================================================
# VALIDATE ENGINE RESULT
# ============================================================

def validate_result(request, result):
    attacker_before = request["attacker"]["formation_size"]
    defender_before = request["defender"]["formation_size"]

    attacker_after = result["attacker"]["formation_size_after"]
    defender_after = result["defender"]["formation_size_after"]

    outcome = result["outcome"]

    assert outcome in {
        "attacker_victory",
        "defender_victory",
        "tie"
    }, f"Unexpected outcome: {outcome}"

    assert 0 <= attacker_after <= attacker_before
    assert 0 <= defender_after <= defender_before

    if outcome == "attacker_victory":
        assert attacker_after == attacker_before
        assert defender_after == max(0, defender_before - 1)

    elif outcome == "defender_victory":
        assert attacker_after == max(0, attacker_before - 1)
        assert defender_after == defender_before

    else:
        assert attacker_after == max(0, attacker_before - 1)
        assert defender_after == max(0, defender_before - 1)

    assert (
        result["attacker"]["destroyed"] == (attacker_after == 0)
    )

    assert (
        result["defender"]["destroyed"] == (defender_after == 0)
    )


# ============================================================
# RUN TESTS
# ============================================================

def main():
    connection = None
    cursor = None

    passed = 0
    failed = 0

    try:
        print("=" * 65)
        print("FRONTLINES DATABASE-DRIVEN COMBAT TEST")
        print("=" * 65)

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        units = load_ground_units(cursor)

        print(f"\nLoaded {len(units)} active land unit definitions.")
        print(f"Running {NUMBER_OF_TESTS} random battles.\n")

        for battle_number in range(1, NUMBER_OF_TESTS + 1):
            request = build_random_battle(
                units,
                battle_number
            )

            attacker = request["attacker"]
            defender = request["defender"]

            try:
                result = resolve_battle(request)
                validate_result(request, result)

                passed += 1
                status = "PASS"

            except Exception as error:
                failed += 1
                status = f"FAIL: {error}"
                result = None

            print("-" * 65)
            print(f"Battle {battle_number}: {status}")

            print(
                f"Attacker: {attacker['unit_name']} "
                f"(strength {attacker['strength']}, "
                f"size {attacker['formation_size']})"
            )

            print(
                f"Defender: {defender['unit_name']} "
                f"(defence {defender['defence']}, "
                f"size {defender['formation_size']})"
            )

            if result is not None:
                print(f"Outcome: {result['outcome']}")

                print(
                    "Attacker formation: "
                    f"{result['attacker']['formation_size_before']} "
                    "-> "
                    f"{result['attacker']['formation_size_after']}"
                )

                print(
                    "Defender formation: "
                    f"{result['defender']['formation_size_before']} "
                    "-> "
                    f"{result['defender']['formation_size_after']}"
                )

        print("\n" + "=" * 65)
        print("TEST SUMMARY")
        print("=" * 65)
        print(f"Battles run: {passed + failed}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")

    except Exception as error:
        print(f"\nTEST SETUP ERROR: {error}")

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

        print("\nDatabase connection closed.")


if __name__ == "__main__":
    main()
