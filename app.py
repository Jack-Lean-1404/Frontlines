from importlib import resources

from flask import Flask, render_template, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from datetime import datetime
from flask import redirect, url_for
import mysql.connector
import os

from economy import (
    get_money_income,
    get_money_upkeep,
    get_oil_production,
    get_oil_consumption,
    get_cm_production,
    get_cm_consumption,
    get_rm_production,
    get_rm_consumption
)

load_dotenv(dotenv_path=".env")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# print(os.getenv("SECRET_KEY"))

# DATABASE CONNECTION FUNCTION Witth the following code, we can connect to the database whenever we need to by calling the get_db_connection() function
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


# ROUTES

# Homepage
@app.route("/")
def home():
    return render_template("index.html")

# Signup/Login Page
@app.route("/access")
def access():
    return render_template("access.html")

# Player Dashboard
@app.route("/dashboard")
def dashboard():

    # Check login 
    if "user_id" not in session:
        return redirect(url_for("access"))



    db = get_db_connection()

    cursor = db.cursor(dictionary=True)

    

    # -------------------------
    # GET NATION
    # -------------------------
    cursor.execute("""
        SELECT *
        FROM nations
        WHERE nation_id = %s
    """, (session["nation_id"],))

    nation = cursor.fetchone()

    nation_id = nation["nation_id"]

    money_income = get_money_income(cursor, nation_id)
    money_upkeep = get_money_upkeep(cursor, nation_id)
    money_net = money_income - money_upkeep

    oil_production = get_oil_production(cursor, nation_id)
    oil_consumption = get_oil_consumption(cursor, nation_id)
    oil_net = oil_production - oil_consumption

    cm_production = get_cm_production(cursor, nation_id)
    cm_consumption = get_cm_consumption(cursor, nation_id)
    cm_net = cm_production - cm_consumption

    rm_production = get_rm_production(cursor, nation_id)
    rm_consumption = get_rm_consumption(cursor, nation_id)
    rm_net = rm_production - rm_consumption

    # -------------------------
    # GET RESOURCES
    # -------------------------
    cursor.execute("""
        SELECT
            nation_resources.resource_id,
            nation_resources.amount,
            resources.name,
            resources.measurement_convention
        FROM nation_resources

        JOIN resources
            ON nation_resources.resource_id = resources.resource_id

        WHERE nation_resources.nation_id = %s
    """, (session["nation_id"],))

    resources = cursor.fetchall()

    resource_values = {}

    for resource in resources:

        resource_values[resource["resource_id"]] = {

            "amount": resource["amount"],
            "unit": resource["measurement_convention"]

        }

    # -------------------------
    # NATION SUMMARY
    # -------------------------

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM nation_buildings
        WHERE nation_id = %s
    """, (nation_id,))

    buildings = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM nation_units
        WHERE nation_id = %s
        AND status = 'active'
    """, (nation_id,))

    units = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM building_queue bq

        JOIN building_lines bl
            ON bq.line_id = bl.line_id

        WHERE bl.nation_id = %s
    """, (nation_id,))

    construction = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM production_queue pq

        JOIN production_lines pl
            ON pq.line_id = pl.line_id

        WHERE pl.nation_id = %s
    """, (nation_id,))

    production = cursor.fetchone()["total"]

    summary = {

        "cities": nation["city_count"],

        "capital": nation["capital_count"],

        "buildings": buildings,

        "units": units,

        "military_score": nation["military_score"],

        "economic_score": nation["economic_score"],

        "construction": construction,

        "production": production

    }

    # -------------------------
    # MILITARY OVERVIEW
    # -------------------------

    cursor.execute("""
        SELECT
            u.unit_name,
            u.unit_class,
            uot.tier_name,
            nu.tier_level,
            COUNT(*) AS total

        FROM nation_units nu

        JOIN units u
            ON nu.unit_id = u.unit_id

        JOIN unit_organisation_tiers uot
            ON uot.tier_type = u.unit_group
        AND uot.tier = nu.tier_level

        WHERE
            nu.nation_id = %s
        AND
            nu.status = 'active'

        GROUP BY
            u.unit_name,
            u.unit_class,
            nu.tier_level,
            uot.tier_name

        ORDER BY
            FIELD(u.unit_class, 'land', 'air', 'sea', 'special'),
            u.unit_name,
            nu.tier_level
    """, (nation_id,))

    rows = cursor.fetchall()

    military = {
        "land": {},
        "air": {},
        "sea": {},
        "special": {}
    }

    for row in rows:

        unit_class = row["unit_class"]

        unit_name = row["unit_name"]

        if unit_class not in military:

            military[unit_class] = {}

        if unit_name not in military[unit_class]:

            military[unit_class][unit_name] = []

        military[unit_class][unit_name].append({

            "tier": row["tier_name"],

            "count": row["total"]

        })

    # -------------------------
    # INFRASTRUCTURE
    # -------------------------

    cursor.execute("""
        SELECT
            b.building_type,
            b.building_name,
            COUNT(*) AS total

        FROM nation_buildings nb

        JOIN buildings b
            ON nb.building_id = b.building_id

        WHERE
            nb.nation_id = %s

        GROUP BY
            b.building_type,
            b.building_name

        ORDER BY
            b.building_type,
            b.building_name
    """, (nation_id,))

    rows = cursor.fetchall()

    titles = {

        "district": "Districts",

        "infrastructure": "Infrastructure",

        "facility": "Facilities"

    }

    infrastructure = {}

    for row in rows:

        building_type = titles.get(
            row["building_type"].lower(),
            row["building_type"].title()
        )

        if building_type not in infrastructure:

            infrastructure[building_type] = {}

        infrastructure[building_type][row["building_name"]] = row["total"]

    # -------------------------
    # ACTIVE CONSTRUCTION
    # -------------------------

    cursor.execute("""
        SELECT

            bl.line_name,

            b.building_name,

            bq.turns_remaining,

            b.build_time

        FROM building_lines bl

        LEFT JOIN building_queue bq
            ON bl.line_id = bq.line_id

        LEFT JOIN buildings b
            ON bq.building_id = b.building_id

        WHERE
            bl.nation_id = %s
        AND
            bq.status = 'building'

        ORDER BY bl.line_id
    """, (nation_id,))

    construction_lines = cursor.fetchall()

    for row in construction_lines:

        if row["build_time"]:

            row["progress"] = (
                (row["build_time"] - row["turns_remaining"])
                / row["build_time"]
            ) * 100

        else:

            row["progress"] = 0

    # -------------------------
    # ACTIVE UNIT PRODUCTION
    # -------------------------

    cursor.execute("""
        SELECT

            pl.line_name,

            u.unit_name,

            pq.turns_remaining,

            pq.tier,

            u.build_time,

            t.tier_name

        FROM production_lines pl

        LEFT JOIN production_queue pq
            ON pl.line_id = pq.line_id

        LEFT JOIN units u
            ON pq.unit_id = u.unit_id

        LEFT JOIN unit_organisation_tiers t
            ON
                t.tier_type = u.unit_group
            AND
                t.tier = pq.tier

        WHERE
            pl.nation_id = %s
        AND
            pq.status = 'building'

        ORDER BY pl.line_id
    """, (nation_id,))

    production_lines = cursor.fetchall()

    for row in production_lines:

        if row["build_time"]:

            row["progress"] = (
                (row["build_time"] - row["turns_remaining"])
                / row["build_time"]
            ) * 100

        else:

            row["progress"] = 0



    # -------------------------
    # GET MONEY HISTORY FOR CHART
    # -------------------------
    cursor.execute("""

        SELECT
            gt.turn_id,
            rh.amount
        FROM resource_history rh
        JOIN game_turns gt
            ON rh.turn_id = gt.turn_id
        WHERE rh.nation_id = %s
        AND rh.resource_id = %s
        ORDER BY gt.turn_id ASC
    """, (nation_id, 1))

    money_history = cursor.fetchall()

    turn_labels = []
    money_values = []

    for row in money_history:
        turn_labels.append(row["turn_id"])
        money_values.append(row["amount"])

    cursor.close()
    db.close()

    print(construction_lines)
    print(production_lines)


    return render_template(
        "dashboard.html",
        current_page="overview",
        resources=resources,
        resource_values=resource_values,
        summary=summary,
        turn_labels=turn_labels,
        money_values=money_values,
        military=military,
        infrastructure=infrastructure,
        construction_lines=construction_lines,
        production_lines=production_lines,
        money_income=money_income,
        money_upkeep=money_upkeep,
        money_net=money_net,

        oil_production=oil_production,
        oil_consumption=oil_consumption,
        oil_net=oil_net,

        cm_production=cm_production,
        cm_consumption=cm_consumption,
        cm_net=cm_net,

        rm_production=rm_production,
        rm_consumption=rm_consumption,
        rm_net=rm_net,
    )

@app.route("/economy")
def economy():
    return render_template("economy.html", current_page="economy")


@app.route("/research")
def research():
    return render_template("research.html", current_page="research")

@app.route("/diplomacy")
def diplomacy():

    nation_id = session["nation_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
    SELECT

        n.nation_id,
        n.name,
        n.flag,
        n.military_score,
        n.economic_score,

        dr.relationship,

        a.alliance_name,
        a.alliance_code

    FROM diplomatic_relations dr

    JOIN nations n

    ON (

        (dr.nation_a = %s AND dr.nation_b = n.nation_id)

        OR

        (dr.nation_b = %s AND dr.nation_a = n.nation_id)

    )

    LEFT JOIN alliance_members am

    ON n.nation_id = am.nation_id

    LEFT JOIN alliances a

    ON am.alliance_id = a.alliance_id

    ORDER BY n.name

    """,
    (
        nation_id,
        nation_id
    ))

    relations = cursor.fetchall()

    print(relations)

    cursor.execute("""
        SELECT

            a.alliance_id,
            a.alliance_code,
            a.alliance_name,
            a.founder_nation_id,
            a.created_turn,

            n.name AS founder_name

        FROM alliance_members am

        JOIN alliances a
            ON am.alliance_id = a.alliance_id

        JOIN nations n
            ON a.founder_nation_id = n.nation_id

        WHERE am.nation_id = %s

    """, (nation_id,))

    current_alliance = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "diplomacy.html",
        current_page="diplomacy",
        relations=relations,
        current_alliance=current_alliance
    )


@app.route("/diplomacy/<int:nation_id>")
def diplomacy_nation(nation_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
    SELECT

        n.nation_id,
        n.name,
        n.flag,
        n.capital_count,
        n.city_count,
        n.military_score,
        n.economic_score,

        a.alliance_name,
        a.alliance_code

    FROM nations n

    LEFT JOIN alliance_members am

    ON n.nation_id = am.nation_id

    LEFT JOIN alliances a

    ON am.alliance_id = a.alliance_id

    WHERE

        n.nation_id = %s

    """, (nation_id,))

    nation = cursor.fetchone()

    cursor.execute("""
    SELECT relationship

    FROM diplomatic_relations

    WHERE

    (nation_a=%s AND nation_b=%s)

    OR

    (nation_b=%s AND nation_a=%s)

    """,
    (
        session["nation_id"],
        nation_id,

        session["nation_id"],
        nation_id
    ))

    relationship = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(

        "diplomacy_nation.html",

        current_page="diplomacy",

        viewed_nation=nation,

        relationship=relationship

    )

