from flask import Flask, request, jsonify, render_template
import random
import csv

app = Flask(__name__)

FILENAME = 'UnitValues.csv'

# ===== MODIFIERS =====
RIVER_MODIFIER = 0.5
NO_HQ = 0.5
NO_SUPPLY = 0
NAT_GRD_CITY = 2
MECH_ARM = 4
AWACS = 1.5

# ===== LOAD ALL UNITS (FOR DROPDOWN) =====
def load_units():
    units = []

    with open(FILENAME, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            units.append({
                "id": row["id"],
                "name": row["name"]
            })

    return units

# ===== GET SINGLE UNIT =====
def get_unit(unit_id):
    with open(FILENAME, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            if row["id"] == unit_id:
                return row
    return None

# ===== CHECK IF SPECIAL =====
def is_special(unit):
    return unit["type"].lower() == "special"

def load_size_labels():
    sizes = {}

    with open("UnitSizes.csv", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            unit_id = str(row["unit_id"])   # MUST be string (matches HTML value)
            size = int(row["size"])
            label = row["label"]

            if unit_id not in sizes:
                sizes[unit_id] = {}

            sizes[unit_id][size] = label

    return sizes

# ===== SIZE SCALING (FINAL CORRECT VERSION) =====
def apply_size(unit, size):
    unit = unit.copy()

    base_strength = int(unit["strength"])
    base_defence = int(unit["defence"])

    if is_special(unit):
        multiplier = 2 ** (size - 1)
    else:
        multiplier = size

    unit["strength"] = base_strength * multiplier
    unit["defence"] = base_defence * multiplier

    return unit

# ===== APPLY MODIFIERS =====
def apply_modifiers(value, modifiers, size, is_attacker=True):
    breakdown = []
    result = value

    for mod in modifiers:
        if mod == "no_hq":
            result *= NO_HQ
            breakdown.append("No HQ ×0.5")

        elif mod == "no_supply":
            result = 0
            breakdown.append("No Supply = 0")

        elif mod == "river" and is_attacker:
            result *= RIVER_MODIFIER
            breakdown.append("River ×0.5")

        elif mod == "urban":
            bonus = NAT_GRD_CITY * size
            result += bonus
            breakdown.append(f"Urban +{bonus}")

        elif mod == "mech" and is_attacker:
            bonus = MECH_ARM * size
            result += bonus
            breakdown.append(f"Mech Bonus +{bonus}")

        elif mod == "awacs":
            result *= AWACS
            breakdown.append("AWACS ×1.5")

    return max(0, round(result)), breakdown

# ===== BATTLE TYPE (FIXED) =====
def get_battle_type(attacker, defender):
    a_type = attacker["type"].lower()
    d_type = defender["type"].lower()

    if a_type == "land" and d_type == "land":
        return "Land"
    elif a_type == "naval" and d_type == "naval":
        return "Naval"
    elif a_type == "air" and d_type == "air":
        return "Air"
    else:
        return "Hybrid"
    
@app.route("/get_unit_stats", methods=["POST"])
def get_unit_stats():
    data = request.json
    unit = get_unit(data["unit_id"])

    if not unit:
        return jsonify({"error": "Unit not found"})

    return jsonify({
        "strength": int(unit["strength"]),
        "defence": int(unit["defence"]),
        "type": unit["type"]
    })

# ===== ROUTES =====
@app.route("/")
def home():
    units = load_units()
    size_labels = load_size_labels()

    return render_template(
        "index.html",
        units=units,
        size_labels=size_labels
    )

@app.route("/simulate", methods=["POST"])
def simulate():

    data = request.json

    attacker_unit = get_unit(data["attacker_unit_id"])
    defender_unit = get_unit(data["defender_unit_id"])

    if not attacker_unit or not defender_unit:
        return jsonify({"error": "Invalid unit name"})

    attacker = apply_size(attacker_unit, int(data["attacker_size"]))
    defender = apply_size(defender_unit, int(data["defender_size"]))

    atk_base = int(attacker["strength"])
    def_base = int(defender["defence"])

    atk_mod, atk_break = apply_modifiers(
        atk_base,
        data["attacker_mods"],
        int(data["attacker_size"]),
        True
    )

    def_mod, def_break = apply_modifiers(
        def_base,
        data["defender_mods"],
        int(data["defender_size"]),
        False
    )

    atk_roll = random.randint(0, max(0, atk_mod))
    def_roll = random.randint(0, max(0, def_mod))

    # ===== RESULT =====
    if atk_roll > def_roll:
        outcome = "Defender loses size"
    elif atk_roll == def_roll:
        outcome = "Both lose size"
    else:
        outcome = "Attacker loses size"

    # ===== SPECIAL RULES (FIXED) =====
    special = []
    unit_name = attacker["name"].lower()

    if "helicopter" in unit_name:
        roll = random.randint(0, 100)
        special.append(f"Helicopter survival roll: {roll}%")
        if roll < 25:
            special.append("Helicopter loses size")

    if "artillery" in unit_name:
        roll = random.randint(0, 100)
        if roll > 50:
            special.append("Target suppressed")
        else:
            special.append("Target loses size")

    if "submarine" in unit_name:
        roll = random.randint(1, 4)
        special.append(f"Sub roll: {roll}")
        if roll == 1:
            outcome = "Attacker loses size"
        else:
            outcome = "Defender loses size"

    return jsonify({
        "battle_type": get_battle_type(attacker, defender),
        "attacker": {
            "base": atk_base,
            "modified": atk_mod,
            "roll": atk_roll,
            "modifiers": atk_break
        },
        "defender": {
            "base": def_base,
            "modified": def_mod,
            "roll": def_roll,
            "modifiers": def_break
        },
        "outcome": outcome,
        "special": special
    })

# ===== RUN =====
if __name__ == "__main__":
    app.run(debug=True)