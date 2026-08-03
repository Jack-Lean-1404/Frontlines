from flask import Flask, render_template, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from datetime import datetime
from flask import redirect, url_for
import mysql.connector
import os


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

    # -------------------------
    # GET RESOURCES
    # -------------------------
    cursor.execute("""
        SELECT
            nation_resources.amount,
            resources.name,
            resources.measurement_convention
        FROM nation_resources

        JOIN resources
            ON nation_resources.resource_id = resources.resource_id

        WHERE nation_resources.nation_id = %s
    """, (session["nation_id"],))

    resources = cursor.fetchall()

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

    return render_template(
        "dashboard.html",
        nation=nation,
        resources=resources,
        turn_labels=turn_labels,
        money_values=money_values
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
        tier = row["tier"]
        name = row["tier_name"]

        if group_id not in organisation_names:
            organisation_names[group_id] = {}

        organisation_names[group_id][tier] = name
        
    for unit in units:
        unit["unit_group"] = int(unit["unit_group"])

    return render_template(
    "production.html",
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
    buildings=buildings
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
        SELECT line_id
        FROM production_queue
        WHERE queue_id = %s
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
        "success": True
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
        SELECT line_id
        FROM building_queue
        WHERE queue_id = %s
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
        "success": True
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
    tier = data["tier"]


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
            pl.line_id,
            pl.line_name,
            COUNT(pq.queue_id) AS queue_size

        FROM production_lines pl

        LEFT JOIN production_queue pq
            ON pl.line_id = pq.line_id

        WHERE pl.line_type = %s

        GROUP BY
            pl.line_id,
            pl.line_name

        ORDER BY queue_size ASC

        LIMIT 1
    """, (unit["unit_class"],))

    line = cursor.fetchone()

    if not line:
        return jsonify({
            "success": False,
            "error": "No production line found"
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
        (tier - 1)
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
        tier,
        position,
        turns_remaining,
        status
    ))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "line": line["line_name"],
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

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get the building
    cursor.execute("""
        SELECT *
        FROM buildings
        WHERE building_id = %s
    """, (building_id,))

    building = cursor.fetchone()

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

        return jsonify({
            "success": False,
            "error": "No construction line found"
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
            %s
        )
    """, (
        line["line_id"],
        building_id,
        position,
        building["build_time"],
        status
    ))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "line": line["line_name"],
        "position": position
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

if __name__ == "__main__": 
    app.run()