@app.route("/alliance/create", methods=["GET", "POST"])
def create_alliance():

    nation_id = session["nation_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        alliance_name = request.form["alliance_name"].strip()
        alliance_code = request.form["alliance_code"].strip().upper()

        # Validate alliance name
        if not alliance_name:

            cursor.close()
            conn.close()

            return "Alliance name is required."

        # Validate alliance code
        if len(alliance_code) != 3 or not alliance_code.isalpha():

            cursor.close()
            conn.close()

            return "Alliance code must be exactly 3 letters."

        # Check whether the code already exists
        cursor.execute("""
            SELECT alliance_id
            FROM alliances
            WHERE alliance_code = %s
        """, (alliance_code,))

        existing_alliance = cursor.fetchone()

        if existing_alliance:

            cursor.close()
            conn.close()

            return "That alliance code is already in use."

        # Check whether the nation is already in an alliance
        cursor.execute("""
            SELECT alliance_member_id
            FROM alliance_members
            WHERE nation_id = %s
        """, (nation_id,))

        existing_membership = cursor.fetchone()

        if existing_membership:

            cursor.close()
            conn.close()

            return "Your nation is already a member of an alliance."

        # Get current turn
        cursor.execute("""
            SELECT current_turn
            FROM game_state
            LIMIT 1
        """)

        game_state = cursor.fetchone()

        current_turn = game_state["current_turn"]

        # Create alliance
        cursor.execute("""
            INSERT INTO alliances (
                alliance_code,
                alliance_name,
                founder_nation_id,
                created_turn
            )
            VALUES (%s, %s, %s, %s)
        """, (
            alliance_code,
            alliance_name,
            nation_id,
            current_turn
        ))

        alliance_id = cursor.lastrowid

        # Add founder as first member
        cursor.execute("""
            INSERT INTO alliance_members (
                alliance_id,
                nation_id,
                joined_turn
            )
            VALUES (%s, %s, %s)
        """, (
            alliance_id,
            nation_id,
            current_turn
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(
            url_for(
                "alliance",
                alliance_id=alliance_id
            )
        )

    cursor.close()
    conn.close()

    return render_template(
        "create_alliance.html",
        current_page="diplomacy"
    )

@app.route("/alliance/<int:alliance_id>")
def alliance(alliance_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get alliance information
    cursor.execute("""
        SELECT

            a.alliance_id,
            a.alliance_code,
            a.alliance_name,
            a.founder_nation_id,
            a.created_turn,

            n.name AS founder_name

        FROM alliances a

        JOIN nations n
            ON a.founder_nation_id = n.nation_id

        WHERE a.alliance_id = %s

    """, (alliance_id,))

    alliance = cursor.fetchone()

    # Make sure alliance exists
    if not alliance:

        cursor.close()
        conn.close()

        return "Alliance not found.", 404

    # Get alliance members
    cursor.execute("""
        SELECT

            n.nation_id,
            n.name,
            n.flag,
            am.joined_turn,

            CASE

                WHEN n.nation_id = a.founder_nation_id

                THEN 1

                ELSE 0

            END AS is_leader

        FROM alliance_members am

        JOIN nations n
            ON am.nation_id = n.nation_id

        JOIN alliances a
            ON am.alliance_id = a.alliance_id

        WHERE am.alliance_id = %s

        ORDER BY is_leader DESC, n.name

    """, (alliance_id,))

    members = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(

        "alliance.html",

        current_page="diplomacy",

        alliance=alliance,

        members=members

    )

@app.route(
    "/alliance/<int:alliance_id>/invite",
    methods=["GET", "POST"]
)
def invite_to_alliance(alliance_id):

    nation_id = session["nation_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Check that current nation belongs to the alliance
    cursor.execute("""
        SELECT alliance_member_id
        FROM alliance_members
        WHERE alliance_id = %s
        AND nation_id = %s
    """, (
        alliance_id,
        nation_id
    ))

    membership = cursor.fetchone()

    if not membership:

        cursor.close()
        conn.close()

        return "You are not a member of this alliance.", 403

    # Get alliance information
    cursor.execute("""
        SELECT
            alliance_id,
            alliance_name,
            alliance_code
        FROM alliances
        WHERE alliance_id = %s
    """, (alliance_id,))

    alliance = cursor.fetchone()

    if not alliance:

        cursor.close()
        conn.close()

        return "Alliance not found.", 404

    # Handle invitation
    if request.method == "POST":

        invited_nation_id = request.form["nation_id"]

        # Check nation exists
        cursor.execute("""
            SELECT
                nation_id,
                name
            FROM nations
            WHERE nation_id = %s
        """, (invited_nation_id,))

        invited_nation = cursor.fetchone()

        if not invited_nation:

            cursor.close()
            conn.close()

            return "Nation not found.", 404

        # Prevent inviting yourself
        if int(invited_nation_id) == nation_id:

            cursor.close()
            conn.close()

            return "You cannot invite your own nation.", 400

        # Check whether nation is already in an alliance
        cursor.execute("""
            SELECT alliance_member_id
            FROM alliance_members
            WHERE nation_id = %s
        """, (invited_nation_id,))

        existing_membership = cursor.fetchone()

        if existing_membership:

            cursor.close()
            conn.close()

            return "That nation is already a member of an alliance.", 400

        # Check for existing pending invitation
        cursor.execute("""
            SELECT invitation_id
            FROM alliance_invitations
            WHERE alliance_id = %s
            AND nation_id = %s
            AND status = 'Pending'
        """, (
            alliance_id,
            invited_nation_id
        ))

        existing_invitation = cursor.fetchone()

        if existing_invitation:

            cursor.close()
            conn.close()

            return "That nation already has a pending invitation.", 400

        # Get current turn
        cursor.execute("""
            SELECT current_turn
            FROM game_state
            LIMIT 1
        """)

        game_state = cursor.fetchone()

        current_turn = game_state["current_turn"]

        # Create invitation
        cursor.execute("""
            INSERT INTO alliance_invitations (
                alliance_id,
                nation_id,
                invited_turn,
                status
            )
            VALUES (%s, %s, %s, 'Pending')
        """, (
            alliance_id,
            invited_nation_id,
            current_turn
        ))

        invitation_id = cursor.lastrowid

        # Create Recent Event
        cursor.execute("""
            INSERT INTO nation_events (
                nation_id,
                event_type,
                title,
                message,
                created_turn
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            invited_nation_id,
            "diplomacy",
            "Alliance Invitation",
            f"{alliance['alliance_name']} [{alliance['alliance_code']}] has invited you to join.",
            current_turn
        ))

        # Create notification
        cursor.execute("""
            INSERT INTO notifications (
                nation_id,
                type,
                title,
                message,
                icon,
                created_turn,
                reference_id,
                persistent
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            invited_nation_id,
            "alliance_invitation",
            "Alliance Invitation",
            f"{alliance['alliance_name']} [{alliance['alliance_code']}] has invited you to join.",
            "🤝",
            current_turn,
            invitation_id,
            True
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(
            url_for(
                "alliance",
                alliance_id=alliance_id
            )
        )

    # Get nations that can be invited
    cursor.execute("""
        SELECT
            n.nation_id,
            n.name,
            n.flag

        FROM nations n

        LEFT JOIN alliance_members am
            ON n.nation_id = am.nation_id

        WHERE am.nation_id IS NULL
        AND n.nation_id != %s

        ORDER BY n.name
    """, (nation_id,))

    available_nations = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "invite_to_alliance.html",
        current_page="diplomacy",
        alliance=alliance,
        available_nations=available_nations
    )

# Production Page
@app.route("/production")
def production():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM units
        WHERE is_active = 1
        ORDER BY money_cost ASC
    """)

    units = cursor.fetchall()

     # Organisation Levels
    cursor.execute("""
        SELECT *
        FROM unit_organisation_tiers
        ORDER BY tier_type, tier
    """)
    organisation_rows = cursor.fetchall()

    cursor.close()
    conn.close()

    organisation_names = {}

    for row in organisation_rows:

        group_id = row["tier_type"]
        tier_id = row["tier"]
        name = row["tier_name"]

        if group_id not in organisation_names:
            organisation_names[group_id] = {}

        organisation_names[group_id][tier_id] = name
        
    for unit in units:
        unit["unit_group"] = int(unit["unit_group"])

    return render_template(
    "production.html",
    current_page="production",
    units=units,
    organisation_names=organisation_names
)

# Construction Page
@app.route("/construction")
def construction():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM buildings
        ORDER BY money_cost ASC
    """)

    buildings = cursor.fetchall()

    #  # Organisation Levels
    # cursor.execute("""
    #     SELECT *
    #     FROM unit_organisation_tiers
    #     ORDER BY tier_type, tier
    # """)
    # organisation_rows = cursor.fetchall()

    cursor.close()
    conn.close()

    # for row in organisation_rows:

    #     group_id = row["tier_type"]
    #     tier = row["tier"]
    #     name = row["tier_name"]

    #     if group_id not in organisation_names:
    #         organisation_names[group_id] = {}

    #     organisation_names[group_id][tier] = name
        
    # for unit in units:
    #     unit["unit_group"] = int(unit["unit_group"])

    return render_template(
    "construction.html",
    buildings=buildings,
    current_page="construction"
)


@app.route("/api/production")
def get_production():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            pl.line_id,
            pl.line_name,
            pl.line_type,

            pq.queue_id,
            pq.position,
            pq.tier,
            pq.turns_remaining,
            pq.status,

            u.unit_name,
            u.build_time,
            t.tier_name

        FROM production_lines pl

        LEFT JOIN production_queue pq
            ON pl.line_id = pq.line_id

        LEFT JOIN units u
            ON pq.unit_id = u.unit_id
                   
        LEFT JOIN unit_organisation_tiers t
            ON pq.tier = t.tier
            AND u.unit_group = t.tier_type

        ORDER BY
            pl.line_id,
            pq.position
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(rows)

@app.route(
    "/api/cancel-queue/<int:queue_id>",
    methods=["DELETE"]
)
def cancel_queue(queue_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Find which production line this queue item belongs to
    cursor.execute("""
        SELECT
            pq.line_id,
            u.unit_name

        FROM production_queue pq

        JOIN units u
            ON pq.unit_id = u.unit_id

        WHERE pq.queue_id = %s
    """, (queue_id,))

    queue_item = cursor.fetchone()

    if not queue_item:

        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "error": "Queue item not found"
        }), 404

    line_id = queue_item["line_id"]
    unit_name = queue_item["unit_name"]

    # Delete the queue item
    cursor.execute("""
        DELETE
        FROM production_queue
        WHERE queue_id = %s
    """, (queue_id,))

    # Get remaining items in order
    cursor.execute("""
        SELECT queue_id
        FROM production_queue
        WHERE line_id = %s
        ORDER BY position
    """, (line_id,))

    remaining = cursor.fetchall()

    # Recalculate positions and statuses
    position = 1

    for item in remaining:

        status = (
            "building"
            if position == 1
            else "queued"
        )

        cursor.execute("""
            UPDATE production_queue
            SET
                position = %s,
                status = %s
            WHERE queue_id = %s
        """, (
            position,
            status,
            item["queue_id"]
        ))

        position += 1

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({

        "success": True,

        "title": "Production Cancelled",

        "message": f"{unit_name} removed from the production queue.",

        "type": "warning",

        "icon": "🚫"

    })

@app.route(
    "/api/cancel-construction/<int:queue_id>",
    methods=["DELETE"]
)
def cancel_construction(queue_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Find which building line this queue item belongs to
    cursor.execute("""
        SELECT
            bq.line_id,
            b.building_name

        FROM building_queue bq

        JOIN buildings b
            ON bq.building_id = b.building_id

        WHERE bq.queue_id = %s
    """, (queue_id,))

    queue_item = cursor.fetchone()

    if not queue_item:

        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "error": "Queue item not found"
        }), 404

    line_id = queue_item["line_id"]
    building_name = queue_item["building_name"]

    # Delete the queue item
    cursor.execute("""
        DELETE
        FROM building_queue
        WHERE queue_id = %s
    """, (queue_id,))

    # Get remaining items in order
    cursor.execute("""
        SELECT queue_id
        FROM building_queue
        WHERE line_id = %s
        ORDER BY position
    """, (line_id,))

    remaining = cursor.fetchall()

    # Recalculate positions and statuses
    position = 1

    for item in remaining:

        status = (
            "building"
            if position == 1
            else "queued"
        )

        cursor.execute("""
            UPDATE building_queue
            SET
                position = %s,
                status = %s
            WHERE queue_id = %s
        """, (
            position,
            status,
            item["queue_id"]
        ))

        position += 1

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({

    "success": True,

    "message":
        f"{building_name} removed from construction queue."

})

# SIGN UP
@app.route("/signup", methods=["POST"])
def signup():

    data = request.json

    username = data["username"]
    email = data["email"]
    password = data["password"]

    password_hash = generate_password_hash(password)

    db = get_db_connection()

    cursor = db.cursor()

    query = """
        INSERT INTO users (username, email, password_hash)
        VALUES (%s, %s, %s)
    """

    values = (username, email, password_hash)

    try:

        cursor.execute(query, values)

        db.commit()

        return jsonify({
            "message": "User created successfully"
        }), 201

    except mysql.connector.Error as err:

        return jsonify({
            "error": str(err)
        }), 400

    finally:

        cursor.close()
        db.close()


# LOGIN
@app.route("/login", methods=["POST"])
def login():

    data = request.json

    username = data["username"]
    password = data["password"]

    db = get_db_connection()

    cursor = db.cursor(dictionary=True)

    query = "SELECT * FROM users WHERE username = %s"

    cursor.execute(query, (username,))

    user = cursor.fetchone()

    # print("Entered password:", password)
    # print("Stored hash:", user["password_hash"])
    # print(check_password_hash(user["password_hash"], password))

    if user and check_password_hash(
        user["password_hash"],
        password
    ):
        
        # CREATE USER SESSION
        session["user_id"] = user["user_id"]
        session["nation_id"] = user["nation_id"]
        session["role"] = user["role"]
        session["username"] = user["username"]


        update_query = """
            UPDATE users
            SET last_login = %s
            WHERE user_id = %s
        """

        cursor.execute(
            update_query,
            (datetime.now(), user["user_id"])
        )

        db.commit()

        cursor.close()
        db.close()

        return jsonify({
            "redirect": url_for("dashboard")
        }), 200

    cursor.close()
    db.close()

    return jsonify({
        "error": "Invalid username or password"
    }), 401

# LOGOUT
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))

# ADMIN USER MANAGEMENT
@app.route("/admin")
def admin_dashboard():

    # CHECK LOGIN
    if "user_id" not in session:
        return redirect(url_for("access"))

    # CHECK ADMIN
    if session["role"] != "admin":
        return "Access Denied", 403

    db = get_db_connection()

    cursor = db.cursor(dictionary=True)

    # -------------------------
    # GET USERS
    # -------------------------
    cursor.execute("""
        SELECT *
        FROM frontlinesdb.users
    """)

    users = cursor.fetchall()

    # -------------------------
    # GET NATIONS
    # -------------------------
    cursor.execute("""
        SELECT *
        FROM frontlinesdb.nations
    """)

    nations = cursor.fetchall()

    # -------------------------
    # GET ALL UNITS
    # -------------------------
    cursor.execute("""
        SELECT *
        FROM frontlinesdb.units
    """)

    units = cursor.fetchall()

    # -------------------------
    # SELECTED UNIT
    # -------------------------
    selected_unit = None

    unit_id = request.args.get("unit_id")

    if unit_id:

        cursor.execute("""
            SELECT *
            FROM frontlinesdb.units
            WHERE unit_id = %s
        """, (unit_id,))

        selected_unit = cursor.fetchone()

    # -------------------------
    # SELECTED NATION
    # -------------------------
    selected_nation = None

    nation_resources = []

    nation_id = request.args.get("nation_id")

    if nation_id:

        # GET NATION
        cursor.execute("""
            SELECT *
            FROM frontlinesdb.nations
            WHERE nation_id = %s
        """, (nation_id,))

        selected_nation = cursor.fetchone()

        # GET NATION RESOURCES
        cursor.execute("""
            SELECT
                nation_resources.resource_id,
                nation_resources.amount,

                resources.resource_id,
                resources.name,
                resources.measurement_convention

            FROM frontlinesdb.nation_resources

            JOIN frontlinesdb.resources
                ON nation_resources.resource_id = resources.resource_id

            WHERE nation_resources.nation_id = %s
        """, (nation_id,))

        nation_resources = cursor.fetchall()

    # -------------------------
    # GET ALL RESOURCE TYPES
    # -------------------------
    cursor.execute("""
        SELECT *
        FROM frontlinesdb.resources
    """)

    resources = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "admin.html",
        users=users,
        nations=nations,
        units=units,
        selected_unit=selected_unit,

        selected_nation=selected_nation,
        nation_resources=nation_resources,
        resources=resources
    )

