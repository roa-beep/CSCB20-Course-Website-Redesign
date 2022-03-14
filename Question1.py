from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "hi"

@app.route("/<name>")
def user(name):
    name = name.strip()
    newname = ''
    if (name.isalpha() == False):
        for c in name:
                if c.isalpha():
                    newname += c
        return f'<h1>Welcome, {newname}, to my CSCB20 website!</h1>'
    elif (name.isupper()):
        newname = name.lower()
    elif (name.islower()):
        newname = name.upper()
    else:
        return f'<h1>Welcome, {name}, to my CSCB20 website!</h1>'
    return f'<h1>Welcome, {newname}, to my CSCB20 website!</h1>'

print(user('Dave'))

if (__name__) == "__main__":
    app.run(debug = True, port=4000)