from flask import Flask

app = Flask(__name__)

@app.route("/CSCB20-A2")
def user(name):
    newname = ''
    if (not name.isalpha()):
        for c in name:
            if c.isaslpha():
                newname = newname + c
        return '''
                <h1>Welcome, {newname}, to my CSCB20 website!</h1>
        '''
    elif (name[0] == ' ' and name[1] == ' '):
        newname = name[2:]
        newname = newname[0].upper() + newname[1:].lower()
    elif (name.isupper()):
        newname = name.lower()
    elif (name.islower()):
        newname = name.upper()
    return '''
    <h1>Welcome, {newname}, to my CSCB20 website!</h1>
    '''
if (__name__) == "__main__":
    app.run(debug = True)