@app.route("/admin/process_turn", methods=["POST"])
def process_turn():

    # CHECK LOGIN
    if "user_id" not in session:
        return redirect(url_for("access"))

    # CHECK ADMIN
    if session["role"] != "admin":
        return "Forbidden", 403

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # -------------------------
    # GET CURRENT TURN
    # -------------------------
    cursor.execute("""
        SELECT current_turn
        FROM game_state
        WHERE id = 1
    """)

    game_state = cursor.fetchone()

    current_turn = game_state["current_turn"]
    next_turn = current_turn + 1

    # -------------------------
    # UPDATE GAME STATE
    # -------------------------
    cursor.execute("""
        UPDATE game_state
        SET current_turn = %s
        WHERE id = 1
    """, (next_turn,))

    # -------------------------
    # CREATE TURN RECORD
    # -------------------------
    cursor.execute("""
        INSERT INTO game_turns
        (
            turn_id,
            started_at,
            processed_at,
            status
        )
        VALUES
        (
            %s,
            NOW(),
            NOW(),
            'Complete'
        )
    """, (next_turn,))
    

    # ==========================================
    # ECONOMY
    # ==========================================

    # Get all active nations
    cursor.execute("""
        SELECT nation_id
        FROM nations
        WHERE is_active = 1
    """)

    nations = cursor.fetchall()

    for nation in nations:

        income = get_money_income(
            cursor,
            nation["nation_id"]
        )

        print(
            f"Nation {nation['nation_id']} "
            f"earned ${income:,}"
        )

        cursor.execute("""
            UPDATE nation_resources
            SET amount = amount + %s
            WHERE nation_id = %s
            AND resource_id = 1
        """,
        (
            income,
            nation["nation_id"]
        ))

    # ===========================
    # PROCESS BUILDING PRODUCTION
    # ===========================

    cursor.execute("""
        SELECT
            nb.nation_id,
            nb.building_id,
            nb.resource_id,
            nb.quantity,
            bro.per_turn_amount
        FROM nation_buildings nb
        JOIN building_resource_outputs bro
            ON nb.building_id = bro.building_id
        AND nb.resource_id = bro.resource_id
    """)

    building_production = cursor.fetchall()

    for building in building_production:

        amount = (
            building["quantity"] *
            building["per_turn_amount"]
        )

        cursor.execute("""
            UPDATE nation_resources
            SET amount = amount + %s
            WHERE nation_id = %s
            AND resource_id = %s
        """,
        (
            amount,
            building["nation_id"],
            building["resource_id"]
        ))

        print(
            f"Nation {building['nation_id']} | "
            f"Building {building['building_id']} | "
            f"Resource {building['resource_id']} | "
            f"+{amount:,}"
        )

    # ===========================
    # PROCESS BUILDING UPKEEP
    # ===========================

    cursor.execute("""
        SELECT
            nb.nation_id,
            nb.quantity,
            b.building_name,
            b.money_upkeep
        FROM nation_buildings nb
        JOIN buildings b
            ON nb.building_id = b.building_id
    """)

    building_upkeep = cursor.fetchall()

    for building in building_upkeep:

        upkeep = (
            building["quantity"] *
            building["money_upkeep"]
        )

        cursor.execute("""
            UPDATE nation_resources
            SET amount = amount - %s
            WHERE nation_id = %s
            AND resource_id = 1
        """,
        (
            upkeep,
            building["nation_id"]
        ))

        print(
            f"Nation {building['nation_id']} | "
            f"{building['building_name']} | "
            f"-${upkeep:,}"
        )

    # ===========================
    # PROCESS UNIT UPKEEP
    # ===========================

    cursor.execute("""
        SELECT
            nu.nation_id,
            nu.tier_level,
            u.unit_name,
            u.money_upkeep,
            u.oil_upkeep
        FROM nation_units nu
        JOIN units u
            ON nu.unit_id = u.unit_id
        WHERE nu.status = 'active'
    """)

    unit_upkeep = cursor.fetchall()

    for unit in unit_upkeep:

        money_upkeep = (
            unit["money_upkeep"] *
            unit["tier_level"]
        )

        oil_upkeep = (
            unit["oil_upkeep"] *
            unit["tier_level"]
        )

        # -------------------------
        # MONEY UPKEEP
        # -------------------------
        cursor.execute("""
            UPDATE nation_resources
            SET amount = amount - %s
            WHERE nation_id = %s
            AND resource_id = 1
        """,
        (
            money_upkeep,
            unit["nation_id"]
        ))

        # -------------------------
        # OIL UPKEEP
        # -------------------------
        cursor.execute("""
            UPDATE nation_resources
            SET amount = amount - %s
            WHERE nation_id = %s
            AND resource_id = 4
        """,
        (
            oil_upkeep,
            unit["nation_id"]
        ))

        print(
            f"Nation {unit['nation_id']} | "
            f"{unit['unit_name']} | "
            f"Tier {unit['tier_level']} | "
            f"-${money_upkeep:,} | "
            f"-{oil_upkeep:,} bbl"
        )

    # ===========================
    # START BUILDING CONSTRUCTION
    # ===========================

    cursor.execute("""
        SELECT line_id
        FROM building_lines
    """)

    building_lines = cursor.fetchall()

    for line in building_lines:

        cursor.execute("""
            SELECT queue_id
            FROM building_queue
            WHERE line_id = %s
            AND status = 'building'
        """,
        (
            line["line_id"],
        ))

        active_build = cursor.fetchone()

        if active_build is None:

            cursor.execute("""
                SELECT queue_id
                FROM building_queue
                WHERE line_id = %s
                AND status = 'queued'
                ORDER BY position
                LIMIT 1
            """,
            (
                line["line_id"],
            ))

            next_building = cursor.fetchone()

            if next_building:

                cursor.execute("""
                    UPDATE building_queue
                    SET status = 'building'
                    WHERE queue_id = %s
                """,
                (
                    next_building["queue_id"],
                ))

                print(
                    f"Started building queue item "
                    f"{next_building['queue_id']}"
                )

    # ===========================
    # PROCESS BUILDING QUEUES
    # ===========================

    cursor.execute("""
        SELECT
            bq.queue_id,
            bq.building_id,
            bq.resource_id,
            bq.turns_remaining,
            bl.nation_id
        FROM building_queue bq
        JOIN building_lines bl
            ON bq.line_id = bl.line_id
        WHERE bq.status = 'building'
    """)

    building_queue = cursor.fetchall()

    for building in building_queue:

        turns_remaining = building["turns_remaining"] - 1

        cursor.execute("""
            UPDATE building_queue
            SET turns_remaining = %s
            WHERE queue_id = %s
        """,
        (
            turns_remaining,
            building["queue_id"]
        ))

        print(
            f"Queue {building['queue_id']} "
            f"now has {turns_remaining} turns remaining."
        )

        print(building)

        if turns_remaining <= 0:

            cursor.execute("""
                SELECT nation_building_id
                FROM nation_buildings
                WHERE nation_id = %s
                AND building_id = %s
                AND (
                    resource_id = %s
                    OR (resource_id IS NULL AND %s IS NULL)
                )
            """,
            (
                building["nation_id"],
                building["building_id"],
                building["resource_id"],
                building["resource_id"]
            ))

            existing = cursor.fetchone()

            if existing:

                cursor.execute("""
                    UPDATE nation_buildings
                    SET quantity = quantity + 1
                    WHERE nation_building_id = %s
                """,
                (
                    existing["nation_building_id"],
                ))

            else:

                cursor.execute("""
                    INSERT INTO nation_buildings
                    (
                        nation_id,
                        building_id,
                        resource_id,
                        quantity
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        1
                    )
                """,
                (
                    building["nation_id"],
                    building["building_id"],
                    building["resource_id"]
                ))

            cursor.execute("""
                DELETE FROM building_queue
                WHERE queue_id = %s
            """,
            (
                building["queue_id"],
            ))

            print(
                f"Building completed! "
                f"Nation {building['nation_id']} "
                f"Building {building['building_id']}"
            )


    # ===========================
    # START UNIT PRODUCTION
    # ===========================

    cursor.execute("""
        SELECT line_id
        FROM production_lines
    """)

    production_lines = cursor.fetchall()

    for line in production_lines:

        cursor.execute("""
            SELECT queue_id
            FROM production_queue
            WHERE line_id = %s
            AND status = 'building'
        """,
        (
            line["line_id"],
        ))

        active_build = cursor.fetchone()

        if active_build is None:

            cursor.execute("""
                SELECT queue_id
                FROM production_queue
                WHERE line_id = %s
                AND status = 'queued'
                ORDER BY position
                LIMIT 1
            """,
            (
                line["line_id"],
            ))

            next_unit = cursor.fetchone()

            if next_unit:

                cursor.execute("""
                    UPDATE production_queue
                    SET status = 'building'
                    WHERE queue_id = %s
                """,
                (
                    next_unit["queue_id"],
                ))

                print(
                    f"Started production queue item "
                    f"{next_unit['queue_id']}"
                )

    # ===========================
    # PROCESS UNIT QUEUES
    # ===========================

    cursor.execute("""
        SELECT
            pq.queue_id,
            pq.unit_id,
            pq.tier,
            pq.turns_remaining,
            pl.nation_id

        FROM production_queue pq

        JOIN production_lines pl
            ON pq.line_id = pl.line_id

        WHERE pq.status = 'building'
    """)

    unit_queue = cursor.fetchall()

    for unit in unit_queue:

        turns_remaining = unit["turns_remaining"] - 1

        cursor.execute("""
            UPDATE production_queue
            SET turns_remaining = %s
            WHERE queue_id = %s
        """,
        (
            turns_remaining,
            unit["queue_id"]
        ))

        print(
            f"Queue {unit['queue_id']} "
            f"now has {turns_remaining} turns remaining."
        )

        print(
            f"Queue {unit['queue_id']} "
            f"now has {turns_remaining} turns remaining."
        )

        if turns_remaining <= 0:

            cursor.execute("""
                INSERT INTO nation_units
                (
                    nation_id,
                    unit_id,
                    game_turn,
                    tier_level,
                    status,
                    created_at,
                    updated_at
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    'active',
                    NOW(),
                    NOW()
                )
            """,
            (
                unit["nation_id"],
                unit["unit_id"],
                next_turn,
                unit["tier"]
            ))

            cursor.execute("""
                DELETE
                FROM production_queue
                WHERE queue_id = %s
            """,
            (
                unit["queue_id"],
            ))

            print(
                f"Unit completed! "
                f"Nation {unit['nation_id']} | "
                f"Unit {unit['unit_id']} | "
                f"Tier {unit['tier']}"
            )

    # ==========================================
    # RESEARCH
    # ==========================================

    # Coming Soon



    
    # -------------------------
    # CREATE TURN LOG
    # -------------------------
    cursor.execute("""
        INSERT INTO turn_logs
        (
            turn_id,
            nation_id,
            event_type,
            details
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s
        )
    """, (
        next_turn,
        1,
        "System",
        f"Turn {next_turn} processed successfully."
    ))

    db.commit()

    cursor.close()
    db.close()

    return redirect(url_for("admin_dashboard"))

