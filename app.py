from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="YOUR_PASSWORD",
    database="example_game"
)

@app.route("/")
def index():

    # Create cursor
    cursor = db.cursor(dictionary=True)

    # SQL query
    cursor.execute("SELECT * FROM units")

    # Fetch all rows
    units = cursor.fetchall()

    # Send data to HTML template
    return render_template("index.html", units=units)

if __name__ == "__main__":
    app.run(debug=True)