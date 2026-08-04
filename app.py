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
        tier_id = row["tier_id"]
        name = row["tier_name"]

        if group_id not in organisation_names:
            organisation_names[group_id] = {}

        organisation_names[group_id][tier_id] = name
        
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

    # Select all active nations and their capitals and cities
    cursor.execute("""
    SELECT
        nation_id,
        capital_count,
        city_count
    FROM nations
    WHERE is_active = 1
    """)

    nations = cursor.fetchall()

    for nation in nations:
        income = (
            nation["capital_count"] * 200000000 +
            nation["city_count"] * 50000000
        )

        print(f"Nation {nation['nation_id']} earned ${income:,}")

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
        """, (
            session["nation_id"],
            unit["unit_class"]
        ))

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

if __name__ == "__main__": 
    app.run()