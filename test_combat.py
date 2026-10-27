
from combat import validate_attack, resolve_combat


# Existing attack-permission checks
permission_tests = [
    ("Motorised", "Armoured", True),
    ("Motorised", "HQ", True),
    ("Engineer", "Armoured", False),
    ("ASF", "BOMB", True),
    ("MPA", "SS", True),
    ("RS", "LCS", False),
    ("SS", "CV", True),
    ("BOMB", "BUILDINGS", True),
    ("Unknown Unit", "HQ", False),
]

for attacker, defender, expected in permission_tests:
    result = validate_attack(attacker, defender)
    assert result["allowed"] == expected, (
        f"Permission test failed: {attacker} -> {defender}"
    )


# Attacker wins
result = resolve_combat(
    {"unit_type": "Motorised", "strength": 5, "formations": 3},
    {"unit_type": "Armoured", "strength": 3, "formations": 2},
)
assert result["result"] == "attacker_wins"
assert result["attacker_losses"] == 0
assert result["defender_losses"] == 1


# Defender wins
result = resolve_combat(
    {"unit_type": "Motorised", "strength": 2, "formations": 3},
    {"unit_type": "Armoured", "strength": 4, "formations": 2},
)
assert result["result"] == "defender_wins"
assert result["attacker_losses"] == 1
assert result["defender_losses"] == 0


# Draw
result = resolve_combat(
    {"unit_type": "Motorised", "strength": 4, "formations": 3},
    {"unit_type": "Armoured", "strength": 4, "formations": 2},
)
assert result["result"] == "draw"
assert result["attacker_losses"] == 1
assert result["defender_losses"] == 1


# Illegal attack must not resolve
result = resolve_combat(
    {"unit_type": "Engineer", "strength": 5, "formations": 3},
    {"unit_type": "Armoured", "strength": 2, "formations": 2},
)
assert result["success"] is False
assert result["result"] == "invalid_attack"


# Formation counts must never become negative
result = resolve_combat(
    {"unit_type": "Motorised", "strength": 4, "formations": 1},
    {"unit_type": "Armoured", "strength": 4, "formations": 1},
)
assert result["attacker_remaining"] == 0
assert result["defender_remaining"] == 0


print("All combat tests passed.")