# ASSIGN NATION TO PLAYER
@app.route("/admin/assign_nation", methods=["POST"])
def assign_nation():

    # CHECK LOGIN
    if "user_id" not in session:
        return redirect(url_for("access"))

    # CHECK ADMIN
    if session["role"] != "admin":
        return "Access Denied", 403

    user_id = request.form["user_id"]
    nation_id = request.form["nation_id"]

    db = get_db_connection()

    cursor = db.cursor()

    query = """
        UPDATE frontlinesdb.users
        SET nation_id = %s
        WHERE user_id = %s
    """

    cursor.execute(
        query,
        (nation_id, user_id)
    )  

    db.commit()

    cursor.close()
    db.close()

    return redirect(url_for("admin_dashboard"))

@app.route("/admin/add_new_units", methods=["POST"])
def add_new_units():

    if session["role"] != "admin":
        return "Forbidden", 403

    unit_name = request.form["unit_name"]
    unit_class = request.form["unit_class"]
    unit_group = request.form["unit_group"]
    strength = request.form["strength"]
    defence = request.form["defence"]
    movement = request.form["movement"]
    unit_size = request.form["unit_size"]
    money_cost = request.form["money_cost"]
    cm_cost = request.form["cm_cost"]
    rm_cost = request.form["rm_cost"]
    money_upkeep = request.form["money_upkeep"]
    description = request.form["description"]

    db = get_db_connection()

    cursor = db.cursor()

    query = """
        INSERT INTO units
        (
            unit_name,
            unit_class,
            unit_group,
            strength,
            defence,
            movement,
            unit_size,
            money_cost,
            cm_cost,
            rm_cost,
            money_upkeep,
            description
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    cursor.execute(
        query,
        (
            unit_name,
            unit_class,
            unit_group,
            strength,
            defence,
            movement,
            unit_size,
            money_cost,
            cm_cost,
            rm_cost,
            money_upkeep,
            description,
        )
    )

    db.commit()

    cursor.close()
    db.close()

    return redirect(url_for("admin_dashboard"))

# UPDATE UNIT
@app.route("/admin/update_unit", methods=["POST"])
def update_unit():

    # CHECK ADMIN
    if session["role"] != "admin":
        return "Forbidden", 403

    unit_id = request.form["unit_id"]

    unit_name = request.form["unit_name"]
    unit_class = request.form["unit_class"]
    unit_group = request.form["unit_group"]

    strength = request.form["strength"]
    defence = request.form["defence"]
    movement = request.form["movement"]

    unit_size = request.form["unit_size"]

    money_cost = request.form["money_cost"]
    cm_cost = request.form["cm_cost"]
    rm_cost = request.form["rm_cost"]

    money_upkeep = request.form["money_upkeep"]

    description = request.form["description"]

    db = get_db_connection()

    cursor = db.cursor()

    query = """
        UPDATE units
        SET
            unit_name = %s,
            unit_class = %s,
            unit_group = %s,
            strength = %s,
            defence = %s,
            movement = %s,
            unit_size = %s,
            money_cost = %s,
            cm_cost = %s,
            rm_cost = %s,
            money_upkeep = %s,
            description = %s
        WHERE unit_id = %s
    """

    cursor.execute(
        query,
        (
            unit_name,
            unit_class,
            unit_group,
            strength,
            defence,
            movement,
            unit_size,
            money_cost,
            cm_cost,
            rm_cost,
            money_upkeep,
            description,
            unit_id
        )
    )

    db.commit()

    cursor.close()
    db.close()

    return redirect(
        url_for(
            "admin_dashboard",
        )
    )

# UPDATE RESOURCE
@app.route("/admin/update_resource", methods=["POST"])
def update_resource():

    if session["role"] != "admin":
        return "Forbidden", 403

    resource_id = request.form["resource_id"]
    nation_id = request.form["nation_id"]
    amount = request.form["amount"]

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # GET CURRENT GAME TURN
    cursor.execute("""
        SELECT turn_id
        FROM game_turns
        ORDER BY turn_id DESC
        LIMIT 1
    """)

    current_turn = cursor.fetchone()

    turn_id = current_turn["turn_id"]

    # UPDATE CURRENT RESOURCE
    cursor.execute("""
        UPDATE nation_resources
        SET amount = %s
        WHERE resource_id = %s
        AND nation_id = %s
    """, (amount, resource_id, nation_id))

    # INSERT RESOURCE HISTORY
    cursor.execute("""
        INSERT INTO resource_history ( 
            nation_id,
            resource_id,
            turn_id,
            amount
        )
        VALUES (%s, %s, %s, %s)
    """, (
        nation_id,
        resource_id,
        turn_id,
        amount
    ))

    db.commit()

    cursor.close()
    db.close()

    return redirect(
        url_for(
            "admin_dashboard",
            nation_id=nation_id
        )
    )


@app.route("/api/unit/<int:unit_id>")
def get_unit(unit_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM units
        JOIN unit_wiki
            ON units.unit_id = unit_wiki.unit_id
        WHERE units.unit_id = %s
    """, (unit_id,))

    unit = cursor.fetchone()

    cursor.execute("""
        SELECT tier_name
        FROM unit_organisation_tiers
        WHERE tier_type = %s
        AND tier = 1
    """, (unit["unit_group"],))

    organisation = cursor.fetchone()

    unit["organisation_name"] = organisation["tier_name"]

    cursor.execute("""
        SELECT *
        FROM resources
        WHERE is_active = 1
    """)

    resources = cursor.fetchall()

    resource_units = {}

    for resource in resources:
        resource_units[
            resource["name"]
        ] = resource["measurement_convention"]

    cursor.close()
    conn.close()

    return jsonify({
        "unit": unit,
        "resource_units": resource_units
    })


