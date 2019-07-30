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
        flash("Email already registered.", "danger")
        return redirect(url_for('index'))
    db.execute("INSERT INTO users (name, password, email) VALUES (:name, :password, :email)",
            {"name": name, "password": password, "email": email})
    db.commit()
    flash("You are now registered.", "success")
    return redirect(url_for('index'))

@app.route("/search", methods=["GET", "POST"])
def search():
    """"Search for books."""
    if request.method == "GET":
        return render_template("search.html")
    else:
        # Get form information.
        keyword = request.form.get("keyword").lower()

        # Check if keyword is part of ISBN Number.
        if db.execute("SELECT * FROM books WHERE lower(isbn) like :keyword OR lower(title) like :keyword OR lower(author) like :keyword", {"keyword": "%"+keyword+"%"}).rowcount == 0:
            flash("Book does not exist.", "danger")
            return redirect(url_for('search'))

        books = db.execute("SELECT * FROM books WHERE lower(isbn) like :keyword OR lower(title) like :keyword OR lower(author) like :keyword", {"keyword": "%"+keyword+"%"}).fetchall()
        return render_template("search.html",books=books)

@app.route("/<string:isbn>", methods=["GET", "POST"])
def bookdetails(isbn):

    #dynamically create a web page for each book search result
    isbn = isbn.lower()
    if request.method == "POST":
        """"Get user review for a book."""
        # Get form information.
        rating = request.form.get("gridRadios")
        if rating=='option1':
            rating=1
        elif rating=='option2':
            rating=2
        elif rating=='option3':
            rating=3
        elif rating=='option4':
            rating=4
        elif rating=='option5':
            rating=5
        comment = request.form.get("comment")
        userid = session["userid"]

        # Check if userid has previously submitted a review for this ISBN Number.
        if db.execute("SELECT * FROM reviews WHERE lower(isbn)=:isbn AND userid=:userid", {"isbn": isbn, "userid": userid}).rowcount > 0:
            flash("User has already submitted a review for this book.", "danger")
            book = db.execute("SELECT * FROM books WHERE lower(isbn)=:isbn", {"isbn":isbn}).fetchone()
            return render_template("bookdetails.html",book=book,isbn=isbn)

        db.execute("INSERT INTO reviews (rating, comment, isbn, userid) VALUES (:rating, :comment, :isbn, :userid)",
                {"rating": rating, "comment": comment, "isbn": isbn, "userid": userid})
        #db.execute("INSERT INTO reviews (rating, comment, isbn, userid) VALUES (5, 'best book', '380795272', 1)")
        db.commit()
        flash("You submitted a review.", "success")

    if db.execute("SELECT * FROM books WHERE lower(isbn)=:isbn", {"isbn":isbn}).rowcount == 0:
        #return "The following ISBN does not exist: {}".format(isbn)
        flash("The #following ISBN does not exist: {}".format(isbn), "danger")
        return redirect(url_for('search'))

    book = db.execute("SELECT * FROM books WHERE lower(isbn)=:isbn", {"isbn":isbn}).fetchone()
    return render_template("bookdetails.html",book=book,isbn=isbn)

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
    sessionuser = session["user"]
    userid= db.execute("SELECT userid FROM users WHERE email=:sessionuser", {"sessionuser": sessionuser}).fetchone()
    session["userid"]=userid[0]
    return redirect(url_for('search'))

@app.route("/logout")
def logout():
    session.pop('user',None)
    session.clear()
    flash("You are now logged out.", "success")
    return redirect(url_for('index'))
