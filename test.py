def user(name):
    name = name.strip()
    newname = ''
    if (name.isalpha() == False):
        for c in name:
                if c.isalpha():
                    newname += c
        return newname
    elif (name.isupper()):
        newname = name.lower()
    elif (name.islower()):
        newname = name.upper()
    else:
        return name
    return newname

print(user('Dave'))