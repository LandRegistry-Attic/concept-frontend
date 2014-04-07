import os
from flask import Flask, redirect, render_template, abort, request
from functools import wraps
from flask.ext.assets import Environment, Bundle
from flask.ext.basicauth import BasicAuth
import logging
from raven.contrib.flask import Sentry
from flask import jsonify
import string
import json
import requests

TITLES_SCHEME_DOMAIN_PORT = os.environ.get('TITLES_SCHEME_DOMAIN_PORT', os.environ.get('TITLES_1_PORT_8004_TCP', '').replace('tcp://', 'http://'))

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
    if title_info:
        title_extent_json = json.dumps(title_info['title'].get('extent', {}))
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

def load_titles_by_postcode(postcode):
    res = requests.get("%s/titles?postcode=%s" % (TITLES_SCHEME_DOMAIN_PORT, postcode))
    if res.status_code == 404:
        return None
    return res.json()

@app.route('/properties')
def properties():
        if 'postcode' in request.args:
            titles_info = load_titles_by_postcode( request.args['postcode'] )
            if titles_info:
                return render_template('/index.html', titles=titles_info['titles'])
            else:
                return "No titles found", 200
        else:
            return "Request for all titles not supported", 403


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8001)
