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
app.secret_key = b"secretkey"

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
    if "user" not in session:
        abort(403, "You are not allowed access")
    db = get_db()

    user = query_db(
        "SELECT firstname, lastname, type FROM User WHERE username = (?)",
        [session["user"]],
        one=True,
    )
    db.close()
    if (user["type"] == "s"):
        abort(403, "This view is instructors only")
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
    return render_template("instructor-viewfeedback.html",
                        anon_feedback=anon_feedback)  

def get_assignments():
    # returns all the assignments
    sql_assignments = """
    SELECT assignment
    FROM marks
    ORDER BY username ASC, aid ASC
    """
    return query_db(sql_assignments)

def get_students():
    # returns all the assignments
    sql_assignments = """
    SELECT student_num
    FROM marks
    ORDER BY username ASC, aid ASC
    """
    return query_db(sql_assignments)

def get_student_names():
    # returns all the assignments
    sql_assignments = """
    SELECT student_name
    FROM marks
    ORDER BY username ASC, aid ASC
    """
    return query_db(sql_assignments)

@app.route("/instructor-viewgrades")
def instructor_viewgrades():
    if "user" not in session:
        abort(403, "You are not allowed access")
    db = get_db()

    user = query_db(
        "SELECT firstname, lastname, type FROM User WHERE username = (?)",
        [session["user"]],
        one=True,
    )
    db.close()
    if (user["type"] == "s"):
        abort(403, "This view is instructors only")
    sql = """
    SELECT mark
    FROM marks
    ORDER BY username ASC, aid ASC
    """
    grades_tuples = query_db(sql)
    assignments = get_assignments()
    students = get_students()
    names = get_student_names()
    return render_template("instructor-viewgrades.html",
                           instructor_name=session["user"],
                           grades=grades_tuples,
                           names=names,
                           students=students,
                           assignments=assignments)



def get_assignment_id():
    # returns all the assignments
    sql_assignments = """
    SELECT DISTINCT aid
    FROM marks
    ORDER BY aid ASC
    """
    return query_db(sql_assignments)


@app.route("/instructor-grader", methods=["GET", "POST"])
def instructor_grading():
    if "user" not in session:
        abort(403, "You are not allowed access")
    db = get_db()

    user = query_db(
        "SELECT firstname, lastname, type FROM User WHERE username = (?)",
        [session["user"]],
        one=True,
    )
    db.close()
    if (user["type"] == "s"):
        abort(403, "This view is instructors only")
    if request.method == "POST":
        student_num = request.form["snum"]
        assignment = request.form["regrade-id"]
        mark = request.form["grade"]
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute(
                "UPDATE marks SET mark = ? WHERE student_num = ? AND assignment = ?",
                [mark,student_num,assignment],
            )
            db.commit()
        except sqlite3.InterfaceError as err:
            flash("Grade not added.")
    
    return render_template("instructor-grader.html",
                           instructor_name=session["user"],
                           error=False)




@app.route("/instructor-enter-grade", methods=["GET", "POST"])
def instructor_enter_grade():
    if "user" not in session:
        abort(403, "You are not allowed access")
    db = get_db()

    user = query_db(
        "SELECT firstname, lastname, type FROM User WHERE username = (?)",
        [session["user"]],
        one=True,
    )
    db.close()
    if (user["type"] == "s"):
        abort(403, "This view is instructors only")

    if request.method == "POST":
        username = request.form["username"]
        aid = request.form["aid"]
        mark = request.form["grade"]
        assignment = request.form["regrade-id"]
        student_num = request.form["snum"]
        student_name = request.form["student-name"]

        db = get_db()
        cur = db.cursor()
        try:
            cur.execute(
                "INSERT INTO marks (username, aid, mark, assignment, student_num, student_name) VALUES (?, ?, ?, ?, ?, ?)",
                [username, aid, mark, assignment, student_num, student_name],
            )
            db.commit()
        except sqlite3.InterfaceError as err:
            flash("Grade not added.")    
    return render_template("instructor-enter-grade.html",
                           instructor_name=session["user"],
                           error=False)





