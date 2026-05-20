from flask import Flask, render_template
import mysql.connector
import os

app = Flask(__name__)

db_password = os.getenv("DB_PASSWORD")


@app.route("/")
def home():

    # CONNECT TO DATABASE (connect to the database with the following information)
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

    # CREATE CURSOR (SQL Script)
    cursor = db.cursor(dictionary=True)

    # RUN QUERY (run the SQL script with the following code)
    cursor.execute("SELECT * FROM units")

    # GET DATA (units = whatever the SQL script returns)
    units = cursor.fetchall()

    # CLOSE CONNECTION (close the connection to the database)
    cursor.close()
    db.close()

    # SEND DATA TO HTML (when you render the HTML, also send the units data to the HTML)
    return render_template(
        "index.html",
        units=units
    )

if __name__ == "__main__": 
    app.run(debug=True)