import os

from flask import Flask, session, render_template, request, url_for, redirect, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    """"Register for the site."""

    # Get form information.
    name = request.form.get("name")
    password = request.form.get("password")
    email = request.form.get("email")

    # Check if email is already taken.
    if db.execute("SELECT * FROM users WHERE email = :email", {"email": email}).rowcount > 0:
        return render_template("error.html", message="Email already registered.")
    db.execute("INSERT INTO users (name, password, email) VALUES (:name, :password, :email)",
            {"name": name, "password": password, "email": email})
    db.commit()
    flash("You are now registered.", "success")
    return redirect(url_for('index'))

@app.route("/login", methods=["POST"])
def login():
    """"Login to the site."""

    # Get form information.
    username = request.form.get("username1")
    password = request.form.get("password1")

    # Check if user credentials are accurate.
    if db.execute("SELECT * FROM users WHERE email = :email", {"email": username}).rowcount==0:
        flash("Email does not exist.", "danger")
        return redirect(url_for('index'))

    if db.execute("SELECT * FROM users WHERE password = :password", {"password": password}).rowcount == 0:
        flash("Password does not match.", "danger")
        return redirect(url_for('index'))

    flash("You are now logged in.", "success")
    session["log"] = True
    session["user"] = username

    return redirect(url_for('index'))

@app.route("/logout")
def logout():
    session.pop('user',None)
    session.clear()
    flash("You are now logged out.", "success")
    return redirect(url_for('index'))
