import os
from flask import Flask, redirect, render_template, abort, request
from functools import wraps
from flask.ext.assets import Environment, Bundle
from flask.ext.basicauth import BasicAuth
import logging
from raven.contrib.flask import Sentry
from flask import jsonify
import forms
import string
import json
import requests
import geojson
from utils import geo

TITLES_SCHEME_DOMAIN_PORT = os.environ.get('TITLES_SCHEME_DOMAIN_PORT', os.environ.get('TITLES_1_PORT_8004_TCP', '').replace('tcp://', 'http://'))
GEO_SCHEME_DOMAIN_PORT = os.environ.get('GEO_SCHEME_DOMAIN_PORT', os.environ.get('GEO_1_PORT_8005_TCP', '').replace('tcp://', 'http://'))

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

def load_title(property_id):
    res = requests.get("%s/titles/%s" % (TITLES_SCHEME_DOMAIN_PORT, property_id))
    if res.status_code == 404:
        return None
    return res.json()
    
# Logging
@app.before_first_request
def setup_logging():
    if not app.debug:
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.INFO)

@app.route('/')
def home():
    form = forms.SearchForm()

    res = requests.get("%s/titles" % TITLES_SCHEME_DOMAIN_PORT)
    res.raise_for_status()
    return render_template('/index.html', titles=res.json()['titles'], form=form)

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

@app.route('/properties')
def properties():
    return "Request for all titles not supported", 403

@app.route('/search')
def search():

    search_term = None
    form = forms.SearchForm()
    titles = []
    latlng = False

    if 'q' in request.args:
        search_term = request.args['q']
        form.q.data = search_term

        #work out the type of search, they try and get a latlng for it
        if geo.is_postcode(search_term):
            latlng = geo.postcode_to_latlng(search_term)
        else:
            latlng = geo.geocode_place_name(search_term)

        #if we have a location, then do a search
        if latlng:

            #make a geojson point
            geojson_point = geojson.Point([latlng[1], latlng[0]], crs={"type": "name","properties": {"name": "EPSG:4326"}})

            #call the geo service
            url = "%s/titles?near=%s" % (GEO_SCHEME_DOMAIN_PORT, geojson.dumps(geojson_point))
            res = requests.get(url)
            titles = res.json()

    return render_template('/search.html', titles=titles['objects'], form=form, search_term=search_term, latlng=latlng)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8001)
