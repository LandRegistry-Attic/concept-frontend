import os
from flask import Flask, redirect, render_template, abort
from functools import wraps
from flask.ext.assets import Environment, Bundle
from flask.ext.basicauth import BasicAuth
import logging
from raven.contrib.flask import Sentry
import string
import json
import requests

TITLES_SCHEME_DOMAIN_PORT = os.environ.get('TITLES_SCHEME_DOMAIN_PORT')

app = Flask(__name__)

# Auth
if os.environ.get('BASIC_AUTH_USERNAME'):
    app.config['BASIC_AUTH_USERNAME'] = os.environ['BASIC_AUTH_USERNAME']
    app.config['BASIC_AUTH_PASSWORD'] = os.environ['BASIC_AUTH_PASSWORD']
    app.config['BASIC_AUTH_FORCE'] = True
    basic_auth = BasicAuth(app)

# Static assets
assets = Environment(app)
css_main = Bundle(
    'stylesheets/main.scss',
    filters='scss',
    output='build/stylesheets/main.css',
    depends="**/*.scss"
)
assets.register('css_main', css_main)

# Sentry exception reporting
if 'SENTRY_DSN' in os.environ:
    sentry = Sentry(app, dsn=os.environ['SENTRY_DSN'])

# Logging
@app.before_first_request
def setup_logging():
    if not app.debug:
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.INFO)
@app.route('/')
def home():
    res = requests.get("%s/titles" % TITLES_SCHEME_DOMAIN_PORT)
    res.raise_for_status()
    return render_template('/index.html', titles=res.json()['titles'])

@app.route('/properties/<property_id>')
def property(property_id):
    title_info = load_title(property_id)
    title_extent_json = json.dumps(title_info['title']['extent'])
    if title_info:
        return render_template("property.html",
            title=title_info['title'],
            title_extent_json=title_extent_json
        )
    else:
        return abort(404)

def load_title(property_id):
    res = requests.get("%s/titles/%s" % (TITLES_SCHEME_DOMAIN_PORT, property_id))
    if res.status_code == 404:
        return None
    return res.json()

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=7000)