@app.route("/api/build-unit", methods=["POST"])
def build_unit():

    data = request.get_json()

    unit_id = data["unit_id"]
    tier_id = data["tier_id"]


    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM units
        WHERE unit_id = %s
    """, (unit_id,))

    unit = cursor.fetchone()

    cursor.execute("""
        SELECT
            resource_id,
            amount
        FROM nation_resources
        WHERE nation_id = %s
    """,
    (
        session["nation_id"],
    ))

    resources = {
        row["resource_id"]: row["amount"]
        for row in cursor.fetchall()
    }

    required = [
    (1, "Money", "💰", unit["money_cost"]),
    (2, "Common Metal", "⛏️", unit["cm_cost"]),
    (3, "Rare Metal", "💎", unit["rm_cost"]),
]

    for resource_id, name, icon, cost in required:

        if resources[resource_id] < cost:

            cursor.close()
            conn.close()

            return jsonify({

                "success": False,

                "title": "Production Failed",

                "message": f"Not enough {name}.",

                "icon": icon,

                "type": "error"

            })

    for resource_id, _, _, cost in required:

        cursor.execute("""
            UPDATE nation_resources
            SET amount = amount - %s
            WHERE nation_id = %s
            AND resource_id = %s
        """,
        (
            cost,
            session["nation_id"],
            resource_id
        ))


    # -------------------------------------------------
    # TEMPORARY:
    # Special units still need a production line.
    # Route them based on organisation group until
    # production_type is added to the database.
    # -------------------------------------------------

    line_type = unit["unit_class"]

    if line_type == "special":

        if unit["unit_group"] == "4":
            # Helicopter
            line_type = "air"

        elif unit["unit_group"] == "6":
            # Submarine
            line_type = "sea"

        else:
            # Engineers, Logistics, HQ, Artillery, etc.
            line_type = "land"

    cursor.execute("""
        SELECT
            pl.line_id,
            pl.line_name,
            COUNT(pq.queue_id) AS queue_size

        FROM production_lines pl

        LEFT JOIN production_queue pq
            ON pl.line_id = pq.line_id

        WHERE
            pl.nation_id = %s
        AND
            pl.line_type = %s

        GROUP BY
            pl.line_id,
            pl.line_name

        ORDER BY
            queue_size ASC,
            pl.line_id ASC

        LIMIT 1
    """,
    (
        session["nation_id"],
        line_type
    ))

    line = cursor.fetchone()

    if not line:
        cursor.close()
        conn.close()

        return jsonify({

            "success": False,

            "title": "Production Failed",

            "message": "No production line found.",

            "icon": "❌",

            "type": "error"

        }), 400

    cursor.execute("""
        SELECT COUNT(*) AS queue_size
        FROM production_queue
        WHERE line_id = %s
    """, (line["line_id"],))

    queue_size = cursor.fetchone()["queue_size"]

    position = queue_size + 1

    turns_remaining = (
        unit["build_time"] +
        (tier_id - 1)
    )

    status = "building" if position == 1 else "queued"

    cursor.execute("""
        INSERT INTO production_queue
        (
            line_id,
            unit_id,
            tier,
            position,
            turns_remaining,
            status
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
    """, (
        line["line_id"],
        unit_id,
        tier_id,
        position,
        turns_remaining,
        status
    ))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({

        "success": True,

        "title": "Production Started",

        "message":
            f"{unit['unit_name']} assigned to {line['line_name']}.",

        "type": "success",

        "icon": "🛡️",

        "line": line["line_name"],

        "unit_name": unit["unit_name"],

        "position": position

    })


@app.route("/api/building/<int:building_id>")
def get_building(building_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM buildings

        JOIN building_wiki
            ON buildings.building_id = building_wiki.building_id

        WHERE buildings.building_id = %s
    """, (building_id,))

    building = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify({
        "building": building
    })

@app.route("/api/build-building", methods=["POST"])
def build_building():

    data = request.get_json()

    building_id = data["building_id"]
    resource_id = data.get("resource_id")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get the building
    cursor.execute("""
        SELECT *
        FROM buildings
        WHERE building_id = %s
    """, (building_id,))

    building = cursor.fetchone()

    cursor.execute("""
        SELECT
            resource_id,
            amount
        FROM nation_resources
        WHERE nation_id = %s
    """,
    (
        session["nation_id"],
    ))

    resources = {
            row["resource_id"]: row["amount"]
            for row in cursor.fetchall()
        }

    if resources[1] < building["money_cost"]:

        cursor.close()
        conn.close()

        return jsonify({

            "success": False,

            "title": "Construction Failed",

            "message": "You do not have enough Money.",

            "icon": "💰",

            "type": "error"

        })
    
    if resources[2] < building["cm_cost"]:

        cursor.close()
        conn.close()

        return jsonify({

            "success": False,

            "title": "Construction Failed",

            "message": "You do not have enough Common Metal.",

            "icon": "⛏️",

            "type": "error"

        })

    if resources[3] < building["rm_cost"]:

        cursor.close()
        conn.close()

        return jsonify({

            "success": False,

            "title": "Construction Failed",

            "message": "You do not have enough Rare Metal.",

            "icon": "💎",

            "type": "error"

        })

    cursor.execute("""
        UPDATE nation_resources
        SET amount = amount - %s
        WHERE nation_id = %s
        AND resource_id = 1
    """,
    (
        building["money_cost"],
        session["nation_id"]
    ))

    cursor.execute("""
        UPDATE nation_resources
        SET amount = amount - %s
        WHERE nation_id = %s
        AND resource_id = 2
    """,
    (
        building["cm_cost"],
        session["nation_id"]
    ))

    cursor.execute("""
        UPDATE nation_resources
        SET amount = amount - %s
        WHERE nation_id = %s
        AND resource_id = 3
    """,
    (
        building["rm_cost"],
        session["nation_id"]
    ))

    # Find the shortest construction line for this nation
    cursor.execute("""
        SELECT
            bl.line_id,
            bl.line_name,
            COUNT(bq.queue_id) AS queue_size

        FROM building_lines bl

        LEFT JOIN building_queue bq
            ON bl.line_id = bq.line_id

        WHERE bl.nation_id = %s

        GROUP BY
            bl.line_id,
            bl.line_name

        ORDER BY
            queue_size ASC,
            bl.line_id ASC

        LIMIT 1
    """, (session["nation_id"],))

    line = cursor.fetchone()

    if not line:

        cursor.close()
        conn.close()

        return jsonify({


            "success": False,

            "title": "Construction Failed",

            "message": "No construction line found.",

            "icon": "❌",

            "type": "error"

        }), 400

    # Current queue size
    cursor.execute("""
        SELECT COUNT(*) AS queue_size
        FROM building_queue
        WHERE line_id = %s
    """, (line["line_id"],))

    queue_size = cursor.fetchone()["queue_size"]

    position = queue_size + 1

    status = "building" if position == 1 else "queued"

    cursor.execute("""
        INSERT INTO building_queue
        (
            line_id,
            building_id,
            resource_id,
            position,
            turns_remaining,
            status
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
    """, (
        line["line_id"],
        building_id,
        resource_id,
        position,
        building["build_time"],
        status
    ))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({

        "success": True,

        "building_name": building["building_name"],

        "resource_id": resource_id,
        "line": line["line_name"]

    })

@app.route("/api/construction")
def get_construction():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT

            bl.line_id,
            bl.line_name,

            bq.queue_id,
            bq.position,
            bq.turns_remaining,
            bq.status,

            b.building_name,
            b.build_time

        FROM building_lines bl

        LEFT JOIN building_queue bq
            ON bl.line_id = bq.line_id

        LEFT JOIN buildings b
            ON bq.building_id = b.building_id

        WHERE bl.nation_id = %s

        ORDER BY
            bl.line_id,
            bq.position

    """, (session["nation_id"],))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(rows)


@app.context_processor
def inject_nation():

    if "nation_id" not in session:

        return {}

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM nations
        WHERE nation_id = %s
    """, (session["nation_id"],))

    nation = cursor.fetchone()

     # Current Turn
    cursor.execute("""
        SELECT current_turn
        FROM game_state
    """)

    turn = cursor.fetchone()

    cursor.close()
    conn.close()

    return {
        "nation": nation,
        "current_turn": turn["current_turn"]
    }

