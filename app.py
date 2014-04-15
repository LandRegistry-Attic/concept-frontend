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
# govuk_template asset path
@app.context_processor
def asset_path_context_processor():
    return {'asset_path': '/static/govuk_template/'}

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
    return render_template('/index.html', form=form)

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

            #call the geo service -
            url = "%s/titles?near=%s" % (GEO_SCHEME_DOMAIN_PORT, geojson.dumps(geojson_point))
            res = requests.get(url)
            titles = res.json()['objects']

            for title in titles:
                title['address'] = title['address'].replace(',', ',<br>').replace('(', '<br>').replace(')', '')

    return render_template('/search.html', titles=titles, form=form, search_term=search_term, latlng=latlng, q=request.args.get('q'))

@app.route('/map')
def map():
    return render_template('map.html', geo_url=os.environ.get('GEO_SCHEME_DOMAIN_PORT', 'http://172.16.42.43:8005'))

@app.route('/editextent')
def editextent():
    return render_template('edit_extent.html', geo_url=os.environ.get('GEO_SCHEME_DOMAIN_PORT', 'http://172.16.42.43:8005'))

@app.route('/sell/find-property')
def sell_find_property():
    return render_template('sell_find_property.html')

@app.route('/sell/ida')
def sell_ida():
    return render_template('sell_ida.html')

@app.route('/sell/done')
def sell_done():
    return render_template('sell_done.html')
   
@app.route('/sell/enter-details')
def sell_enter_details():
    return render_template('sell_enter_details.html')

@app.route('/buy/enter-details')
def buy_enter_details():
    return render_template('buy_enter_details.html')

@app.route('/buy/done')
def buy_done():
    return render_template('buy_done.html')

@app.route('/conveyance-sale/task-list')
def conveyance_sale():
    return render_template('sell_solicitor_todo_list.html')

@app.route('/conveyance-sale/agree-to-transact')
def conveyance_agree_transact():
    return render_template('sell_solicitor_agree.html')

@app.route('/conveyance-sale/complete')
def conveyance_sale_complete():
    return render_template('sell_solicitor_complete.html')

@app.route('/authorise-solicitor/start')
def authorise_solicitor_start():
    return render_template('authorise_solicitor_start.html')

@app.route('/authorise-solicitor/confirm')
def authorise_solicitor_confirm():
    return render_template('authorise_solicitor_confirm.html')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8001)
