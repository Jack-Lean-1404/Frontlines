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

# ===== SPECIAL UNIT IDS =====
HELICOPTER_ID = {"8"}      
ARTILLERY_ID = {"9"}
MECHANISED_ARTILLERY_ID = {"10"}
COASTAL_DEFENCE_ID = {"11"}
ANTI_AIR_ID = {"12"}
SUBMARINE_ID = {"29"}
ANTI_AIR_ID = {"12"}
STEALTH_IDS = {"17", "18", "19"}
SUBMARINE_IDS = {"29"}          # your sub ID
ASW_IDS = {"27", "29", "23"}    # destroyer, sub, MPA

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

    # ===== SPECIAL RULES =====
    special = []

    attacker_id = attacker["id"]
    defender_id = defender["id"]

    print(attacker["id"], defender["id"])

    # ===== HELICOPTER =====
    if attacker_id in HELICOPTER_ID:
        roll = random.randint(0, 100)
        if roll > 25:
            special.append(f"Attack Helicopter remains operational. Roll: {roll}%")
        else:
            special.append(f"Attack Helicopter is destroyed. Roll: {roll}%")

        if roll < 25:
            if attacker_id in HELICOPTER_ID:
                outcome = "Attacker loses size"
            else:
                outcome = "Defender loses size"

    # ===== ARTILLERY LOGIC =====

    attacker_is_artillery = attacker_id in ARTILLERY_ID or attacker_id in MECHANISED_ARTILLERY_ID
    defender_is_artillery = defender_id in ARTILLERY_ID or defender_id in MECHANISED_ARTILLERY_ID


    # ===== CASE 1: ARTILLERY vs ARTILLERY =====
    if attacker_is_artillery and defender_is_artillery:
        roll = random.randint(0, 100)

        if roll > 50:
            special.append(f"Artillery Duel: Target Suppressed. Roll: {roll}%")
        elif 25 < roll <= 50:
            special.append(f"Artillery Duel: Target Destroyed. Roll: {roll}%")
        else:
            special.append(f"Artillery Duel: Missed. Roll: {roll}%")

        outcome = "See Special"


    # ===== CASE 2: ATTACKER IS ARTILLERY =====
    elif attacker_is_artillery:
        roll = random.randint(0, 100)

        if roll > 50:
            special.append(f"Artillery Strike: Target Suppressed. Roll: {roll}%")
        elif 25 < roll <= 50:
            special.append(f"Artillery Strike: Target Destroyed. Roll: {roll}%")
        else:
            special.append(f"Artillery Strike: Missed. Roll: {roll}%")
        
        outcome = "See Special"

        # Optional counter-battery ONLY if defender artillery
        if defender_is_artillery:
            cb_roll = random.randint(0, 100)

            if cb_roll > 50:
                special.append(f"Counter-Battery: Suppressed. Roll: {cb_roll}%")
            elif 25 < cb_roll <= 50:
                special.append(f"Counter-Battery: Destroyed. Roll: {cb_roll}%")
            else:
                special.append(f"Counter-Battery: Missed. Roll: {cb_roll}%")
        
            outcome = "See Special"


    # ===== CASE 3: DEFENDER IS ARTILLERY =====
    elif defender_is_artillery:
        # 🚫 NO artillery used — too close
        special.append("Artillery cannot fire (too close range)")

        # 👉 DO NOTHING ELSE — fall back to normal combat


    # ===== CASE 4: NO ARTILLERY =====
    else:
        pass  # normal combat already handled by your roll system

    # ===== FLAGS =====
    attacker_is_air = attacker["type"].lower() == "air"
    defender_is_air = defender["type"].lower() == "air"

    attacker_id = str(attacker["id"])
    defender_id = str(defender["id"])

    attacker_is_stealth = attacker_id in STEALTH_IDS
    defender_is_stealth = defender_id in STEALTH_IDS

    is_sead = attacker_is_air and defender_id in ANTI_AIR_ID


    # ===== SEAD (OVERRIDES AA) =====
    if is_sead:
        special.append("SEAD Operation Initiated")

        # ---- AA fires ONCE ----
        hit_chance = 20 if attacker_is_stealth else 80
        aa_roll = random.randint(1, 100)

        if aa_roll <= hit_chance:
            special.append(f"SEAD: Aircraft hit by AA. Roll: {aa_roll}% → Attacker loses size")
            outcome = "See Special"
        
        else:
            special.append(f"SEAD: Aircraft evaded AA. Roll: {aa_roll}%")
            outcome = "See Special"

            # ---- SEAD strike ----
            sead_roll = random.randint(1, 100)

            if sead_roll <= 60:
                special.append(f"SEAD successful. Roll: {sead_roll}% → Anti-Air destroyed")
                outcome = "See Special"
            else:
                special.append(f"SEAD failed. Roll: {sead_roll}%")
                outcome = "See Special"


    # ===== NORMAL ANTI-AIR (ONLY IF NOT SEAD) =====
    elif attacker_id in ANTI_AIR_ID and defender_is_air:

        hit_chance = 20 if defender_is_stealth else 80
        roll = random.randint(1, 100)

        if roll <= hit_chance:
            special.append(f"Anti-Air hit aircraft. Roll: {roll}% → Defender loses size")
            outcome = "See Special"
        else:
            special.append(f"Anti-Air missed. Roll: {roll}%")
            outcome = "See Special"


    elif defender_id in ANTI_AIR_ID and attacker_is_air:

        hit_chance = 20 if attacker_is_stealth else 80
        roll = random.randint(1, 100)

        if roll <= hit_chance:
            special.append(f"Anti-Air hit aircraft. Roll: {roll}% → Attacker loses size")
            outcome = "See Special"
        else:
            special.append(f"Anti-Air missed. Roll: {roll}%")
            outcome = "See Special"

    # ===== SUBMARINE & ASW =====

    attacker_id = str(attacker["id"])
    defender_id = str(defender["id"])

    attacker_is_sub = attacker_id in SUBMARINE_IDS
    defender_is_sub = defender_id in SUBMARINE_IDS

    attacker_is_naval = attacker["type"].lower() == "naval"
    defender_is_naval = defender["type"].lower() == "naval"

    attacker_is_asw = attacker_id in ASW_IDS
    defender_is_asw = defender_id in ASW_IDS


    # ===== SUBMARINE ATTACK (OVERRIDES NORMAL COMBAT) =====
    # Only when submarine is the attacker vs naval unit

    if attacker_is_sub and defender_is_naval:

        roll = random.randint(1, 100)

        if roll <= 25:
            special.append(f"Submarine attack failed. Roll: {roll}%")
            outcome = "See Special"
        
        else:
            special.append(f"Submarine strike successful. Roll: {roll}% → Defender loses size")
            outcome = "See Special"


    # ===== DEFENSIVE EVASION (WHEN SUB IS TARGETED) =====
    elif defender_is_sub:

        # Check if attacker can engage submarine (ASW)
        if attacker_is_asw:

            evade_roll = random.randint(1, 100)

            if evade_roll <= 50:
                special.append(f"Submarine evaded attack. Roll: {evade_roll}% → No damage")

                # 🚫 Cancel result of combat
                outcome = "See Special"

            else:
                special.append(f"Submarine hit by ASW. Roll: {evade_roll}%")

                outcome = "See Special"

        else:
            # Non-ASW units (you said handle later, but safe placeholder)
            special.append("Target is a submarine — attacker lacks ASW capability")

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