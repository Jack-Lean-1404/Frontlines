import random

from test_battle import get_units

# ============================================================
# UNIT DATA
# ============================================================

units = get_units()

UNIT_IDS = {
    unit["unit_name"].lower(): unit["unit_id"]
    for unit in units
}


# ============================================================
# SPECIAL UNIT IDS
# ============================================================

HELICOPTER_ID = UNIT_IDS["attack helicopter"]

COASTAL_DEFENCE_ID = UNIT_IDS["coastal defence"]
ANTI_AIR_ID = UNIT_IDS["anti-air"]

SUBMARINE_ID = UNIT_IDS["submarine"]

# Units capable of ASW
ASW_IDS = {
    UNIT_IDS["destroyer"],
    UNIT_IDS["submarine"],
    UNIT_IDS["marine patrol aircraft"]
}

# Units capable of Artillery
ARTILLERY_IDS = {
    UNIT_IDS["artillery"],
    UNIT_IDS["mechanised artillery"]
}

# Units capable of Stealth
STEALTH_IDS = {
    UNIT_IDS["stealth air superiority fighter"],
    UNIT_IDS["stealth bomber"],
    UNIT_IDS["stealth multi-role fighter"]
}

# Units capable of Bombing
BOMBING_IDS = {
    UNIT_IDS["bomber"],
    UNIT_IDS["stealth bomber"],
}

# Units capable of ATG
ATG_IDS = {
    UNIT_IDS["multi-role fighter"],
    UNIT_IDS["attack fighter"],
    UNIT_IDS["stealth bomber"],
    UNIT_IDS["bomber"],
    UNIT_IDS["stealth multi-role fighter"],
    UNIT_IDS["naval multi-role fighter"]
}

# Units capable of ATS
ATS_IDS = {
    UNIT_IDS["naval multi-role fighter"],
    UNIT_IDS["marine patrol aircraft"]
}


# ============================================================
# COMBAT MODIFIERS
# ============================================================

RIVER_MODIFIER = 0.5
NO_HQ_MODIFIER = 0.5
NO_SUPPLY_MODIFIER = 0

NAT_GRD_CITY_BONUS = 2
COMBINED_ARMS_BONUS = 1

AWACS_MODIFIER = 1.5


# ============================================================
# Special Units
# ============================================================

# Artillery
ARTILLERY_SUPPRESSED_CHANCE = 50
ARTILLERY_DESTROYED_CHANCE = 25
ARTILLERY_NO_EFFECT_CHANCE = 25

#Air Defence
ANTI_AIR_NON_STEALTH_HIT_CHANCE = 80
ANTI_AIR_STEALTH_HIT_CHANCE = 20

# SEAD 
SEAD_SUCCESS_CHANCE = 60

# Attack Helicopter
HELICOPTER_DESTROYED_CHANCE = 25

# Submarine
SUBMARINE_ATTACK_FAILED_CHANCE = 25
SUBMARINE_ATTACK_SUCCESS_CHANCE = 75

# Coastal Defence
COASTAL_DEFENCE_HIT_CHANCE = 60

# ============================================================
# Air Units
# ============================================================

# Airdrop
AIRDROP_SUCCESS_CHANCE = 80

# Bombing Success
STRATEGIC_BOMBING_SUCCESS_CHANCE = 60


# ============================================================
# SEA Units
# ============================================================

# Anti-Submarine Warfare
ASW_SUCCESS_CHANCE = 50

# Amphibious Assault
AMPHIBIOUS_SUCCESS_CHANCE = 50



# ============================================================
# COMBAT MODIFIERS
# ============================================================

def apply_modifiers(base_value, modifiers=None):
    if modifiers is None:
        modifiers = []

    value = base_value

    # Apply flat modifiers first
    for modifier in modifiers:
        if modifier["type"] == "flat":
            value += modifier["value"]

    # Apply percentage modifiers second
    for modifier in modifiers:
        if modifier["type"] == "percentage":
            value *= 1 + (modifier["value"] / 100)

    return value

# ============================================================
# AWACS
# ============================================================

def awacs_modifier(has_awacs):
    if not has_awacs:
        return []

    return [
        {
            "type": "percentage",
            "value": AWACS_MODIFIER * 100 - 100  # Convert to percentage
        }
    ]


# ============================================================
# COMBAT VALUES
# ============================================================

def calculate_combat_values(
    unit,
    strength_modifiers=None,
    defence_modifiers=None
):
    strength = apply_modifiers(
        unit["strength"],
        strength_modifiers
    )

    defence = apply_modifiers(
        unit["defence"],
        defence_modifiers
    )

    return {
        "strength": strength,
        "defence": defence
    }


# ============================================================
# FORMATION SCALING
# ============================================================

def apply_formation_size(values, formation_size):
    return {
        "strength": values["strength"] * formation_size,
        "defence": values["defence"] * formation_size
    }

# ============================================================
# COMBAT ROLL
# ============================================================

def roll_combat(value):
    return random.randint(0, int(value))


