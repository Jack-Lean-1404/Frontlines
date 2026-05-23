from flask import Flask, render_template, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from datetime import datetime
from flask import redirect, url_for
import mysql.connector
import os


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

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

    if "user_id" not in session:
        return redirect(url_for("access"))

    return render_template("dashboard.html")


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

    print("Entered password:", password)
    print("Stored hash:", user["password_hash"])
    print(check_password_hash(user["password_hash"], password))

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

    print("test")

    # CHECK LOGIN
    if "user_id" not in session:
        return redirect(url_for("access"))

    # CHECK ADMIN
    if session["role"] != "admin":
        return "Access Denied", 403

    db = get_db_connection()

    cursor = db.cursor(dictionary=True)

    # GET ALL USERS
    cursor.execute("""
        SELECT * FROM frontlinesdb.users;
    """)

    users = cursor.fetchall()

    # GET ALL NATIONS
    cursor.execute("""
        SELECT * FROM frontlinesdb.nations;
    """)

    nations = cursor.fetchall()

    cursor.close()
    db.close()


    return render_template(
        "admin.html",
        users=users,
        nations=nations
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

if __name__ == "__main__": 
    app.run(debug=True)