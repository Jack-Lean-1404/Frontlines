import random


# ============================================================
# COMBAT CONSTANTS
# ============================================================

# Percentage-based roll modifiers
AWACS_MODIFIER = 1.5
DISORGANISED_MODIFIER = 0.5

# Flat roll bonuses
COMBINED_ARMS_BONUS = 1

# Artillery
ARTILLERY_SUPPRESSED_CHANCE = 50
ARTILLERY_DESTROYED_CHANCE = 25

# Air Defence
ANTI_AIR_NON_STEALTH_HIT_CHANCE = 80
ANTI_AIR_STEALTH_HIT_CHANCE = 20

# SEAD
SEAD_SUCCESS_CHANCE = 60

# Helicopter
HELICOPTER_DESTROYED_CHANCE = 25

# Submarine
SUBMARINE_ATTACK_FAILED_CHANCE = 25
SUBMARINE_EVASION_CHANCE = 50

# Strategic bombing
STRATEGIC_BOMBING_SUCCESS_CHANCE = 60


# ============================================================
# GENERIC CALCULATION HELPERS
# ============================================================

def apply_formation_size(base_value, formation_size):
    """
    Scale a combat value by formation size.

    Formation scaling happens before combat modifiers.
    """

    return int(base_value) * formation_size


def apply_percentage_modifiers(value, modifiers=None):
    """
    Apply percentage-based modifiers.

    Percentage modifiers affect the maximum possible roll.
    The final value is rounded down.
    """

    if modifiers is None:
        modifiers = []

    result = value

    for modifier in modifiers:

        if modifier["name"] == "AWACS":
            result *= AWACS_MODIFIER

        elif modifier["name"] == "Disorganised":
            result *= DISORGANISED_MODIFIER

    return int(result)


def roll_combat(max_value):
    """
    Roll from 0 to the calculated maximum value.

    Zero is a valid combat value.
    """

    return random.randint(
        0,
        max(0, int(max_value))
    )


def apply_roll_bonuses(roll, bonuses=None):
    """
    Apply flat bonuses after the random roll.

    These bonuses do NOT increase the maximum possible roll.
    """

    if bonuses is None:
        bonuses = []

    result = roll

    for bonus in bonuses:
        result += bonus["value"]

    return result


def determine_outcome(attacker_roll, defender_roll):
    """
    Determine the result of a standard opposed combat roll.
    """

    if attacker_roll > defender_roll:
        return "attacker_victory"

    if defender_roll > attacker_roll:
        return "defender_victory"

    return "tie"


def apply_casualties(
    outcome,
    attacker_size,
    defender_size
):
    """
    Apply the standard one-formation-size casualty rule.

    Attacker victory:
        Defender -1

    Defender victory:
        Attacker -1

    Tie:
        Both -1
    """

    attacker_after = attacker_size
    defender_after = defender_size

    if outcome == "attacker_victory":

        defender_after = max(
            0,
            defender_size - 1
        )

    elif outcome == "defender_victory":

        attacker_after = max(
            0,
            attacker_size - 1
        )

    elif outcome == "tie":

        attacker_after = max(
            0,
            attacker_size - 1
        )

        defender_after = max(
            0,
            defender_size - 1
        )

    return {
        "attacker_size": attacker_after,
        "defender_size": defender_after,
        "attacker_destroyed": attacker_after == 0,
        "defender_destroyed": defender_after == 0
    }


