
"""
Frontlines Combat Engine
------------------------
Step 1: Validate whether one unit type can attack another.

This module only handles attack permissions.
Battle resolution and database updates will be added separately.
"""

# Each attacker can only attack the unit types listed here.
# These presets are based on the attack matrix provided for Frontlines.

ATTACK_PRESETS = {
    "Motorised": [
        "Motorised", "Mechanised", "Armoured", "Engineer",
        "Logistics", "HQ", "National G", "ART", "MART", "AA", "CD"
    ],

    "Mechanised": [
        "Motorised", "Mechanised", "Armoured", "Engineer",
        "Logistics", "HQ", "National G", "ART", "MART", "AA", "CD"
    ],

    "Armoured": [
        "Motorised", "Mechanised", "Armoured", "Engineer",
        "Logistics", "HQ", "National G", "ART", "MART", "AA", "CD"
    ],

    "Engineer": [],
    "Logistics": [],
    "HQ": [],
    "National G": [],

    "ASF": [
        "ASF", "MRF", "AF", "BOMB", "SBOMB", "SASF",
        "SMRF", "AWACS", "TANKER", "SAA", "MPA", "NMRF"
    ],

    "MRF": [
        "Motorised", "Mechanised", "Armoured", "Engineer",
        "Logistics", "HQ", "National G", "ART", "MART", "AA", "CD",
        "ASF", "MRF", "AF", "BOMB", "SBOMB", "SASF",
        "SMRF", "AWACS", "TANKER", "SAA", "MPA", "NMRF"
    ],

    "AF": [
        "Motorised", "Mechanised", "Armoured", "Engineer",
        "Logistics", "HQ", "National G", "ART", "MART", "AA", "CD"
    ],

    "BOMB": [
        "Motorised", "Mechanised", "Armoured", "Engineer",
        "Logistics", "HQ", "National G", "ART", "MART", "AA",
        "CD", "BUILDINGS"
    ],

    "SBOMB": [
        "Motorised", "Mechanised", "Armoured", "Engineer",
        "Logistics", "HQ", "National G", "ART", "MART", "AA",
        "CD", "BUILDINGS"
    ],

    "SASF": [
        "ASF", "MRF", "AF", "BOMB", "SBOMB", "SASF",
        "SMRF", "AWACS", "TANKER", "SAA", "MPA", "NMRF"
    ],

    "SMRF": [
        "Motorised", "Mechanised", "Armoured", "Engineer",
        "Logistics", "HQ", "National G", "ART", "MART", "AA", "CD",
        "ASF", "MRF", "AF", "BOMB", "SBOMB", "SASF",
        "SMRF", "AWACS", "TANKER", "SAA", "MPA", "NMRF"
    ],

    "AWACS": [],
    "TANKER": [],
    "SAA": [],

    "MPA": ["SS"],

    "NMRF": [
        "Motorised", "Mechanised", "Armoured", "Engineer",
        "Logistics", "HQ", "National G", "ART", "MART", "AA", "CD",
        "ASF", "MRF", "AF", "BOMB", "SBOMB", "SASF",
        "SMRF", "AWACS", "TANKER", "SAA", "MPA", "NMRF",
        "LCS", "FF", "DD", "CC", "RS", "AAS", "CV", "SL"
    ],

    "LCS": ["LCS", "FF", "DD", "CC", "RS", "AAS", "CV", "SL"],

    "FF": ["LCS", "FF", "DD", "CC", "RS", "AAS", "CV", "SL"],

    "DD": [
        "LCS", "FF", "DD", "CC", "RS", "AAS", "CV", "SL", "SS"
    ],

    "CC": ["LCS", "FF", "DD", "CC", "RS", "AAS", "CV", "SL"],

    "RS": [],
    "AAS": [],
    "CV": [],
    "SL": [],

    "AH": [
        "Motorised", "Mechanised", "Armoured", "Engineer",
        "Logistics", "HQ", "National G", "ART", "MART", "AA", "CD"
    ],

    "ART": [
        "Motorised", "Mechanised", "Armoured", "Engineer",
        "Logistics", "HQ", "National G", "ART", "MART", "AA", "CD"
    ],

    "MART": [
        "Motorised", "Mechanised", "Armoured", "Engineer",
        "Logistics", "HQ", "National G", "ART", "MART", "AA", "CD"
    ],

    "CD": ["LCS", "FF", "DD", "CC", "RS", "AAS", "CV", "SL"],

    "AA": [
        "ASF", "MRF", "AF", "BOMB", "SBOMB", "SASF",
        "SMRF", "AWACS", "TANKER", "SAA", "MPA", "NMRF"
    ],

    "SS": ["LCS", "FF", "DD", "CC", "RS", "AAS", "CV", "SL", "SS"],
}