@app.route("/api/notifications")
def get_notifications():

    if "nation_id" not in session:

        return jsonify([])

    nation_id = session["nation_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT

            notification_id,
            type,
            title,
            message,
            icon,
            created_turn,
            is_read,
            reference_id,
            persistent

        FROM notifications

        WHERE nation_id = %s
        AND is_read = FALSE

        ORDER BY notification_id DESC

    """, (nation_id,))

    notifications = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(notifications)


@app.route(
    "/api/alliance-invitation/<int:invitation_id>/accept",
    methods=["POST"]
)
def accept_alliance_invitation(invitation_id):

    if "nation_id" not in session:

        return jsonify([])

    nation_id = session["nation_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Find pending invitation
    cursor.execute("""
        SELECT
            ai.invitation_id,
            ai.alliance_id,
            a.alliance_name,
            a.alliance_code

        FROM alliance_invitations ai

        JOIN alliances a
            ON ai.alliance_id = a.alliance_id

        WHERE ai.invitation_id = %s
        AND ai.nation_id = %s
        AND ai.status = 'Pending'
    """, (
        invitation_id,
        nation_id
    ))

    invitation = cursor.fetchone()

    if not invitation:

        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "error": "This invitation is no longer valid.",
            "type": "error",
            "title": "Alliance Invitation",
            "message": "This invitation is no longer valid.",
            "icon": "❌"
        }), 400

    # Make sure nation isn't already in an alliance
    cursor.execute("""
        SELECT alliance_member_id
        FROM alliance_members
        WHERE nation_id = %s
    """, (nation_id,))

    existing_membership = cursor.fetchone()

    if existing_membership:

        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "error": "You are already a member of an alliance.",
            "type": "error",
            "title": "Alliance Invitation",
            "message": "You are already a member of an alliance.",
            "icon": "❌"
        }), 400

    # Get current turn
    cursor.execute("""
        SELECT current_turn
        FROM game_state
        LIMIT 1
    """)

    game_state = cursor.fetchone()

    current_turn = game_state["current_turn"]

    # Add nation to alliance
    cursor.execute("""
        INSERT INTO alliance_members (
            alliance_id,
            nation_id,
            joined_turn
        )
        VALUES (%s, %s, %s)
    """, (
        invitation["alliance_id"],
        nation_id,
        current_turn
    ))

    # Mark invitation accepted
    cursor.execute("""
        UPDATE alliance_invitations

        SET status = 'Accepted'

        WHERE invitation_id = %s
    """, (invitation_id,))

    # Add Recent Event
    cursor.execute("""
        INSERT INTO nation_events (
            nation_id,
            event_type,
            title,
            message,
            created_turn
        )
        VALUES (%s, %s, %s, %s, %s)
    """, (
        nation_id,
        "diplomacy",
        "Alliance Joined",
        f"You joined {invitation['alliance_name']} [{invitation['alliance_code']}].",
        current_turn
    ))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "type": "success",
        "title": "Alliance Joined",
        "message": f"You joined {invitation['alliance_name']} [{invitation['alliance_code']}].",
        "icon": "🤝"
    })


@app.route(
    "/api/alliance-invitation/<int:invitation_id>/decline",
    methods=["POST"]
)
def decline_alliance_invitation(invitation_id):

    nation_id = session["nation_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Find pending invitation
    cursor.execute("""
        SELECT
            ai.invitation_id,
            ai.alliance_id,
            a.alliance_name,
            a.alliance_code

        FROM alliance_invitations ai

        JOIN alliances a
            ON ai.alliance_id = a.alliance_id

        WHERE ai.invitation_id = %s
        AND ai.nation_id = %s
        AND ai.status = 'Pending'
    """, (
        invitation_id,
        nation_id
    ))

    invitation = cursor.fetchone()

    if not invitation:

        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "error": "This invitation is no longer valid.",
            "type": "error",
            "title": "Alliance Invitation",
            "message": "This invitation is no longer valid.",
            "icon": "❌"
        }), 400

    # Get current turn
    cursor.execute("""
        SELECT current_turn
        FROM game_state
        LIMIT 1
    """)

    game_state = cursor.fetchone()

    current_turn = game_state["current_turn"]

    # Mark invitation declined
    cursor.execute("""
        UPDATE alliance_invitations

        SET status = 'Declined'

        WHERE invitation_id = %s
    """, (invitation_id,))

    # Add Recent Event
    cursor.execute("""
        INSERT INTO nation_events (
            nation_id,
            event_type,
            title,
            message,
            created_turn
        )
        VALUES (%s, %s, %s, %s, %s)
    """, (
        nation_id,
        "diplomacy",
        "Alliance Invitation Declined",
        f"You declined the invitation to join {invitation['alliance_name']} [{invitation['alliance_code']}].",
        current_turn
    ))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "type": "info",
        "title": "Invitation Declined",
        "message": f"You declined the invitation to join {invitation['alliance_name']} [{invitation['alliance_code']}].",
        "icon": "ℹ️"
    })


@app.route("/api/notifications/<int:notification_id>/read", methods=["POST"])
def mark_notification_read(notification_id):

    nation_id = session["nation_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE notifications

        SET is_read = TRUE

        WHERE notification_id = %s
        AND nation_id = %s

    """, (
        notification_id,
        nation_id
    ))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "success": True
    })