@app.route("/student-remark", methods=["GET", "POST"])
def student_remark():
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
        student_num = request.form["snum"]
        assignment_id = request.form["regrade-id"]
        reason = request.form["reason"]
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute(
                "INSERT INTO remark_requests(student_num, aid, regrade_reason) VALUES (?,?, ?)",
                [student_num, assignment_id, reason],
            )
            db.commit()
        except sqlite3.InterfaceError as err:
            flash("Remark not added.")
    
    return render_template("student-remark.html",
                           student_name=session["user"],
                           error=False)
    
@app.route("/instructor-viewremark")
def instructor_viewregrade():
    if "user" not in session:
        abort(403, "You are not allowed access")
    db = get_db()

    user = query_db(
        "SELECT firstname, lastname, type FROM User WHERE username = (?)",
        [session["user"]],
        one=True,
    )
    db.close()
    if (user["type"] == "s"):
        abort(403, "This view is instructors only")
    sql_reason = """
    SELECT regrade_reason
    FROM remark_requests
    ORDER BY student_num ASC, aid ASC
    """
    sql_sn = """
    SELECT student_num
    FROM remark_requests
    ORDER BY student_num ASC, aid ASC
    """
    sql_aid = """
    SELECT aid
    FROM remark_requests
    ORDER BY student_num ASC, aid ASC
    """
    remark_tuples = query_db(sql_reason)
    student_num = query_db(sql_sn)
    aid = query_db(sql_aid)
    return render_template("instructor-viewregrade.html",
                           instructor_name=session["user"],
                           remark=remark_tuples,
                           student_num=student_num,
                           aid=aid)





@app.route("/student-marks")
def student_marks():
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
    sql_student_marks = """
    SELECT mark 
    FROM marks
    WHERE username = ?
    ORDER BY aid ASC
    """
    sql_assignments = """
    SELECT assignment
    FROM marks
    WHERE username = ?
    ORDER BY aid ASC
    """
    marks_tuples = query_db(sql_student_marks, (session["user"],))
    assignments = query_db(sql_assignments, (session["user"],))
    return render_template("student-marks.html",
                        assignments=assignments,
                        grades=marks_tuples)  

@app.route("/assignments")
def assignments():
    if "user" not in session:
        abort(403, "You are not allowed access")
    db = get_db()

    user = query_db(
        "SELECT firstname, lastname, type FROM User WHERE username = (?)",
        [session["user"]],
        one=True,
    )
    db.close()
    if (user["type"] == "s"):
        abort(403, "This view is instructors only")
    return render_template("asgmt.html")

@app.route("/labs")
def labs():
    if "user" not in session:
        abort(403, "You are not allowed access")
    db = get_db()

    user = query_db(
        "SELECT firstname, lastname, type FROM User WHERE username = (?)",
        [session["user"]],
        one=True,
    )
    db.close()
    if (user["type"] == "s"):
        abort(403, "This view is instructors only")
    return render_template("labs.html")

@app.route("/courseteam")
def courseteam():
    if "user" not in session:
        abort(403, "You are not allowed access")
    db = get_db()

    user = query_db(
        "SELECT firstname, lastname, type FROM User WHERE username = (?)",
        [session["user"]],
        one=True,
    )
    db.close()
    if (user["type"] == "s"):
        abort(403, "This view is instructors only")
    return render_template("courseteam.html")

@app.route("/assignments-student")
def assignments_student():
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
    return render_template("asgmt-student.html")

@app.route("/labs-student")
def labs_student():
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
    return render_template("labs-student.html")

@app.route("/courseteam-student")
def courseteam_student():
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
    return render_template("courseteam-student.html")

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
    app.run(debug=True)