# Handle inconsistent spacing and spelling in incoming unit names.
UNIT_ALIASES = {
    # Database unit names
    "motorised infantry": "Motorised",
    "mechanised infantry": "Mechanised",
    "headquarters": "HQ",
    "national guard": "National G",
    "artillery": "ART",
    "mechanised artillery": "MART",
    "anti-air": "AA",
    "coastal defence": "CD",
    "attack helicopter": "AH",
    "air superiority fighter": "ASF",
    "multi-role fighter": "MRF",
    "attack fighter": "AF",
    "bomber": "BOMB",
    "stealth bomber": "SBOMB",
    "stealth air superiority fighter": "SASF",
    "stealth multi-role fighter": "SMRF",
    "airborne warning and control system": "AWACS",
    "tanker": "TANKER",
    "strategic airlift aircraft": "SAA",
    "marine patrol aircraft": "MPA",
    "naval multi-role fighter": "NMRF",
    "litoral combat ship": "LCS",
    "frigate": "FF",
    "destroyer": "DD",
    "cruiser": "CC",
    "replenishment ship": "RS",
    "amphibious assault ship": "AAS",
    "aircraft carrier": "CV",
    "sealift": "SL",
    "submarine": "SS",

    # Existing aliases
    "logisitics": "Logistics",
    "national": "National G",
}



def normalize_unit_type(unit_type):
    """Return a canonical unit type name."""
    if not isinstance(unit_type, str) or not unit_type.strip():
        return None

    name = unit_type.strip()

    # Match canonical names without case sensitivity.
    for canonical_name in ATTACK_PRESETS:
        if name.casefold() == canonical_name.casefold():
            return canonical_name

    return UNIT_ALIASES.get(name.casefold(), name)


def validate_attack(attacker_type, defender_type):
    """
    Check whether an attacker is permitted to attack a defender.

    Returns:
        {
            "allowed": bool,
            "attacker": str | None,
            "defender": str | None,
            "reason": str
        }
    """

    attacker = normalize_unit_type(attacker_type)
    defender = normalize_unit_type(defender_type)

    if attacker is None or defender is None:
        return {
            "allowed": False,
            "attacker": attacker,
            "defender": defender,
            "reason": "Attacker and defender types are required."
        }

    if attacker not in ATTACK_PRESETS:
        return {
            "allowed": False,
            "attacker": attacker,
            "defender": defender,
            "reason": f"Unknown attacker unit type: {attacker}"
        }

    if defender != "BUILDINGS" and defender not in ATTACK_PRESETS:
        return {
            "allowed": False,
            "attacker": attacker,
            "defender": defender,
            "reason": f"Unknown defender unit type: {defender}"
        }

    if defender not in ATTACK_PRESETS[attacker]:
        return {
            "allowed": False,
            "attacker": attacker,
            "defender": defender,
            "reason": f"{attacker} is not permitted to attack {defender}."
        }

    return {
        "allowed": True,
        "attacker": attacker,
        "defender": defender,
        "reason": f"{attacker} is permitted to attack {defender}."
    }



def resolve_combat(attacker, defender):
    """
    Resolve a basic battle after validating attack permissions.

    Expected unit dictionaries:
        {
            "unit_type": "Motorised",
            "strength": 5,
            "formations": 3
        }

    Returns the battle outcome and proposed formation losses.
    This function does not update the database.
    """

    permission = validate_attack(
        attacker.get("unit_type"),
        defender.get("unit_type")
    )

    if not permission["allowed"]:
        return {
            "success": False,
            "result": "invalid_attack",
            "reason": permission["reason"],
            "attacker_losses": 0,
            "defender_losses": 0,
        }

    try:
        attack_strength = float(attacker["strength"])
        defence_strength = float(defender["strength"])
        attacker_formations = int(attacker["formations"])
        defender_formations = int(defender["formations"])
    except (KeyError, TypeError, ValueError):
        return {
            "success": False,
            "result": "invalid_input",
            "reason": (
                "Both units require valid strength and formation values."
            ),
            "attacker_losses": 0,
            "defender_losses": 0,
        }

    if (
        attack_strength < 0
        or defence_strength < 0
        or attacker_formations < 0
        or defender_formations < 0
    ):
        return {
            "success": False,
            "result": "invalid_input",
            "reason": "Strength and formations cannot be negative.",
            "attacker_losses": 0,
            "defender_losses": 0,
        }

    if attacker_formations == 0 or defender_formations == 0:
        return {
            "success": False,
            "result": "invalid_battle",
            "reason": "Both units must have at least one formation.",
            "attacker_losses": 0,
            "defender_losses": 0,
        }

    if attack_strength > defence_strength:
        result = "attacker_wins"
        attacker_losses = 0
        defender_losses = 1

    elif attack_strength < defence_strength:
        result = "defender_wins"
        attacker_losses = 1
        defender_losses = 0

    else:
        result = "draw"
        attacker_losses = 1
        defender_losses = 1

    # Never reduce a unit below zero formations.
    attacker_losses = min(attacker_losses, attacker_formations)
    defender_losses = min(defender_losses, defender_formations)

    return {
        "success": True,
        "result": result,
        "reason": "Combat resolved successfully.",
        "attacker_losses": attacker_losses,
        "defender_losses": defender_losses,
        "attacker_remaining": attacker_formations - attacker_losses,
        "defender_remaining": defender_formations - defender_losses,
    }