@app.route("/api/events")
def get_events():

    if "nation_id" not in session:

        return jsonify([])

    nation_id = session["nation_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT

            event_id,
            event_type,
            title,
            message,
            created_turn,
            created_at

        FROM nation_events

        WHERE nation_id = %s

        ORDER BY event_id DESC

        LIMIT 10

    """, (nation_id,))

    events = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(events)

@app.route("/trade")
def trade():

    nation_id = session["nation_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get all other active nations
    cursor.execute("""
        SELECT
            nation_id,
            name,
            flag
        FROM nations
        WHERE is_active = 1
        AND nation_id != %s
        ORDER BY name
    """, (nation_id,))

    nations = cursor.fetchall()

    # Get resources available to the current nation
    cursor.execute("""
        SELECT
            r.resource_id,
            r.name,
            nr.amount

        FROM resources r

        JOIN nation_resources nr
            ON r.resource_id = nr.resource_id

        WHERE nr.nation_id = %s

        ORDER BY r.resource_id
    """, (nation_id,))

    resources = cursor.fetchall()

    # Get units available to the current nation
    cursor.execute("""
        SELECT
            u.unit_id,
            u.unit_name,
            u.unit_group,
            nu.tier_level,
            uot.tier_name,
            COUNT(nu.nation_unit_id) AS quantity

        FROM units u

        JOIN nation_units nu
            ON u.unit_id = nu.unit_id

        LEFT JOIN unit_organisation_tiers uot
            ON uot.tier_type = u.unit_group
            AND uot.tier = nu.tier_level

        WHERE nu.nation_id = %s

        AND nu.status = 'active'

        GROUP BY
            u.unit_id,
            u.unit_name,
            u.unit_group,
            nu.tier_level,
            uot.tier_name

        ORDER BY
            u.unit_name,
            nu.tier_level
    """, (nation_id,))

    units = cursor.fetchall()

    # ------------------------------------------
    # Incoming Trade Offers
    # ------------------------------------------

    cursor.execute("""
        SELECT
            t.trade_offer_id,
            t.sender_nation_id,
            t.receiver_nation_id,
            t.status,
            t.created_turn,
            n.name AS sender_name,
            n.flag AS sender_flag

        FROM trade_offers t

        JOIN nations n
            ON t.sender_nation_id = n.nation_id

        WHERE t.receiver_nation_id = %s

        ORDER BY t.trade_offer_id DESC
    """, (nation_id,))

    incoming_offers = cursor.fetchall()


    # ------------------------------------------
    # Outgoing Trade Offers
    # ------------------------------------------

    cursor.execute("""
        SELECT
            t.trade_offer_id,
            t.sender_nation_id,
            t.receiver_nation_id,
            t.status,
            t.created_turn,
            n.name AS receiver_name,
            n.flag AS receiver_flag

        FROM trade_offers t

        JOIN nations n
            ON t.receiver_nation_id = n.nation_id

        WHERE t.sender_nation_id = %s

        ORDER BY t.trade_offer_id DESC
    """, (nation_id,))


    outgoing_offers = cursor.fetchall()

    # ------------------------------------------
    # Incoming Offer Items
    # ------------------------------------------

    cursor.execute("""
        SELECT
            toi.trade_offer_id,
            toi.side,
            toi.resource_id,
            toi.unit_id,
            toi.tier_level,
            toi.quantity,

            r.name AS resource_name,

            u.unit_name,
            u.unit_group,
            uot.tier_name

        FROM trade_offer_items toi

        LEFT JOIN resources r
            ON toi.resource_id = r.resource_id

        LEFT JOIN units u
            ON toi.unit_id = u.unit_id

        LEFT JOIN unit_organisation_tiers uot
            ON uot.tier_type = u.unit_group
            AND uot.tier = toi.tier_level

        JOIN trade_offers t
            ON toi.trade_offer_id = t.trade_offer_id

        WHERE t.receiver_nation_id = %s

        ORDER BY toi.trade_offer_id DESC
    """, (nation_id,))

    incoming_offer_items = cursor.fetchall()

    # ------------------------------------------
    # Outgoing Offer Items
    # ------------------------------------------

    cursor.execute("""
        SELECT
            toi.trade_offer_id,
            toi.side,
            toi.resource_id,
            toi.unit_id,
            toi.tier_level,
            toi.quantity,

            r.name AS resource_name,

            u.unit_name,
            u.unit_group,
            uot.tier_name

        FROM trade_offer_items toi

        LEFT JOIN resources r
            ON toi.resource_id = r.resource_id

        LEFT JOIN units u
            ON toi.unit_id = u.unit_id

        LEFT JOIN unit_organisation_tiers uot
            ON uot.tier_type = u.unit_group
            AND uot.tier = toi.tier_level

        JOIN trade_offers t
            ON toi.trade_offer_id = t.trade_offer_id

        WHERE t.sender_nation_id = %s

        ORDER BY toi.trade_offer_id DESC
    """, (nation_id,))

    outgoing_offer_items = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "trade.html",
        current_page="trade",
        nations=nations,
        resources=resources,
        units=units,
        incoming_offers=incoming_offers,
        outgoing_offers=outgoing_offers,
        incoming_offer_items=incoming_offer_items,
        outgoing_offer_items=outgoing_offer_items
    )

@app.route("/trade/create", methods=["POST"])
def create_trade():

    sender_nation_id = session["nation_id"]

    receiver_nation_id = request.form.get(
        "receiver_nation_id"
    )

    sender_resource_id = request.form.get(
        "sender_resource_id"
    )

    sender_resource_quantity = request.form.get(
        "sender_resource_quantity"
    )

    sender_unit = request.form.get(
        "sender_unit_id"
    )

    sender_unit_quantity = request.form.get(
        "sender_unit_quantity"
    )

    receiver_resource_id = request.form.get(
        "receiver_resource_id"
    )

    receiver_resource_quantity = request.form.get(
        "receiver_resource_quantity"
    )

    receiver_unit = request.form.get(
        "receiver_unit_id"
    )

    receiver_unit_quantity = request.form.get(
        "receiver_unit_quantity"
    )


    # ------------------------------------------
    # BASIC VALIDATION
    # ------------------------------------------

    if not receiver_nation_id:

        return "You must select a nation.", 400


    try:

        receiver_nation_id = int(
            receiver_nation_id
        )

    except ValueError:

        return "Invalid nation.", 400


    if receiver_nation_id == sender_nation_id:

        return "You cannot trade with yourself.", 400


    if not (
        sender_resource_id
        or sender_unit
    ):

        return "You must offer something.", 400


    if not (
        receiver_resource_id
        or receiver_unit
    ):

        return "You must request something.", 400


    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)


    try:

        # --------------------------------------
        # VERIFY RECEIVER
        # --------------------------------------

        cursor.execute("""
            SELECT nation_id
            FROM nations
            WHERE nation_id = %s
            AND is_active = 1
        """, (
            receiver_nation_id,
        ))

        receiver = cursor.fetchone()


        if not receiver:

            raise ValueError(
                "Nation not found."
            )


        # --------------------------------------
        # GET CURRENT TURN
        # --------------------------------------

        cursor.execute("""
            SELECT current_turn
            FROM game_state
            LIMIT 1
        """)

        game_state = cursor.fetchone()


        if not game_state:

            raise ValueError(
                "Game state could not be found."
            )


        current_turn = game_state[
            "current_turn"
        ]


        # --------------------------------------
        # SENDER RESOURCE
        # --------------------------------------

        if sender_resource_id:

            try:

                sender_resource_id = int(
                    sender_resource_id
                )

                quantity = int(
                    sender_resource_quantity
                )

            except (ValueError, TypeError):

                raise ValueError(
                    "Invalid resource information."
                )


            if quantity <= 0:

                raise ValueError(
                    "Invalid resource quantity."
                )


            cursor.execute("""
                SELECT amount
                FROM nation_resources
                WHERE nation_id = %s
                AND resource_id = %s
            """, (
                sender_nation_id,
                sender_resource_id
            ))

            resource = cursor.fetchone()


            if not resource:

                raise ValueError(
                    "You do not own this resource."
                )


            if resource["amount"] < quantity:

                raise ValueError(
                    "You do not have enough of this resource."
                )


        # --------------------------------------
        # SENDER UNIT
        # --------------------------------------

        sender_unit_id = None
        sender_unit_tier = None


        if sender_unit:

            try:

                parts = sender_unit.split(":")


                if len(parts) != 2:

                    raise ValueError


                sender_unit_id = int(
                    parts[0]
                )

                sender_unit_tier = int(
                    parts[1]
                )

                quantity = int(
                    sender_unit_quantity
                )

            except (ValueError, TypeError):

                raise ValueError(
                    "Invalid unit information."
                )


            if quantity <= 0:

                raise ValueError(
                    "Invalid unit quantity."
                )


            # Make sure this formation actually exists
            # in the sender's army.

            cursor.execute("""
                SELECT
                    COUNT(*) AS quantity
                FROM nation_units
                WHERE nation_id = %s
                AND unit_id = %s
                AND tier_level = %s
                AND status = 'active'
            """, (
                sender_nation_id,
                sender_unit_id,
                sender_unit_tier
            ))

            available = cursor.fetchone()


            if available["quantity"] < quantity:

                raise ValueError(
                    "You do not have enough of this unit formation."
                )


        # --------------------------------------
        # RECEIVER RESOURCE
        # --------------------------------------

        if receiver_resource_id:

            try:

                receiver_resource_id = int(
                    receiver_resource_id
                )

                quantity = int(
                    receiver_resource_quantity
                )

            except (ValueError, TypeError):

                raise ValueError(
                    "Invalid requested resource information."
                )


            if quantity <= 0:

                raise ValueError(
                    "Invalid requested resource quantity."
                )


            # We only verify that the resource exists.
            #
            # We DO NOT check the receiver's
            # stockpile because that information
            # is private.

            cursor.execute("""
                SELECT resource_id
                FROM resources
                WHERE resource_id = %s
            """, (
                receiver_resource_id,
            ))

            resource = cursor.fetchone()


            if not resource:

                raise ValueError(
                    "Requested resource does not exist."
                )


        # --------------------------------------
        # RECEIVER UNIT
        # --------------------------------------

        receiver_unit_id = None
        receiver_unit_tier = None


        if receiver_unit:

            try:

                parts = receiver_unit.split(":")


                if len(parts) != 2:

                    raise ValueError


                receiver_unit_id = int(
                    parts[0]
                )

                receiver_unit_tier = int(
                    parts[1]
                )

                quantity = int(
                    receiver_unit_quantity
                )

            except (ValueError, TypeError):

                raise ValueError(
                    "Invalid requested unit."
                )


            if quantity <= 0:

                raise ValueError(
                    "Invalid requested unit quantity."
                )


            # Verify the unit exists.

            cursor.execute("""
                SELECT
                    unit_id,
                    unit_group
                FROM units
                WHERE unit_id = %s
                AND is_active = 1
            """, (
                receiver_unit_id,
            ))

            unit = cursor.fetchone()


            if not unit:

                raise ValueError(
                    "Requested unit does not exist."
                )


            # Verify the formation tier exists
            # for this unit group.

            cursor.execute("""
                SELECT tier_id
                FROM unit_organisation_tiers
                WHERE tier_type = %s
                AND tier = %s
                LIMIT 1
            """, (
                unit["unit_group"],
                receiver_unit_tier
            ))

            tier = cursor.fetchone()


            if not tier:

                raise ValueError(
                    "Invalid requested unit formation."
                )


        # --------------------------------------
        # CREATE TRADE OFFER
        # --------------------------------------

        cursor.execute("""
            INSERT INTO trade_offers (
                sender_nation_id,
                receiver_nation_id,
                status,
                created_turn
            )

            VALUES (
                %s,
                %s,
                'Pending',
                %s
            )
        """, (
            sender_nation_id,
            receiver_nation_id,
            current_turn
        ))


        trade_offer_id = cursor.lastrowid


        # --------------------------------------
        # SENDER RESOURCE ITEM
        # --------------------------------------

        if sender_resource_id:

            cursor.execute("""
                INSERT INTO trade_offer_items (
                    trade_offer_id,
                    side,
                    resource_id,
                    unit_id,
                    tier_level,
                    quantity
                )

                VALUES (
                    %s,
                    'Sender',
                    %s,
                    NULL,
                    NULL,
                    %s
                )
            """, (
                trade_offer_id,
                sender_resource_id,
                int(sender_resource_quantity)
            ))


        # --------------------------------------
        # SENDER UNIT ITEM
        # --------------------------------------

        if sender_unit_id:

            cursor.execute("""
                INSERT INTO trade_offer_items (
                    trade_offer_id,
                    side,
                    resource_id,
                    unit_id,
                    tier_level,
                    quantity
                )

                VALUES (
                    %s,
                    'Sender',
                    NULL,
                    %s,
                    %s,
                    %s
                )
            """, (
                trade_offer_id,
                sender_unit_id,
                sender_unit_tier,
                int(sender_unit_quantity)
            ))


        # --------------------------------------
        # RECEIVER RESOURCE ITEM
        # --------------------------------------

        if receiver_resource_id:

            cursor.execute("""
                INSERT INTO trade_offer_items (
                    trade_offer_id,
                    side,
                    resource_id,
                    unit_id,
                    tier_level,
                    quantity
                )

                VALUES (
                    %s,
                    'Receiver',
                    %s,
                    NULL,
                    NULL,
                    %s
                )
            """, (
                trade_offer_id,
                receiver_resource_id,
                int(receiver_resource_quantity)
            ))


        # --------------------------------------
        # RECEIVER UNIT ITEM
        # --------------------------------------

        if receiver_unit_id:

            cursor.execute("""
                INSERT INTO trade_offer_items (
                    trade_offer_id,
                    side,
                    resource_id,
                    unit_id,
                    tier_level,
                    quantity
                )

                VALUES (
                    %s,
                    'Receiver',
                    NULL,
                    %s,
                    %s,
                    %s
                )
            """, (
                trade_offer_id,
                receiver_unit_id,
                receiver_unit_tier,
                int(receiver_unit_quantity)
            ))

            
        # --------------------------------------
        # CREATE TRADE NOTIFICATION
        # --------------------------------------

        cursor.execute("""
            SELECT
                n.name AS sender_name
            FROM nations n
            WHERE n.nation_id = %s
        """, (
            sender_nation_id,
        ))

        sender = cursor.fetchone()


        # Get the items in the trade

        cursor.execute("""
            SELECT
                toi.side,
                toi.quantity,

                r.name AS resource_name,

                u.unit_name,
                u.unit_group,
                uot.tier_name

            FROM trade_offer_items toi

            LEFT JOIN resources r
                ON toi.resource_id = r.resource_id

            LEFT JOIN units u
                ON toi.unit_id = u.unit_id

            LEFT JOIN unit_organisation_tiers uot
                ON uot.tier_type = u.unit_group
                AND uot.tier = toi.tier_level

            WHERE toi.trade_offer_id = %s

            ORDER BY toi.trade_item_id
        """, (
            trade_offer_id,
        ))

        trade_items = cursor.fetchall()


        # Build notification text

        give_items = []
        receive_items = []


        for item in trade_items:

            if item["resource_name"]:

                item_name = item["resource_name"]

            else:

                item_name = (
                    f"{item['unit_name']} "
                    f"{item['tier_name']}"
                )


            item_text = (
                f"{item_name} × "
                f"{item['quantity']:,}"
            )


            if item["side"] == "Sender":

                give_items.append(
                    item_text
                )

            else:

                receive_items.append(
                    item_text
                )


        give_text = "<br>".join(
            give_items
        )

        receive_text = "<br>".join(
            receive_items
        )


        notification_message = f"""
        <strong>{sender['sender_name']}</strong> has sent you a trade offer.

        <br>

        <strong>They Give:</strong><br>
        {give_text}

        <br>

        <strong>They Request:</strong><br>
        {receive_text}
        """


        cursor.execute("""
            INSERT INTO notifications (
                nation_id,
                type,
                title,
                message,
                icon,
                created_turn,
                is_read,
                reference_id,
                persistent
            )

            VALUES (
                %s,
                'trade_offer',
                'Trade Offer',
                %s,
                '⇄',
                %s,
                0,
                %s,
                1
            )
        """, (
            receiver_nation_id,
            notification_message,
            current_turn,
            trade_offer_id
        ))

        conn.commit()

    except ValueError as error:

        conn.rollback()

        cursor.close()
        conn.close()

        return str(error), 400


    except Exception:

        conn.rollback()

        cursor.close()
        conn.close()

        raise


    cursor.close()
    conn.close()


    return redirect(
        url_for("trade")
    )

@app.route("/api/trade/nation/<int:nation_id>/units")
def trade_nation_units(nation_id):

    current_nation_id = session["nation_id"]

    if nation_id == current_nation_id:

        return {
            "success": False,
            "error": "Invalid nation."
        }, 400


    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)


    cursor.execute("""
        SELECT
            u.unit_id,
            u.unit_name,
            u.unit_group,
            nu.tier_level,
            uot.tier_name,
            COUNT(nu.nation_unit_id) AS quantity

        FROM units u

        JOIN nation_units nu
            ON u.unit_id = nu.unit_id

        LEFT JOIN unit_organisation_tiers uot
            ON uot.tier_type = u.unit_group
            AND uot.tier = nu.tier_level

        WHERE nu.nation_id = %s

        AND nu.status = 'active'

        GROUP BY
            u.unit_id,
            u.unit_name,
            u.unit_group,
            nu.tier_level,
            uot.tier_name

        ORDER BY
            u.unit_name,
            nu.tier_level
    """, (nation_id,))


    units = cursor.fetchall()


    cursor.close()
    conn.close()


    return {
        "success": True,
        "units": units
    }

@app.route("/api/trade/<int:trade_offer_id>/decline", methods=["POST"])
def decline_trade(trade_offer_id):

    nation_id = session["nation_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                trade_offer_id,
                sender_nation_id,
                receiver_nation_id,
                status
            FROM trade_offers
            WHERE trade_offer_id = %s
            FOR UPDATE
        """, (trade_offer_id,))

        offer = cursor.fetchone()

        if not offer:

            raise ValueError(
                "Trade offer not found."
            )

        # Only the receiver can decline.

        if offer["receiver_nation_id"] != nation_id:

            raise ValueError(
                "You cannot decline this trade offer."
            )

        # It must still be pending.

        if offer["status"] != "Pending":

            raise ValueError(
                "This trade offer is no longer pending."
            )

        cursor.execute("""
            UPDATE trade_offers
            SET status = 'Declined'
            WHERE trade_offer_id = %s
        """, (trade_offer_id,))

        conn.commit()

        return {
            "success": True,
            "title": "Trade Declined",
            "message": "The trade offer has been declined.",
            "type": "info",
            "icon": "ℹ"
        }

    except ValueError as error:

        conn.rollback()

        return {
            "success": False,
            "title": "Trade Failed",
            "message": str(error),
            "type": "error",
            "icon": "❌"
        }, 400

    except Exception:

        conn.rollback()

        raise

    finally:

        cursor.close()
        conn.close()

