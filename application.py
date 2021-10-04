import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash


from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///fitness.db")

# Make sure API key is set
# if not os.environ.get("API_KEY"):
    # raise RuntimeError("API_KEY not set")

# /
@app.route("/")
@login_required
def index():
    sum_run_rows = db.execute("SELECT ROUND(SUM(run), 2) FROM run WHERE user_id = :user_id", user_id = session['user_id'])

    weight_loss = db.execute("SELECT ROUND(MAX(weight)-MIN(weight), 1) FROM weight WHERE user_id = :user_id", user_id = session['user_id'])

    return render_template("index.html", sum_run_rows = sum_run_rows, weight_loss = weight_loss)


# login
@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

# logout
@app.route("/logout")
def logout():

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

# register
@app.route("/register", methods=["GET", "POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    if request.method == "GET":
        return render_template("register.html")
    else:
        if not request.form.get("username"):
            return apology("Missing username!")
        elif password == request.form.get("confirmation"):
            # hash the password
            hash = generate_password_hash(password)
            # add user to database, checking to make sure they are not already registered
            success = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=username, hash=hash)
            if not success:
                return apology("Username already exists")
            # log them in
            rows = db.execute("SELECT id FROM users WHERE username = :username", username=username)
            if not rows:
                return apology("Query failed")
            session["user_id"] = rows[0]["id"]
            return redirect("/")
        else:
            return apology("Passwords do not match!")



# bmi
@app.route("/bmi")
@login_required
def bmi():
     return render_template("bmi.html")

# weight logs
@app.route("/weight_log")
@login_required
def weight_log():
    # Extract user weight
    weight_rows = db.execute("SELECT weight, datetime FROM weight WHERE user_id = :user_id", user_id = session['user_id'])

    # Process each row
    weight_rows_parsed = []
    counter = 0
    for row in weight_rows:
        weight = row['weight']
        datetime = row['datetime']

        single_row = {}
        single_row['weight'] = weight
        single_row['datetime'] = datetime

        weight_rows_parsed.append(single_row)
        counter = counter + 1

    return render_template("weight_log.html", weight_rows = weight_rows_parsed)

# run logs
@app.route("/run_log")
@login_required
def run_log():
    # Extract user run
    run_rows = db.execute("SELECT run, minutes, datetime FROM run WHERE user_id = :user_id", user_id = session['user_id'])
    print(run_rows)
    # Process each row
    run_rows_parsed = []
    counter = 0
    for row in run_rows:
        run = row['run']
        minutes = row['minutes']
        datetime = row['datetime']

        single_row = {}
        single_row['run'] = run
        single_row['minutes'] = minutes
        single_row['datetime'] = datetime

        run_rows_parsed.append(single_row)
        counter = counter + 1

    return render_template("run_log.html", run_rows = run_rows_parsed)

# weight
@app.route("/weight", methods=["GET", "POST"])
@login_required
def weight():
    if request.method == "GET":
        return render_template("weight.html")

    else:
        # ensure symbol valid, not empty
        weight = request.form.get('weight')
        if not request.form.get("weight"):
            return apology("Please enter weight in kg")
        else:
            weight = float(weight)
            # valid ensured. Send to page
            rows = db.execute("INSERT INTO weight (user_id, weight) VALUES (:user_id, :weight)", user_id=session["user_id"], weight=weight)
            rows = db.execute("UPDATE weight SET weight = round(weight, 2) WHERE user_id = :user_id", user_id = session['user_id'])
            if not rows:
                return apology("input failed, try again")
            flash(f"You weigh {weight} kg")
            return redirect("/")
        return render_template("weight.html")

# run
@app.route("/run", methods=["GET", "POST"])
@login_required
def run():
    if request.method == "GET":
        return render_template("run.html")

    else:
        # ensure symbol valid, not empty
        run = request.form.get('run')
        if not request.form.get("run"):
            return apology("Please enter distance ran in km")
        minutes = request.form.get('minutes')
        if not request.form.get("minutes"):
            return apology("Please enter total time taken in minutes")
        else:
            run = float(run)
            minutes = float(minutes)
            # valid ensured. Send to page
            rows = db.execute("INSERT INTO run (user_id, run, minutes) VALUES (:user_id, :run, :minutes)", user_id=session["user_id"], run=run, minutes=minutes)
            rows = db.execute("UPDATE run SET run = round(run, 2) WHERE user_id = :user_id", user_id = session['user_id'])
            if not rows:
                return apology("input failed, try again")
            flash(f"You ran {run} km in {minutes} minutes")
            return redirect("/")
        return render_template("run.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)