def calculate_combat_value(
    base_value,
    formation_size,
    percentage_modifiers=None,
    roll_bonuses=None
):
    """
    Calculate one side's combat roll.

    Order:

        Base value
        ↓
        Formation scaling
        ↓
        Percentage modifiers
        ↓
        Round down
        ↓
        Random roll
        ↓
        Flat roll bonuses
        ↓
        Final roll
    """

    if percentage_modifiers is None:
        percentage_modifiers = []

    if roll_bonuses is None:
        roll_bonuses = []

    # --------------------------------------------------------
    # FORMATION SCALING
    # --------------------------------------------------------

    formation_value = apply_formation_size(
        base_value,
        formation_size
    )

    # --------------------------------------------------------
    # PERCENTAGE MODIFIERS
    # --------------------------------------------------------

    maximum_roll = apply_percentage_modifiers(
        formation_value,
        percentage_modifiers
    )

    # --------------------------------------------------------
    # RANDOM ROLL
    # --------------------------------------------------------

    roll = roll_combat(
        maximum_roll
    )

    # --------------------------------------------------------
    # FLAT ROLL BONUSES
    # --------------------------------------------------------

    final_roll = apply_roll_bonuses(
        roll,
        roll_bonuses
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return {
        "base_value": int(base_value),
        "formation_size": formation_size,
        "formation_value": formation_value,
        "percentage_modifiers": percentage_modifiers,
        "maximum_roll": maximum_roll,
        "roll": roll,
        "roll_bonuses": roll_bonuses,
        "final_roll": final_roll
    }


def resolve_standard_combat(request):
    attacker = request["attacker"]
    defender = request["defender"]

    context = request.get("context", {})

    attacker_context = context.get("attacker", {})
    defender_context = context.get("defender", {})

    # --------------------------------------------------------
    # ATTACKER MODIFIERS
    # --------------------------------------------------------

    attacker_percentage_modifiers = []

    if attacker_context.get("awacs"):
        attacker_percentage_modifiers.append({
            "name": "AWACS"
        })

    if attacker_context.get("disorganised"):
        attacker_percentage_modifiers.append({
            "name": "Disorganised"
        })

    attacker_roll_bonuses = []

    if attacker_context.get("combined_arms"):
        attacker_roll_bonuses.append({
            "name": "Combined Arms",
            "value": (
                COMBINED_ARMS_BONUS
                * attacker["formation_size"]
            )
        })

    # --------------------------------------------------------
    # DEFENDER MODIFIERS
    # --------------------------------------------------------

    defender_percentage_modifiers = []

    if defender_context.get("awacs"):
        defender_percentage_modifiers.append({
            "name": "AWACS"
        })

    if defender_context.get("disorganised"):
        defender_percentage_modifiers.append({
            "name": "Disorganised"
        })

    # --------------------------------------------------------
    # CALCULATE ATTACKER STRENGTH
    # --------------------------------------------------------

    attacker_result = calculate_combat_value(
        base_value=attacker["strength"],
        formation_size=attacker["formation_size"],
        percentage_modifiers=attacker_percentage_modifiers,
        roll_bonuses=attacker_roll_bonuses
    )

    # --------------------------------------------------------
    # CALCULATE DEFENDER DEFENCE
    # --------------------------------------------------------

    defender_result = calculate_combat_value(
        base_value=defender["defence"],
        formation_size=defender["formation_size"],
        percentage_modifiers=defender_percentage_modifiers
    )

    # --------------------------------------------------------
    # DETERMINE OUTCOME
    # --------------------------------------------------------

    outcome = determine_outcome(
        attacker_result["final_roll"],
        defender_result["final_roll"]
    )

    # --------------------------------------------------------
    # APPLY CASUALTIES
    # --------------------------------------------------------

    casualties = apply_casualties(
        outcome,
        attacker["formation_size"],
        defender["formation_size"]
    )

    # --------------------------------------------------------
    # BUILD RESULT
    # --------------------------------------------------------

    return {
        "combat_type": "standard",
        "success": True,
        "outcome": outcome,

        "attacker": {
            "unit_id": attacker.get("unit_id"),
            "unit_name": attacker.get("unit_name"),
            "formation_size_before": attacker["formation_size"],
            "formation_size_after": casualties["attacker_size"],
            "destroyed": casualties["attacker_destroyed"],
            "calculation": attacker_result
        },

        "defender": {
            "unit_id": defender.get("unit_id"),
            "unit_name": defender.get("unit_name"),
            "formation_size_before": defender["formation_size"],
            "formation_size_after": casualties["defender_size"],
            "destroyed": casualties["defender_destroyed"],
            "calculation": defender_result
        },

        "effects": [],

        "description": (
            f"{attacker.get('unit_name', 'Attacker')} "
            f"{outcome.replace('_', ' ')} against "
            f"{defender.get('unit_name', 'Defender')}."
        )
    }


def resolve_artillery_combat(request):
    attacker = request["attacker"]
    defender = request["defender"]

    roll = random.randint(1, 100)

    # --------------------------------------------------------
    # DETERMINE ARTILLERY RESULT
    # --------------------------------------------------------

    if roll <= ARTILLERY_SUPPRESSED_CHANCE:
        outcome = "suppressed"

    elif roll <= (
        ARTILLERY_SUPPRESSED_CHANCE
        + ARTILLERY_DESTROYED_CHANCE
    ):
        outcome = "destroyed"

    else:
        outcome = "no_effect"

    # --------------------------------------------------------
    # BUILD EFFECTS
    # --------------------------------------------------------

    effects = []

    if outcome == "suppressed":
        effects.append({
            "type": "suppression",
            "target": defender.get("unit_id"),
            "description": "Target is suppressed and cannot move next turn."
        })

    elif outcome == "destroyed":
        effects.append({
            "type": "destruction",
            "target": defender.get("unit_id"),
            "description": "Target is destroyed."
        })

    # --------------------------------------------------------
    # BUILD RESULT
    # --------------------------------------------------------

    return {
        "combat_type": "artillery",
        "success": True,
        "outcome": outcome,

        "attacker": {
            "unit_id": attacker.get("unit_id"),
            "unit_name": attacker.get("unit_name")
        },

        "defender": {
            "unit_id": defender.get("unit_id"),
            "unit_name": defender.get("unit_name")
        },

        "roll": roll,

        "effects": effects,

        "description": (
            f"{attacker.get('unit_name', 'Artillery')} "
            f"artillery attack resulted in "
            f"{outcome.replace('_', ' ')}."
        )
    }


def resolve_air_defence(request):
    attacker = request["attacker"]   # Anti-Air unit
    defender = request["defender"]   # Aircraft

    capabilities = defender.get("capabilities", {})

    stealth = capabilities.get("stealth", False)

    if stealth:
        hit_chance = ANTI_AIR_STEALTH_HIT_CHANCE
    else:
        hit_chance = ANTI_AIR_NON_STEALTH_HIT_CHANCE

    roll = random.randint(1, 100)

    hit = roll <= hit_chance

    formation_loss = 1 if hit else 0

    defender_size_before = defender["formation_size"]

    defender_size_after = max(
        0,
        defender_size_before - formation_loss
    )

    destroyed = defender_size_after == 0

    effects = []

    if hit:
        effects.append({
            "type": "formation_loss",
            "target": defender.get("unit_id"),
            "amount": formation_loss,
            "description": (
                "Aircraft lost one formation size "
                "to anti-air interception."
            )
        })

    if destroyed:
        effects.append({
            "type": "destruction",
            "target": defender.get("unit_id"),
            "description": "Aircraft was destroyed by anti-air defence."
        })

    return {
        "combat_type": "air_defence",
        "success": True,

        "outcome": (
            "aircraft_destroyed"
            if destroyed
            else "aircraft_intercepted"
            if hit
            else "aircraft_survived"
        ),

        "attacker": {
            "unit_id": attacker.get("unit_id"),
            "unit_name": attacker.get("unit_name")
        },

        "defender": {
            "unit_id": defender.get("unit_id"),
            "unit_name": defender.get("unit_name"),
            "formation_size_before": defender_size_before,
            "formation_size_after": defender_size_after,
            "destroyed": destroyed
        },

        "roll": roll,
        "hit_chance": hit_chance,
        "stealth": stealth,
        "formation_loss": formation_loss,

        "effects": effects,

        "description": (
            f"{defender.get('unit_name', 'Aircraft')} "
            f"{'was intercepted by' if hit else 'evaded'} "
            f"{attacker.get('unit_name', 'Anti-Air')}."
        )
    }


def resolve_air_to_ground_combat(request):
    attacker = request["attacker"]
    defender = request["defender"]

    context = request.get("context", {})
    special = request.get("special", {})

    # --------------------------------------------------------
    # AIR DEFENCE
    # --------------------------------------------------------

    air_defence = None

    air_defence_unit = special.get("air_defence_unit")

    if (
        air_defence_unit is not None
        and not is_helicopter
    ):

        air_defence_request = {
            "combat_type": "air_defence",
            "attacker": air_defence_unit,
            "defender": attacker,
            "context": {},
            "special": {}
        }

        air_defence = resolve_air_defence(
            air_defence_request
        )

    # --------------------------------------------------------
    # AIRCRAFT FORMATION AFTER AIR DEFENCE
    # --------------------------------------------------------

    attacker_size_before = attacker["formation_size"]

    if air_defence is not None:

        attacker_size_after = (
            air_defence["defender"]["formation_size_after"]
        )

        attacker_destroyed = (
            air_defence["defender"]["destroyed"]
        )

    else:

        attacker_size_after = attacker_size_before
        attacker_destroyed = False

    # --------------------------------------------------------
    # AIRCRAFT DESTROYED BY AIR DEFENCE
    # --------------------------------------------------------

    if attacker_destroyed:

        effects = []

        if air_defence is not None:
            effects.extend(
                air_defence["effects"]
            )

        return {
            "combat_type": "air_to_ground",
            "success": True,
            "outcome": "aircraft_destroyed",

            "attacker": {
                "unit_id": attacker.get("unit_id"),
                "unit_name": attacker.get("unit_name"),
                "formation_size_before": attacker_size_before,
                "formation_size_after": attacker_size_after,
                "destroyed": True
            },

            "defender": {
                "unit_id": defender.get("unit_id"),
                "unit_name": defender.get("unit_name"),
                "formation_size_before": defender["formation_size"],
                "formation_size_after": defender["formation_size"],
                "destroyed": False
            },

            "air_defence": air_defence,

            "helicopter_risk": None,

            "attacker_calculation": None,
            "defender_calculation": None,

            "effects": effects,

            "description": (
                f"{attacker.get('unit_name', 'Aircraft')} "
                f"was destroyed by air defence before "
                f"attacking the ground target."
            )
        }

    # --------------------------------------------------------
    # COMBAT MODIFIERS
    # --------------------------------------------------------

    attacker_modifiers = []
    attacker_bonuses = []

    defender_modifiers = []

    attacker_context = context.get("attacker", {})
    defender_context = context.get("defender", {})

    # AWACS
    if attacker_context.get("awacs", False):

        attacker_modifiers.append({
            "name": "AWACS"
        })

    if defender_context.get("awacs", False):

        defender_modifiers.append({
            "name": "AWACS"
        })

    # Disorganised
    if attacker_context.get("disorganised", False):

        attacker_modifiers.append({
            "name": "Disorganised"
        })

    if defender_context.get("disorganised", False):

        defender_modifiers.append({
            "name": "Disorganised"
        })

    # Combined Arms
    if attacker_context.get("combined_arms", False):

        attacker_bonuses.append({
            "name": "Combined Arms",
            "value": (
                COMBINED_ARMS_BONUS *
                attacker_size_after
            )
        })

    # --------------------------------------------------------
    # COMBAT RESOLUTION
    # --------------------------------------------------------

    attacker_calculation = calculate_combat_value(
        base_value=attacker["strength"],
        formation_size=attacker_size_after,
        percentage_modifiers=attacker_modifiers,
        roll_bonuses=attacker_bonuses
    )

    defender_calculation = calculate_combat_value(
        base_value=defender["defence"],
        formation_size=defender["formation_size"],
        percentage_modifiers=defender_modifiers,
        roll_bonuses=[]
    )

    outcome = determine_outcome(
        attacker_calculation["final_roll"],
        defender_calculation["final_roll"]
    )

    # --------------------------------------------------------
    # GROUND CASUALTIES
    # --------------------------------------------------------

    defender_size_before = defender["formation_size"]

    defender_size_after = defender_size_before

    if outcome == "attacker_victory":

        defender_size_after = max(
            0,
            defender_size_before - 1
        )

    defender_destroyed = (
        defender_size_after == 0
    )

    # --------------------------------------------------------
    # HELICOPTER RISK
    # --------------------------------------------------------

    helicopter_risk = None

    is_helicopter = (
        attacker.get("capabilities", {})
        .get("helicopter", False)
    )

    if is_helicopter:

        helicopter_risk = resolve_helicopter_risk()

    # --------------------------------------------------------
    # EFFECTS
    # --------------------------------------------------------

    effects = []

    if air_defence is not None:

        effects.extend(
            air_defence["effects"]
        )

    if outcome == "attacker_victory":

        effects.append({
            "type": "formation_loss",
            "target": defender.get("unit_id"),
            "amount": 1,
            "description": (
                f"{defender.get('unit_name', 'Ground unit')} "
                f"lost 1 formation."
            )
        })

    if defender_destroyed:

        effects.append({
            "type": "destruction",
            "target": defender.get("unit_id"),
            "description": (
                f"{defender.get('unit_name', 'Ground unit')} "
                f"was destroyed."
            )
        })

    if (
        helicopter_risk is not None
        and helicopter_risk["destroyed"]
    ):

        effects.append({
            "type": "destruction",
            "target": attacker.get("unit_id"),
            "description": (
                f"{attacker.get('unit_name', 'Helicopter')} "
                f"was destroyed after the ground attack."
            )
        })

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return {
        "combat_type": "air_to_ground",
        "success": True,
        "outcome": outcome,

        "attacker": {
            "unit_id": attacker.get("unit_id"),
            "unit_name": attacker.get("unit_name"),
            "formation_size_before": attacker_size_before,
            "formation_size_after": attacker_size_after,
            "destroyed": (
                helicopter_risk is not None
                and helicopter_risk["destroyed"]
            )
        },

        "defender": {
            "unit_id": defender.get("unit_id"),
            "unit_name": defender.get("unit_name"),
            "formation_size_before": defender_size_before,
            "formation_size_after": defender_size_after,
            "destroyed": defender_destroyed
        },

        "air_defence": air_defence,

        "helicopter_risk": helicopter_risk,

        "attacker_calculation": attacker_calculation,

        "defender_calculation": defender_calculation,

        "effects": effects,

        "description": (
            f"{attacker.get('unit_name', 'Aircraft')} "
            f"attacked "
            f"{defender.get('unit_name', 'Ground unit')} "
            f"and the result was {outcome}."
        )
    }


def resolve_air_to_sea_combat(request):
    attacker = request["attacker"]
    defender = request["defender"]

    special = request.get("special", {})

    # --------------------------------------------------------
    # AIR DEFENCE
    # --------------------------------------------------------

    air_defence = None

    air_defence_unit = special.get("air_defence_unit")

    if air_defence_unit is not None:

        air_defence_request = {
            "combat_type": "air_defence",

            "attacker": air_defence_unit,

            "defender": attacker,

            "context": {},

            "special": {}
        }

        air_defence = resolve_air_defence(
            air_defence_request
        )

    # --------------------------------------------------------
    # AIRCRAFT FORMATION
    # --------------------------------------------------------

    attacker_size_before = attacker["formation_size"]

    if air_defence is not None:

        attacker_size_after = (
            air_defence["defender"]["formation_size_after"]
        )

        attacker_destroyed = (
            air_defence["defender"]["destroyed"]
        )

    else:

        attacker_size_after = attacker_size_before

        attacker_destroyed = False

    # --------------------------------------------------------
    # AIRCRAFT DESTROYED BY AIR DEFENCE
    # --------------------------------------------------------

    if attacker_destroyed:

        return {
            "combat_type": "air_to_sea",

            "success": True,

            "outcome": "aircraft_destroyed",

            "attacker": {
                "unit_id": attacker.get("unit_id"),
                "unit_name": attacker.get("unit_name"),
                "formation_size_before": attacker_size_before,
                "formation_size_after": attacker_size_after,
                "destroyed": True
            },

            "defender": {
                "unit_id": defender.get("unit_id"),
                "unit_name": defender.get("unit_name"),
                "formation_size_before": defender["formation_size"],
                "formation_size_after": defender["formation_size"],
                "destroyed": False
            },

            "air_defence": air_defence,

            "effects": air_defence["effects"],

            "description": (
                f"{attacker.get('unit_name', 'Aircraft')} "
                f"was destroyed by air defence before "
                f"completing the attack."
            )
        }

    # --------------------------------------------------------
    # ATTACK MODIFIERS
    # --------------------------------------------------------

    context = request.get("context", {})

    attacker_context = context.get("attacker", {})
    defender_context = context.get("defender", {})

    attacker_percentage_modifiers = []

    attacker_roll_bonuses = []

    defender_percentage_modifiers = []

    # --------------------------------------------------------
    # ATTACKER MODIFIERS
    # --------------------------------------------------------

    if attacker_context.get("awacs"):

        attacker_percentage_modifiers.append({
            "name": "AWACS"
        })

    if attacker_context.get("disorganised"):

        attacker_percentage_modifiers.append({
            "name": "Disorganised"
        })

    # --------------------------------------------------------
    # DEFENDER MODIFIERS
    # --------------------------------------------------------

    if defender_context.get("awacs"):

        defender_percentage_modifiers.append({
            "name": "AWACS"
        })

    if defender_context.get("disorganised"):

        defender_percentage_modifiers.append({
            "name": "Disorganised"
        })

    # --------------------------------------------------------
    # AIRCRAFT STRENGTH
    # --------------------------------------------------------

    attacker_result = calculate_combat_value(
        base_value=attacker["strength"],

        formation_size=attacker_size_after,

        percentage_modifiers=attacker_percentage_modifiers,

        roll_bonuses=attacker_roll_bonuses
    )

    # --------------------------------------------------------
    # NAVAL DEFENCE
    # --------------------------------------------------------

    defender_result = calculate_combat_value(
        base_value=defender["defence"],

        formation_size=defender["formation_size"],

        percentage_modifiers=defender_percentage_modifiers
    )

    # --------------------------------------------------------
    # DETERMINE OUTCOME
    # --------------------------------------------------------

    if attacker_result["final_roll"] > defender_result["final_roll"]:

        outcome = "attacker_victory"

        defender_size_after = max(
            0,
            defender["formation_size"] - 1
        )

    else:

        outcome = "no_effect"

        defender_size_after = defender["formation_size"]

    defender_destroyed = defender_size_after == 0

    # --------------------------------------------------------
    # BUILD EFFECTS
    # --------------------------------------------------------

    effects = []

    if air_defence is not None:

        effects.extend(
            air_defence["effects"]
        )

    if outcome == "attacker_victory":

        effects.append({
            "type": "formation_loss",

            "target": defender.get("unit_id"),

            "amount": 1,

            "description": (
                "Naval unit lost one formation size "
                "to the air attack."
            )
        })

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return {
        "combat_type": "air_to_sea",

        "success": True,

        "outcome": outcome,

        "attacker": {
            "unit_id": attacker.get("unit_id"),
            "unit_name": attacker.get("unit_name"),
            "formation_size_before": attacker_size_before,
            "formation_size_after": attacker_size_after,
            "destroyed": False,
            "calculation": attacker_result
        },

        "defender": {
            "unit_id": defender.get("unit_id"),
            "unit_name": defender.get("unit_name"),
            "formation_size_before": defender["formation_size"],
            "formation_size_after": defender_size_after,
            "destroyed": defender_destroyed,
            "calculation": defender_result
        },

        "air_defence": air_defence,

        "effects": effects,

        "description": (
            f"{attacker.get('unit_name', 'Aircraft')} "
            f"conducted an air-to-sea attack against "
            f"{defender.get('unit_name', 'Naval Unit')} "
            f"with outcome: "
            f"{outcome.replace('_', ' ')}."
        )
    }


def resolve_submarine_evasion(submarine):
    """
    Resolve a defending submarine's evasion attempt.

    Returns whether the submarine successfully evaded.
    """

    roll = random.randint(1, 100)

    evaded = roll <= SUBMARINE_EVASION_CHANCE

    return {
        "roll": roll,
        "evasion_chance": SUBMARINE_EVASION_CHANCE,
        "evaded": evaded
    }


def resolve_submarine_combat(request):
    attacker = request["attacker"]
    defender = request["defender"]

    effects = []

    # --------------------------------------------------------
    # DEFENDER SUBMARINE EVASION
    # --------------------------------------------------------

    defender_is_submarine = (
        defender.get("capabilities", {})
        .get("submarine", False)
    )

    evasion = None

    if defender_is_submarine:

        evasion = resolve_submarine_evasion(
            defender
        )

        if evasion["evaded"]:

            return {
                "combat_type": "submarine",
                "success": True,
                "outcome": "evaded",

                "attacker": {
                    "unit_id": attacker.get("unit_id"),
                    "unit_name": attacker.get("unit_name"),
                    "formation_size_before": attacker["formation_size"],
                    "formation_size_after": attacker["formation_size"],
                    "destroyed": False
                },

                "defender": {
                    "unit_id": defender.get("unit_id"),
                    "unit_name": defender.get("unit_name"),
                    "formation_size_before": defender["formation_size"],
                    "formation_size_after": defender["formation_size"],
                    "destroyed": False
                },

                "evasion": evasion,

                "attack": None,

                "effects": [],

                "description": (
                    f"{defender.get('unit_name', 'Submarine')} "
                    f"evaded the submarine attack."
                )
            }

    # --------------------------------------------------------
    # SUBMARINE ATTACK
    # --------------------------------------------------------

    roll = random.randint(1, 100)

    attack_success = (
        roll > SUBMARINE_ATTACK_FAILED_CHANCE
    )

    # --------------------------------------------------------
    # ATTACK FAILED
    # --------------------------------------------------------

    if not attack_success:

        return {
            "combat_type": "submarine",
            "success": True,
            "outcome": "attack_failed",

            "attacker": {
                "unit_id": attacker.get("unit_id"),
                "unit_name": attacker.get("unit_name"),
                "formation_size_before": attacker["formation_size"],
                "formation_size_after": attacker["formation_size"],
                "destroyed": False
            },

            "defender": {
                "unit_id": defender.get("unit_id"),
                "unit_name": defender.get("unit_name"),
                "formation_size_before": defender["formation_size"],
                "formation_size_after": defender["formation_size"],
                "destroyed": False
            },

            "evasion": evasion,

            "attack": {
                "roll": roll,
                "success_chance": (
                    100 - SUBMARINE_ATTACK_FAILED_CHANCE
                ),
                "success": False
            },

            "effects": [],

            "description": (
                f"{attacker.get('unit_name', 'Submarine')} "
                f"failed to successfully attack "
                f"{defender.get('unit_name', 'Naval Unit')}."
            )
        }

    # --------------------------------------------------------
    # ATTACK SUCCESSFUL
    # --------------------------------------------------------

    defender_size_before = defender["formation_size"]

    defender_size_after = max(
        0,
        defender_size_before - 1
    )

    defender_destroyed = (
        defender_size_after == 0
    )

    effects.append({
        "type": "formation_loss",
        "target": defender.get("unit_id"),
        "amount": 1,
        "description": (
            "Target lost one formation size "
            "to the successful submarine attack."
        )
    })

    if defender_destroyed:

        effects.append({
            "type": "destruction",
            "target": defender.get("unit_id"),
            "description": (
                "Target's formation size reached zero "
                "and the unit was destroyed."
            )
        })

    return {
        "combat_type": "submarine",
        "success": True,
        "outcome": (
            "target_destroyed"
            if defender_destroyed
            else "target_damaged"
        ),

        "attacker": {
            "unit_id": attacker.get("unit_id"),
            "unit_name": attacker.get("unit_name"),
            "formation_size_before": attacker["formation_size"],
            "formation_size_after": attacker["formation_size"],
            "destroyed": False
        },

        "defender": {
            "unit_id": defender.get("unit_id"),
            "unit_name": defender.get("unit_name"),
            "formation_size_before": defender_size_before,
            "formation_size_after": defender_size_after,
            "destroyed": defender_destroyed
        },

        "evasion": evasion,

        "attack": {
            "roll": roll,
            "success_chance": (
                100 - SUBMARINE_ATTACK_FAILED_CHANCE
            ),
            "success": True
        },

        "effects": effects,

        "description": (
            f"{attacker.get('unit_name', 'Submarine')} "
            f"successfully attacked "
            f"{defender.get('unit_name', 'Naval Unit')} "
            f"and reduced its formation from "
            f"{defender_size_before} to "
            f"{defender_size_after}."
        )
    }


def resolve_strategic_bombing_combat(request):
    attacker = request["attacker"]

    special = request.get("special", {})

    target_building = special.get("target_building")

    if target_building is None:
        raise ValueError(
            "Strategic bombing requires a target_building."
        )

    # --------------------------------------------------------
    # AIR DEFENCE
    # --------------------------------------------------------

    air_defence = None

    air_defence_unit = special.get("air_defence_unit")

    if air_defence_unit is not None:

        air_defence_request = {
            "combat_type": "air_defence",
            "attacker": air_defence_unit,
            "defender": attacker,
            "context": {},
            "special": {}
        }

        air_defence = resolve_air_defence(
            air_defence_request
        )

    # --------------------------------------------------------
    # AIRCRAFT FORMATION
    # --------------------------------------------------------

    attacker_size_before = attacker["formation_size"]

    if air_defence is not None:

        attacker_size_after = (
            air_defence["defender"]["formation_size_after"]
        )

        attacker_destroyed = (
            air_defence["defender"]["destroyed"]
        )

    else:

        attacker_size_after = attacker_size_before
        attacker_destroyed = False

    # --------------------------------------------------------
    # AIRCRAFT DESTROYED BY AIR DEFENCE
    # --------------------------------------------------------

    if attacker_destroyed:

        return {
            "combat_type": "strategic_bombing",
            "success": True,
            "outcome": "aircraft_destroyed",

            "attacker": {
                "unit_id": attacker.get("unit_id"),
                "unit_name": attacker.get("unit_name"),
                "formation_size_before": attacker_size_before,
                "formation_size_after": attacker_size_after,
                "destroyed": True
            },

            "target": {
                "building_id": target_building.get("building_id"),
                "building_name": target_building.get("building_name"),
                "destroyed": False
            },

            "air_defence": air_defence,

            "bombing": None,

            "effects": air_defence["effects"],

            "description": (
                f"{attacker.get('unit_name', 'Bomber')} "
                f"was destroyed by air defence before "
                f"reaching the target."
            )
        }

    # --------------------------------------------------------
    # BOMBING RESOLUTION
    # --------------------------------------------------------

    roll = random.randint(1, 100)

    bombing_success = (
        roll <= STRATEGIC_BOMBING_SUCCESS_CHANCE
    )

    # --------------------------------------------------------
    # BOMBING FAILED
    # --------------------------------------------------------

    if not bombing_success:

        effects = []

        if air_defence is not None:
            effects.extend(
                air_defence["effects"]
            )

        return {
            "combat_type": "strategic_bombing",
            "success": True,
            "outcome": "bombing_failed",

            "attacker": {
                "unit_id": attacker.get("unit_id"),
                "unit_name": attacker.get("unit_name"),
                "formation_size_before": attacker_size_before,
                "formation_size_after": attacker_size_after,
                "destroyed": False
            },

            "target": {
                "building_id": target_building.get("building_id"),
                "building_name": target_building.get("building_name"),
                "destroyed": False
            },

            "air_defence": air_defence,

            "bombing": {
                "roll": roll,
                "success_chance": STRATEGIC_BOMBING_SUCCESS_CHANCE,
                "success": False
            },

            "effects": effects,

            "description": (
                f"{attacker.get('unit_name', 'Bomber')} "
                f"failed to destroy "
                f"{target_building.get('building_name', 'building')}."
            )
        }

    # --------------------------------------------------------
    # BOMBING SUCCESSFUL
    # --------------------------------------------------------

    effects = []

    if air_defence is not None:
        effects.extend(
            air_defence["effects"]
        )

    effects.append({
        "type": "building_destruction",
        "target": target_building.get("building_id"),
        "description": (
            f"{target_building.get('building_name', 'Building')} "
            f"was destroyed by strategic bombing."
        )
    })

    return {
        "combat_type": "strategic_bombing",
        "success": True,
        "outcome": "building_destroyed",

        "attacker": {
            "unit_id": attacker.get("unit_id"),
            "unit_name": attacker.get("unit_name"),
            "formation_size_before": attacker_size_before,
            "formation_size_after": attacker_size_after,
            "destroyed": False
        },

        "target": {
            "building_id": target_building.get("building_id"),
            "building_name": target_building.get("building_name"),
            "destroyed": True
        },

        "air_defence": air_defence,

        "bombing": {
            "roll": roll,
            "success_chance": STRATEGIC_BOMBING_SUCCESS_CHANCE,
            "success": True
        },

        "effects": effects,

        "description": (
            f"{attacker.get('unit_name', 'Bomber')} "
            f"successfully destroyed "
            f"{target_building.get('building_name', 'building')}."
        )
    }

def resolve_helicopter_risk():
    roll = random.randint(1, 100)

    destroyed = roll <= HELICOPTER_DESTROYED_CHANCE

    return {
        "roll": roll,
        "destruction_chance": HELICOPTER_DESTROYED_CHANCE,
        "destroyed": destroyed
    }


def resolve_battle(request):
    combat_type = request["combat_type"]

    if combat_type == "standard":
        return resolve_standard_combat(request)

    if combat_type == "artillery":
        return resolve_artillery_combat(request)

    if combat_type == "air_defence":
        return resolve_air_defence(request)

    if combat_type == "air_to_ground":
        return resolve_air_to_ground_combat(request)
    
    if combat_type == "air_to_sea":
        return resolve_air_to_sea_combat(request)

    if combat_type == "submarine":
        return resolve_submarine_combat(request)

    if combat_type == "strategic_bombing":
        return resolve_strategic_bombing_combat(request)

    raise ValueError(
        f"Unsupported combat type: {combat_type}"
    )



if __name__ == "__main__":

    # ========================================================
    # TEST 1: NORMAL AIR-TO-GROUND ATTACK
    # ========================================================

    normal_air_to_ground = {
        "combat_type": "air_to_ground",

        "attacker": {
            "unit_id": 200,
            "unit_name": "Fighter",
            "unit_class": "Air",
            "unit_type": "Fighter",
            "strength": 10,
            "defence": 6,
            "formation_size": 3,
            "capabilities": {
                "helicopter": False,
                "stealth": False
            }
        },

        "defender": {
            "unit_id": 201,
            "unit_name": "Infantry",
            "unit_class": "Ground",
            "unit_type": "Infantry",
            "strength": 5,
            "defence": 8,
            "formation_size": 3,
            "capabilities": {}
        },

        "context": {
            "attacker": {},
            "defender": {}
        },

        "special": {}
    }

    result_1 = resolve_battle(
        normal_air_to_ground
    )

    print("\n")
    print("=" * 60)
    print("TEST 1: NORMAL AIR-TO-GROUND")
    print("=" * 60)

    print("\nOutcome:")
    print(result_1["outcome"])

    print("\nAircraft:")
    print(
        "Formation:",
        result_1["attacker"]["formation_size_before"],
        "->",
        result_1["attacker"]["formation_size_after"]
    )

    print(
        "Destroyed:",
        result_1["attacker"]["destroyed"]
    )

    print("\nGround Unit:")
    print(
        "Formation:",
        result_1["defender"]["formation_size_before"],
        "->",
        result_1["defender"]["formation_size_after"]
    )

    print(
        "Destroyed:",
        result_1["defender"]["destroyed"]
    )

    print("\nHelicopter Risk:")
    print(
        result_1["helicopter_risk"]
    )

    print("\nEffects:")

    for effect in result_1["effects"]:
        print(effect)

    print("\nDescription:")
    print(result_1["description"])


    # ========================================================
    # TEST 2: HELICOPTER AIR-TO-GROUND ATTACK
    # ========================================================

    helicopter_attack = {
        "combat_type": "air_to_ground",

        "attacker": {
            "unit_id": 210,
            "unit_name": "Attack Helicopter",
            "unit_class": "Air",
            "unit_type": "Attack Helicopter",
            "strength": 10,
            "defence": 6,
            "formation_size": 3,
            "capabilities": {
                "helicopter": True,
                "stealth": False
            }
        },

        "defender": {
            "unit_id": 211,
            "unit_name": "Mechanised Infantry",
            "unit_class": "Ground",
            "unit_type": "Mechanised Infantry",
            "strength": 8,
            "defence": 9,
            "formation_size": 3,
            "capabilities": {}
        },

        "context": {
            "attacker": {},
            "defender": {}
        },

        "special": {}
    }

    result_2 = resolve_battle(
        helicopter_attack
    )

    print("\n")
    print("=" * 60)
    print("TEST 2: HELICOPTER AIR-TO-GROUND")
    print("=" * 60)

    print("\nOutcome:")
    print(result_2["outcome"])

    print("\nHelicopter:")
    print(
        "Formation:",
        result_2["attacker"]["formation_size_before"],
        "->",
        result_2["attacker"]["formation_size_after"]
    )

    print(
        "Destroyed:",
        result_2["attacker"]["destroyed"]
    )

    print("\nGround Unit:")
    print(
        "Formation:",
        result_2["defender"]["formation_size_before"],
        "->",
        result_2["defender"]["formation_size_after"]
    )

    print(
        "Destroyed:",
        result_2["defender"]["destroyed"]
    )

    print("\nHelicopter Risk:")

    if result_2["helicopter_risk"] is not None:

        print(
            "Roll:",
            result_2["helicopter_risk"]["roll"]
        )

        print(
            "Destruction Chance:",
            result_2["helicopter_risk"]
            ["destruction_chance"]
        )

        print(
            "Destroyed:",
            result_2["helicopter_risk"]
            ["destroyed"]
        )

    else:

        print("No helicopter risk applied.")

    print("\nEffects:")

    for effect in result_2["effects"]:
        print(effect)

    print("\nDescription:")
    print(result_2["description"])


    # ========================================================
    # TEST 3: HELICOPTER WITH AIR DEFENCE
    # ========================================================

    helicopter_with_aa = {
        "combat_type": "air_to_ground",

        "attacker": {
            "unit_id": 220,
            "unit_name": "Attack Helicopter",
            "unit_class": "Air",
            "unit_type": "Attack Helicopter",
            "strength": 10,
            "defence": 6,
            "formation_size": 3,
            "capabilities": {
                "helicopter": True,
                "stealth": False
            }
        },

        "defender": {
            "unit_id": 221,
            "unit_name": "Tank Battalion",
            "unit_class": "Ground",
            "unit_type": "Armoured",
            "strength": 12,
            "defence": 10,
            "formation_size": 3,
            "capabilities": {}
        },

        "context": {
            "attacker": {},
            "defender": {}
        },

        "special": {

            "air_defence_unit": {
                "unit_id": 222,
                "unit_name": "Anti-Air Battery",
                "unit_class": "Ground",
                "unit_type": "Anti-Air",
                "strength": 5,
                "defence": 8,
                "formation_size": 2,
                "capabilities": {
                    "anti_air": True
                }
            }
        }
    }

    result_3 = resolve_battle(
        helicopter_with_aa
    )

    print("\n")
    print("=" * 60)
    print("TEST 3: HELICOPTER WITH AIR DEFENCE")
    print("=" * 60)

    print("\nOutcome:")
    print(result_3["outcome"])

    print("\nAir Defence:")

    if result_3["air_defence"] is not None:

        print(
            "Roll:",
            result_3["air_defence"]["roll"]
        )

        print(
            "Hit Chance:",
            result_3["air_defence"]["hit_chance"]
        )

        print(
            "Formation:",
            result_3["air_defence"]["defender"]
            ["formation_size_before"],
            "->",
            result_3["air_defence"]["defender"]
            ["formation_size_after"]
        )

    print("\nHelicopter:")

    print(
        "Formation:",
        result_3["attacker"]["formation_size_before"],
        "->",
        result_3["attacker"]["formation_size_after"]
    )

    print(
        "Destroyed:",
        result_3["attacker"]["destroyed"]
    )

    print("\nGround Unit:")

    print(
        "Formation:",
        result_3["defender"]["formation_size_before"],
        "->",
        result_3["defender"]["formation_size_after"]
    )

    print(
        "Destroyed:",
        result_3["defender"]["destroyed"]
    )

    print("\nHelicopter Risk:")

    if result_3["helicopter_risk"] is not None:

        print(
            "Roll:",
            result_3["helicopter_risk"]["roll"]
        )

        print(
            "Destruction Chance:",
            result_3["helicopter_risk"]
            ["destruction_chance"]
        )

        print(
            "Destroyed:",
            result_3["helicopter_risk"]
            ["destroyed"]
        )

    else:

        print("No helicopter risk applied.")

    print("\nEffects:")

    for effect in result_3["effects"]:
        print(effect)

    print("\nDescription:")
    print(result_3["description"])