# ============================================================
# DETERMINE OUTCOME
# ============================================================

def determine_outcome(attacker_roll, defender_roll):
    if attacker_roll > defender_roll:
        return "attacker_win"

    if defender_roll > attacker_roll:
        return "defender_win"

    return "tie"

# ============================================================
# APPLY CASUALTIES
# ============================================================

def apply_casualties(attacker_size, defender_size, outcome):

    if outcome == "attacker_win":
        defender_size -= 1

    elif outcome == "defender_win":
        attacker_size -= 1

    elif outcome == "tie":
        attacker_size -= 1
        defender_size -= 1

    # Formation size cannot go below zero
    attacker_size = max(0, attacker_size)
    defender_size = max(0, defender_size)

    return {
        "attacker_size": attacker_size,
        "defender_size": defender_size,
        "attacker_destroyed": attacker_size == 0,
        "defender_destroyed": defender_size == 0
    }

# ============================================================
# COMBINED ARMS
# ============================================================

def combined_arms_modifier(combined_arms, unit_level):
    if not combined_arms:
        return 0

    combined_arms_bonus = COMBINED_ARMS_BONUS * unit_level

    return combined_arms_bonus


# ============================================================
# ARTILLERY
# ============================================================

def resolve_artillery(attacker, defender, attacker_size, defender_size):
    attacker_is_artillery = attacker["unit_id"] in ARTILLERY_IDS
    defender_is_artillery = defender["unit_id"] in ARTILLERY_IDS

    # Attacker is not artillery
    if not attacker_is_artillery:
        return None

    # Both sides are artillery
    if attacker_is_artillery and defender_is_artillery:
        attacker_roll = roll_combat(
            attacker["strength"] * attacker_size
        )

        defender_roll = roll_combat(
            defender["strength"] * defender_size
        )

        outcome = determine_outcome(
            attacker_roll,
            defender_roll
        )

        casualties = apply_casualties(
            attacker_size,
            defender_size,
            outcome
        )

        return {
            "type": "artillery",
            "mode": "artillery_duel",
            "attacker_roll": attacker_roll,
            "defender_roll": defender_roll,
            "outcome": outcome,
            **casualties
        }

    # Attacker artillery firing at a non-artillery unit
    attacker_roll = roll_combat(
        attacker["strength"] * attacker_size
    )

    return {
        "type": "artillery",
        "mode": "artillery_attack",
        "attacker_roll": attacker_roll,
        "defender_roll": None,
        "outcome": "attacker_win",
        **apply_casualties(
            attacker_size,
            defender_size,
            "attacker_win"
        )
    }

# ============================================================
# ARTILLERY ATTACK
# ============================================================

def resolve_artillery_attack():
    roll = random.randint(1, 100)

    if roll <= ARTILLERY_SUPPRESSED_CHANCE:
        result = "suppressed"

    elif roll <= ARTILLERY_DESTROYED_CHANCE:
        result = "destroyed"

    else:
        result = "no_effect"

    return {
        "result": result,
        "roll": roll
    }

# ============================================================
# AIR DEFENCE
# ============================================================

def resolve_air_defence(attacker):
    if attacker["unit_id"] in STEALTH_IDS:
        hit_chance = ANTI_AIR_STEALTH_HIT_CHANCE
    else:
        hit_chance = ANTI_AIR_NON_STEALTH_HIT_CHANCE

    if random.random() < hit_chance:
        return {
            "intercepted": True,
            "chance": hit_chance
        }

    return {
        "intercepted": False,
        "chance": hit_chance
    }


# ============================================================
# SEAD
# ============================================================

def resolve_sead(attacker):
    if attacker["unit_id"] not in ATG_IDS:
        return {
            "attempted": False,
            "successful": False
        }

    success = random.random() < SEAD_SUCCESS_CHANCE

    return {
        "attempted": True,
        "successful": success
    }


# ============================================================
# AIR ATTACK
# ============================================================

def resolve_air_attack(attacker):
    # Air defence interception
    air_defence = resolve_air_defence(attacker)

    if air_defence["intercepted"]:
        return {
            "attack_stopped": True,
            "reason": "air_defence",
            "intercepted": True,
            "sead_attempted": False,
            "sead_successful": False
        }

    # SEAD attempt
    sead = resolve_sead(attacker)

    if sead["successful"]:
        return {
            "attack_stopped": False,
            "reason": "sead_success",
            "intercepted": False,
            "sead_attempted": True,
            "sead_successful": True
        }

    return {
        "attack_stopped": False,
        "reason": "air_defence_failed",
        "intercepted": False,
        "sead_attempted": sead["attempted"],
        "sead_successful": False
    }


# ============================================================
# SUBMARINE ATTACK
# ============================================================

def resolve_submarine_attack():
    roll = random.randint(1, 100)

    if roll <= SUBMARINE_ATTACK_FAILED_CHANCE:
        return {
            "result": "failed",
            "roll": roll
        }

    return {
        "result": "destroyed",
        "roll": roll
    }


