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
from flask_bcrypt import Bcrypt

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

bcrypt = Bcrypt(app)

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
            "SELECT username, password FROM User WHERE username = ?",
            [username],
            one=True,
        )
        db.close()

        print("user value:", user)
        if user and bcrypt.check_password_hash(user["password"], password):
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
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        type = request.form["type"]

        db = get_db()

        # make a new cursor from the database connection
        cur = db.cursor()

        # Stores the info in the db.
        try:
            cur.execute(
                "INSERT INTO User values (?,?,?,?,?)",
                [username, hashed_password, firstname, lastname, type],
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
    
@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if "user" not in session:
        abort(403, "You are not allowed access")
    db = get_db()

    user = query_db(
        "SELECT firstname, lastname, type FROM User WHERE username = (?)",
        [session["user"]],
        one=True,
    )
    db.close()
    if (user["type"] == "i"):
        abort(403, "This view is students only")
    if request.method == "POST":
        ins = request.form["instructor"]
        msg = request.form["message"]
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute(
                "INSERT INTO anon(message, username) VALUES (?,?)",
                [msg,ins],
            )
            db.commit()
        except sqlite3.InterfaceError as err:
            flash("Feedback not added.")
    return render_template("anon.html", user=session["user"])
    

@app.route("/instructor-viewfeedback")
def instructor_feedback():
    sql_anon_feedback = """
    SELECT message
    FROM anon
    WHERE username = ?
    """
    anon_feedback = query_db(sql_anon_feedback, (session["user"],))
    
    for p in anon_feedback:
        res = [p[key] for key in ('message',)]
        print(res)
        check = ('message',)
        return render_template("instructor-viewfeedback.html",
                        instructor_name=session["user"],
                        urhelp=check,
                        anon_feedback=anon_feedback)  

@app.route("/student-marks")
def student_marks():
    sql_student_marks_a1 = """
    SELECT mark 
    FROM marks
    WHERE username = ? AND aid = 1
    """
    mark_a1 = query_db(sql_student_marks_a1, (session["user"],))

    sql_student_marks_a2 = """
    SELECT mark 
    FROM marks
    WHERE username = ? AND aid = 2
    """
    mark_a2 = query_db(sql_student_marks_a2, (session["user"],))

    sql_student_marks_a3 = """
    SELECT mark 
    FROM marks
    WHERE username = ? AND aid = 3
    """
    mark_a3 = query_db(sql_student_marks_a3, (session["user"],))

    sql_student_marks_mid = """
    SELECT mark 
    FROM marks
    WHERE username = ? AND aid = 4
    """
    mark_mid = query_db(sql_student_marks_mid, (session["user"],))

    sql_student_marks_f = """
    SELECT mark 
    FROM marks
    WHERE username = ? AND aid = 5
    """
    mark_f = query_db(sql_student_marks_f, (session["user"],))

    if (len(mark_a1) == 0):
        tempa1 = 'Unreleased'
    else:
        tempa1 = mark_a1[0]['mark']
    
    if (len(mark_a2) == 0):
        tempa2 = 'Unreleased'
    else:
        tempa2=mark_a2[0]['mark']
    
    if (len(mark_a3) == 0):
        tempa3 = 'Unreleased'
    else:
        tempa3 = mark_a3[0]['mark']

    if (len(mark_mid) == 0):
        tempmid = 'Unreleased'
    else:
        tempmid = mark_mid[0]['mark']

    if (len(mark_f) == 0):
        tempf = 'Unreleased'
    else:
        tempf = mark_f[0]['mark']
    
    
    return render_template("student-marks.html",
                        a1=tempa1,
                        a2=tempa2,
                        a3=tempa3,
                        mid=tempmid,
                        final=tempf)  



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
