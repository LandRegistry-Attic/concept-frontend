import os
from flask import Flask
from flask import render_template
from functools import wraps
from flask import request, Response
import string


app = Flask(__name__)

def check_auth(username, password):
    expectedUsr = os.environ['LAND_REG_USR']
    expectedPasswd = os.environ['LAND_REG_PSWD']
    return username == expectedUsr and password == expectedPasswd


def authenticate():
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/')
#@requires_auth
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")