# ============================================================
# SUBMARINE EVASION
# ============================================================

def resolve_submarine_evasion():
    roll = random.randint(1, 100)

    if roll <= ASW_SUCCESS_CHANCE:
        return {
            "evaded": True,
            "roll": roll
        }

    return {
        "evaded": False,
        "roll": roll
    }


# ============================================================
# HELICOPTER ATTACK RISK
# ============================================================

def resolve_helicopter_attack():
    roll = random.randint(1, 100)

    if roll <= HELICOPTER_DESTROYED_CHANCE:
        return {
            "destroyed": True,
            "roll": roll
        }

    return {
        "destroyed": False,
        "roll": roll
    }

# ============================================================
# AIR-TO-GROUND COMBAT
# ============================================================

def resolve_air_to_ground(attacker_strength, defender_defence):
    attacker_roll = roll_combat(attacker_strength)
    defender_roll = roll_combat(defender_defence)

    if attacker_roll > defender_roll:
        outcome = "hit"
    else:
        outcome = "no_effect"

    return {
        "attacker_roll": attacker_roll,
        "defender_roll": defender_roll,
        "outcome": outcome
    }


# ============================================================
# AIR-TO-SEA COMBAT
# ============================================================

def resolve_air_to_sea(attacker_strength, defender_defence):
    attacker_roll = roll_combat(attacker_strength)
    defender_roll = roll_combat(defender_defence)

    if attacker_roll > defender_roll:
        outcome = "hit"
    else:
        outcome = "no_effect"

    return {
        "attacker_roll": attacker_roll,
        "defender_roll": defender_roll,
        "outcome": outcome
    }

# ============================================================
# STRATEGIC BOMBING
# ============================================================

def resolve_strategic_bombing():
    roll = random.randint(1, 100)

    if roll <= STRATEGIC_BOMBING_SUCCESS_CHANCE:
        return {
            "successful": True,
            "roll": roll
        }

    return {
        "successful": False,
        "roll": roll
    }












# ============================================================
# STANDARD COMBAT
# ============================================================

def apply_modifiers(base_value, modifiers=None):
    if modifiers is None:
        modifiers = []

    value = base_value

    # Apply flat modifiers first
    for modifier in modifiers:
        if modifier["type"] == "flat":
            value += modifier["value"]

    # Apply percentage modifiers second
    for modifier in modifiers:
        if modifier["type"] == "percentage":
            value *= 1 + (modifier["value"] / 100)

    return value


def calculate_combat_values(unit, modifiers=None):
    strength = apply_modifiers(unit["strength"], modifiers)
    defence = apply_modifiers(unit["defence"], modifiers)

    return {
        "strength": strength,
        "defence": defence
    }


def apply_formation_size(values, formation_size):
    return {
        "strength": values["strength"] * formation_size,
        "defence": values["defence"] * formation_size
    }


def roll_combat(value):
    return random.randint(0, int(value))


def determine_outcome(attacker_roll, defender_roll):
    if attacker_roll > defender_roll:
        return "attacker_win"

    if defender_roll > attacker_roll:
        return "defender_win"

    return "tie"


def apply_casualties(attacker_size, defender_size, outcome):
    if outcome == "attacker_win":
        defender_size -= 1

    elif outcome == "defender_win":
        attacker_size -= 1

    elif outcome == "tie":
        attacker_size -= 1
        defender_size -= 1

    attacker_size = max(0, attacker_size)
    defender_size = max(0, defender_size)

    return {
        "attacker_size": attacker_size,
        "defender_size": defender_size,
        "attacker_destroyed": attacker_size == 0,
        "defender_destroyed": defender_size == 0
    }


def resolve_standard_combat(
    attacker,
    defender,
    attacker_formation_size,
    defender_formation_size,
    attacker_strength_modifiers=None,
    attacker_defence_modifiers=None,
    defender_strength_modifiers=None,
    defender_defence_modifiers=None
):
    attacker_values = calculate_combat_values(
        attacker,
        attacker_strength_modifiers,
        attacker_defence_modifiers
    )

    defender_values = calculate_combat_values(
        defender,
        defender_strength_modifiers,
        defender_defence_modifiers
    )

    attacker_values = apply_formation_size(
        attacker_values,
        attacker_formation_size
    )

    defender_values = apply_formation_size(
        defender_values,
        defender_formation_size
    )

    attacker_roll = roll_combat(
        attacker_values["strength"]
    )

    defender_roll = roll_combat(
        defender_values["defence"]
    )

    outcome = determine_outcome(
        attacker_roll,
        defender_roll
    )

    casualties = apply_casualties(
        attacker_formation_size,
        defender_formation_size,
        outcome
    )

    return {
        "attacker_roll": attacker_roll,
        "defender_roll": defender_roll,
        "outcome": outcome,
        "attacker_size": casualties["attacker_size"],
        "defender_size": casualties["defender_size"],
        "attacker_destroyed": casualties["attacker_destroyed"],
        "defender_destroyed": casualties["defender_destroyed"]
    }