@app.route("/api/trade/<int:trade_offer_id>/accept", methods=["POST"])
def accept_trade(trade_offer_id):

    receiver_nation_id = session["nation_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        # --------------------------------------
        # LOCK THE TRADE OFFER
        # --------------------------------------

        cursor.execute("""
            SELECT
                trade_offer_id,
                sender_nation_id,
                receiver_nation_id,
                status
            FROM trade_offers
            WHERE trade_offer_id = %s
            FOR UPDATE
        """, (trade_offer_id,))

        offer = cursor.fetchone()


        if not offer:

            raise ValueError(
                "Trade offer not found."
            )


        # Only receiver can accept.

        if (
            offer["receiver_nation_id"]
            != receiver_nation_id
        ):

            raise ValueError(
                "You cannot accept this trade offer."
            )


        # Prevent double acceptance.

        if offer["status"] != "Pending":

            raise ValueError(
                "This trade offer is no longer pending."
            )


        sender_nation_id = (
            offer["sender_nation_id"]
        )


        # --------------------------------------
        # GET ALL TRADE ITEMS
        # --------------------------------------

        cursor.execute("""
            SELECT
                trade_item_id,
                side,
                resource_id,
                unit_id,
                tier_level,
                quantity
            FROM trade_offer_items
            WHERE trade_offer_id = %s
            ORDER BY trade_item_id
        """, (trade_offer_id,))

        items = cursor.fetchall()


        if not items:

            raise ValueError(
                "This trade offer contains no items."
            )


        # --------------------------------------
        # SEPARATE THE TWO SIDES
        # --------------------------------------

        sender_items = [
            item
            for item in items
            if item["side"] == "Sender"
        ]

        receiver_items = [
            item
            for item in items
            if item["side"] == "Receiver"
        ]


        if not sender_items:

            raise ValueError(
                "This trade offer has nothing to give."
            )


        if not receiver_items:

            raise ValueError(
                "This trade offer has nothing to receive."
            )


        # --------------------------------------
        # VALIDATE SENDER'S OFFER
        # --------------------------------------

        for item in sender_items:

            quantity = item["quantity"]


            if quantity <= 0:

                raise ValueError(
                    "Trade contains an invalid quantity."
                )


            # RESOURCE

            if item["resource_id"] is not None:

                cursor.execute("""
                    SELECT
                        amount
                    FROM nation_resources
                    WHERE nation_id = %s
                    AND resource_id = %s
                    FOR UPDATE
                """, (
                    sender_nation_id,
                    item["resource_id"]
                ))

                resource = cursor.fetchone()


                if not resource:

                    raise ValueError(
                        "The sender no longer has the offered resource."
                    )


                if resource["amount"] < quantity:

                    raise ValueError(
                        "The sender no longer has enough of the offered resource."
                    )


            # UNIT

            elif item["unit_id"] is not None:

                cursor.execute("""
                    SELECT
                        nation_unit_id
                    FROM nation_units
                    WHERE nation_id = %s
                    AND unit_id = %s
                    AND tier_level = %s
                    AND status = 'active'
                    FOR UPDATE
                """, (
                    sender_nation_id,
                    item["unit_id"],
                    item["tier_level"]
                ))

                units = cursor.fetchall()


                if len(units) < quantity:

                    raise ValueError(
                        "The sender no longer has enough of the offered unit formation."
                    )


            else:

                raise ValueError(
                    "Invalid trade item."
                )


        # --------------------------------------
        # VALIDATE RECEIVER'S OFFER
        # --------------------------------------

        for item in receiver_items:

            quantity = item["quantity"]


            if quantity <= 0:

                raise ValueError(
                    "Trade contains an invalid quantity."
                )


            # RESOURCE

            if item["resource_id"] is not None:

                cursor.execute("""
                    SELECT
                        amount
                    FROM nation_resources
                    WHERE nation_id = %s
                    AND resource_id = %s
                    FOR UPDATE
                """, (
                    receiver_nation_id,
                    item["resource_id"]
                ))

                resource = cursor.fetchone()


                if not resource:

                    raise ValueError(
                        "You do not have the requested resource."
                    )


                if resource["amount"] < quantity:

                    raise ValueError(
                        "You no longer have enough of the requested resource."
                    )


            # UNIT

            elif item["unit_id"] is not None:

                cursor.execute("""
                    SELECT
                        nation_unit_id
                    FROM nation_units
                    WHERE nation_id = %s
                    AND unit_id = %s
                    AND tier_level = %s
                    AND status = 'active'
                    FOR UPDATE
                """, (
                    receiver_nation_id,
                    item["unit_id"],
                    item["tier_level"]
                ))

                units = cursor.fetchall()


                if len(units) < quantity:

                    raise ValueError(
                        "You no longer have enough of the requested unit formation."
                    )


            else:

                raise ValueError(
                    "Invalid trade item."
                )


        # --------------------------------------
        # TRANSFER SENDER RESOURCES
        # --------------------------------------

        for item in sender_items:

            if item["resource_id"] is not None:

                quantity = item["quantity"]


                cursor.execute("""
                    UPDATE nation_resources
                    SET amount = amount - %s
                    WHERE nation_id = %s
                    AND resource_id = %s
                """, (
                    quantity,
                    sender_nation_id,
                    item["resource_id"]
                ))


                cursor.execute("""
                    UPDATE nation_resources
                    SET amount = amount + %s
                    WHERE nation_id = %s
                    AND resource_id = %s
                """, (
                    quantity,
                    receiver_nation_id,
                    item["resource_id"]
                ))


        # --------------------------------------
        # TRANSFER RECEIVER RESOURCES
        # --------------------------------------

        for item in receiver_items:

            if item["resource_id"] is not None:

                quantity = item["quantity"]


                cursor.execute("""
                    UPDATE nation_resources
                    SET amount = amount - %s
                    WHERE nation_id = %s
                    AND resource_id = %s
                """, (
                    quantity,
                    receiver_nation_id,
                    item["resource_id"]
                ))


                cursor.execute("""
                    UPDATE nation_resources
                    SET amount = amount + %s
                    WHERE nation_id = %s
                    AND resource_id = %s
                """, (
                    quantity,
                    sender_nation_id,
                    item["resource_id"]
                ))


        # --------------------------------------
        # TRANSFER SENDER UNITS
        # --------------------------------------

        for item in sender_items:

            if item["unit_id"] is not None:

                quantity = item["quantity"]


                cursor.execute("""
                    SELECT
                        nation_unit_id
                    FROM nation_units
                    WHERE nation_id = %s
                    AND unit_id = %s
                    AND tier_level = %s
                    AND status = 'active'
                    LIMIT %s
                    FOR UPDATE
                """, (
                    sender_nation_id,
                    item["unit_id"],
                    item["tier_level"],
                    quantity
                ))

                selected_units = cursor.fetchall()


                for unit in selected_units:

                    cursor.execute("""
                        UPDATE nation_units
                        SET nation_id = %s
                        WHERE nation_unit_id = %s
                    """, (
                        receiver_nation_id,
                        unit["nation_unit_id"]
                    ))


        # --------------------------------------
        # TRANSFER RECEIVER UNITS
        # --------------------------------------

        for item in receiver_items:

            if item["unit_id"] is not None:

                quantity = item["quantity"]


                cursor.execute("""
                    SELECT
                        nation_unit_id
                    FROM nation_units
                    WHERE nation_id = %s
                    AND unit_id = %s
                    AND tier_level = %s
                    AND status = 'active'
                    LIMIT %s
                    FOR UPDATE
                """, (
                    receiver_nation_id,
                    item["unit_id"],
                    item["tier_level"],
                    quantity
                ))

                selected_units = cursor.fetchall()


                for unit in selected_units:

                    cursor.execute("""
                        UPDATE nation_units
                        SET nation_id = %s
                        WHERE nation_unit_id = %s
                    """, (
                        sender_nation_id,
                        unit["nation_unit_id"]
                    ))


        # --------------------------------------
        # MARK TRADE ACCEPTED
        # --------------------------------------

        cursor.execute("""
            UPDATE trade_offers
            SET status = 'Accepted'
            WHERE trade_offer_id = %s
        """, (
            trade_offer_id,
        ))


        conn.commit()


        return {
            "success": True,
            "title": "Trade Accepted",
            "message": "The trade has been completed successfully.",
            "type": "success",
            "icon": "✓"
        }


    except ValueError as error:

        conn.rollback()

        return {
            "success": False,
            "title": "Trade Failed",
            "message": str(error),
            "type": "error",
            "icon": "❌"
        }, 400


    except Exception:

        conn.rollback()

        raise


    finally:

        cursor.close()
        conn.close()

if __name__ == "__main__": 
    app.run()