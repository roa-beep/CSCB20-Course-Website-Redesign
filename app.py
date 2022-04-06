from flask import (
    Flask,
    redirect,
    render_template,
    request,
    url_for,
    session,
    abort,
    flash,
    g,
)
import sqlite3

DATABASE = "Assignment3.db"
TABLE = "User"


def get_db():
    db = getattr(g, "database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        cur = db.cursor()
        cur.execute(
            """create table if not exists {} (
            username TEXT PRIMARY KEY, 
            password TEXT, 
            firstName TEXT, 
            lastName TEXT,
            type TEXT)""".format(
                TABLE
            )
        )
    db.row_factory = make_dicts
    return db


def make_dicts(cursor, row):
    print("Make_dicts", "Cursor:", cursor.description, "row:", row)
    return dict((cursor.description[idx][0], value) for idx, value in enumerate(row))


def query_db(query, args=(), one=False):
    print("Query value:", query, "Args value:", args)
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


app = Flask(__name__)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        # close the database if we are connected to it
        db.close()


@app.route("/api/login", methods=["GET", "POST"])
def login():
    session.pop("user", None)

    if request.method == "POST":
        # Checks if the user gave all necessary information
        if not ("username" in request.form and "password" in request.form):
            flash("Did not enter all necessary information")
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()

        user = query_db(
            "SELECT username, password FROM User WHERE username = ? and password = ?",
            [username, password],
            one=True,
        )
        db.close()

        print("user value:", user)
        if user:
            session["user"] = username
            return redirect(url_for("home"))
        else:
            flash("The username and/or password is invalid")

    return render_template("login.html")


@app.route("/api/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":
        # Checks if the user gave all necessary information
        if not (
            "firstname" in request.form
            and "lastname" in request.form
            and "username" in request.form
            and "password" in request.form
            and "type" in request.form
        ):
            flash("Did not enter all necessary information")

        firstname = request.form["firstname"]
        lastname = request.form["lastname"]
        username = request.form["username"]
        password = request.form["password"]
        type = request.form["type"]

        db = get_db()

        # make a new cursor from the database connection
        cur = db.cursor()

        # Stores the info in the db.
        try:
            cur.execute(
                "INSERT INTO User values (?,?,?,?,?)",
                [username, password, firstname, lastname, type],
            )
            db.commit()
            flash("User successfully added")
        except sqlite3.IntegrityError as err:
            flash("That username already exists. Please choose a new one.")

        db.close()

    return render_template("signup.html")


@app.route("/")
def index():
    return redirect(url_for("login"))
    


@app.route("/home")
def home():
    if "user" not in session:
        abort(403, "You are not allowed access")

    db = get_db()

    user = query_db(
        "SELECT firstname, lastname, type FROM User WHERE username = (?)",
        [session["user"]],
        one=True,
    )
    db.close()

    firstname, lastname = user["firstName"], user["lastName"]
    if (user["type"] == "s"):
        return render_template("studenthome.html", firstname=firstname, lastname=lastname)
    else:
        return render_template("instructorhome.html", firstname=firstname, lastname=lastname)


if __name__ == "__main__":
    app.secret_key = b"secretkey"
    app.run(debug=True)
