import os
from flask import Flask, redirect, render_template, abort, request, session, url_for
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
from twilio.rest import TwilioRestClient
from pyproj import Proj, transform

TITLES_SCHEME_DOMAIN_PORT = os.environ.get('TITLES_SCHEME_DOMAIN_PORT', os.environ.get('TITLES_1_PORT_8004_TCP', '').replace('tcp://', 'http://'))
GEO_SCHEME_DOMAIN_PORT = os.environ.get('GEO_SCHEME_DOMAIN_PORT', os.environ.get('GEO_1_PORT_8005_TCP', '').replace('tcp://', 'http://'))
API_KEY_MAILGUN = os.environ.get('API_KEY_MAILGUN')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
SELLER_RECIPIENT_PHONE_NO = os.environ.get('SELLER_RECIPIENT_PHONE_NO')
BUYER_RECIPIENT_PHONE_NO = os.environ.get('BUYER_RECIPIENT_PHONE_NO')

app = Flask(__name__)
app.secret_key='dsadsadsa784932bh43nbjkfd890vd'


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
    geojson_point = False

    if 'postcode' in request.args:
        search_term = request.args['postcode']

        #work out the type of search, they try and get a latlng for it
        if geo.is_postcode(search_term):
            latlng = geo.postcode_to_latlng(search_term)

        #if we have a location, then do a search
        if latlng:
            #make a geojson point
            inProj = Proj(init='epsg:4326')
            outProj = Proj(init='epsg:3857')
            x2,y2 = transform(inProj,outProj,latlng[1],latlng[0])
        else:
            x2 = 14708.755563011973
            y2 = 6761018.225448865              
    else:
        x2 = 14708.755563011973
        y2 = 6761018.225448865

    geojson_point = json.dumps(geojson.Point([x2, y2], crs={"type": "name","properties": {"name": "EPSG:3857"}}))   
    return render_template('/map.html', postcode_centre=geojson_point, geo_url=os.environ.get('GEO_SCHEME_DOMAIN_PORT', 'http://172.16.42.43:8005'))



@app.route('/search-map-results')
def map_search_results():
    geojson_point = False
    postcode_4326 = False

    if 'place' in request.args:
        search_term = request.args['place']

        #work out the type of search, they try and get a latlng for it
        if geo.is_postcode(search_term):
            latlng = geo.postcode_to_latlng(search_term)
        else:
            latlng = geo.geocode_place_name(search_term)    

        #if we have a location, then do a search
        if latlng:
            #make a geojson point
            inProj = Proj(init='epsg:4326')
            outProj = Proj(init='epsg:3857')
            x2,y2 = transform(inProj,outProj,latlng[1],latlng[0])
            postcode_4326 = json.dumps(geojson.Point([latlng[1], latlng[0]], crs={"type": "name","properties": {"name": "EPSG:4326"}}))
        else:
            x2 = 14708.755563011973
            y2 = 6761018.225448865              
    else:
        x2 = 14708.755563011973
        y2 = 6761018.225448865

    geojson_point = json.dumps(geojson.Point([x2, y2], crs={"type": "name","properties": {"name": "EPSG:3857"}}))   
    return render_template('/map_search_results.html', postcode_centre=geojson_point, postcode_4326=postcode_4326, geo_url=os.environ.get('GEO_SCHEME_DOMAIN_PORT', 'http://172.16.42.43:8005'))



@app.route('/editextent')
def editextent():
    return render_template('edit_extent.html', geo_url=os.environ.get('GEO_SCHEME_DOMAIN_PORT', 'http://172.16.42.43:8005'))

@app.route('/authorise-solicitor')
def authorise_solicitor_start():
    return render_template('authorise_solicitor_start.html')

@app.route('/authorise-solicitor/confirm')
def authorise_solicitor_confirm():
    return render_template('authorise_solicitor_confirm.html')

@app.route('/authorise-solicitor/done')
def authorise_solicitor_done():
    print API_KEY_MAILGUN
    try:
        email = 'Enact <lrdemo@mailinator.com>'
        if session['user'] == 'buyer':
            email = 'Baldwin and Robinson Law  <lrdemo1@mailinator.com>'

        requests.post(
            "https://api.mailgun.net/v2/sandbox96c2d499b2ef4495ac3443874fd995ad.mailgun.org/messages",
            auth=("api", API_KEY_MAILGUN),
            data={"from": "LandRegistry Concept <postmaster@sandbox96c2d499b2ef4495ac3443874fd995ad.mailgun.org>",
                  "to": email,
                  "subject": "GOV.UK - new land registry authorisation",
                  "text": "\nYou have a new pending authorisation to change the land registry.\n\n Log in to GOV.UK to accept."} )
    except:
        pass

    return render_template('authorise_solicitor_done.html')

@app.route('/solicitors')
def solicitor_start():
    return render_template('solicitor_start.html')

@app.route('/solicitors/case-list')
def solicitor_case_list():
    return render_template('solicitor_case_list.html')

@app.route('/solicitors/add-client')
def solicitor_add_client():
    return render_template('solicitor_add_client.html')

@app.route('/solicitors/find-property')
def solicitor_find_property():
    return render_template('solicitor_find_property.html')

@app.route('/solicitors/confirm-client')
def solicitor_confirm_client():
    return render_template('solicitor_confirm_client.html')

def send_sms(text, number):
    if TWILIO_AUTH_TOKEN:
        # Your Account Sid and Auth Token from twilio.com/user/account
        account_sid = "AC8f255468ed1d8e298bdc390dadc0b001"
        auth_token = TWILIO_AUTH_TOKEN
        client = TwilioRestClient(account_sid, auth_token)
        message = client.sms.messages.create(body=text,
        to=number, # Recipient phone number
        from_="+441522246068") #  Twilio number
        print message.sid

@app.route('/solicitors/add-client/done')
def solicitor_add_client_done():
    return render_template('solicitor_add_client_done.html')

@app.route('/solicitors/agree-to-transact')
def solicitor_agree_to_transact():
    return render_template('solicitor_agree_to_transact.html')

@app.route('/solicitors/agree-to-transact/done')
def solicitor_agree_to_transact_done():
    return render_template('solicitor_agree_to_transact_done.html')

@app.route('/solicitors/initiate-exchange')
def solicitor_initiate_exchange():
    return render_template('solicitor_initiate_exchange.html')

@app.route('/solicitors/initiate-exchange/done')
def solicitor_initiate_exchange_done():
    send_sms("XXX Solicitors has agreed to transact with YYY Solicitors on the purchase of ZZZ", BUYER_RECIPIENT_PHONE_NO) #buyer   
    send_sms("XXX Solicitors has agreed to transact with YYY Solicitors on the sale ZZZ", SELLER_RECIPIENT_PHONE_NO) #seller
    return render_template('solicitor_initiate_exchange_done.html')

@app.route('/solicitors/define_an_area')
def solicitor_define_an_area():
    return render_template('define_an_area.html')

@app.route('/solicitors/define_an_area/conf')
def solicitor_define_an_area_conf():
    return render_template('define_an_area_conf.html')

@app.route('/solicitors/freeze_interest')
def solicitor_freeze_interest():
    return render_template('freeze_interest.html')

@app.route('/solicitors/freeze_mortgage')
def solicitor_freeze_mortgage():
    return render_template('freeze_mortgage.html')

@app.route('/solicitors/freeze_confirmation')
def solicitor_freeze_confirmation():
    return render_template('freeze_confirmation.html')

@app.route('/solicitors/freeze_receipt')
def solicitor_freeze_receipt():
    return render_template('freeze_receipt.html')

@app.route('/solicitors/transfer_title')
def solicitor_transfer_title():
    return render_template('transfer_title.html')

@app.route('/solicitors/transfer_property')
def solicitor_transfer_property():
    return render_template('transfer_property.html')

@app.route('/solicitors/transfer_provisions')
def solicitor_transfer_provisions():
    return render_template('transfer_provisions.html')

@app.route('/solicitors/transfer_mortgage')
def solicitor_transfer_mortgage():
    return render_template('transfer_mortgage.html')

@app.route('/solicitors/transfer_confirmation')
def solicitor_transfer_confirmation():
    return render_template('transfer_confirmation.html')

@app.route('/solicitors/transfer_receipt')
def solicitor_transfer_receipt():
    return render_template('transfer_receipt.html')


@app.route('/team-leader/casework-status') #route to a team leader's casework status control view.
def team_leader_casework_status():
    return render_template('casework_status.html')

@app.route('/caseworker/worklist') # route to a caseworker's worklist view
def caseworker_worklist():
    return render_template('worklist.html')

@app.route('/caseworker/case') #route to a caseworker's individual case view
def caseworker_case():
    return render_template('caseworker_case.html')


@app.route('/signin', methods=['GET', 'POST'])
def sign_in():

    # logout whoever is logged in
    session.pop('user', None)

    if request.method == 'POST':
        session['user'] = request.form['user']

        if 'solicitor' in session['user']:
            return redirect(url_for('solicitor_case_list'))
        else:
            return redirect(url_for('authorise_solicitor_confirm'))

    return render_template('sign-in.html')


@app.route('/lasso') #route to a caseworker's individual case view
def lasso():
    return render_template('lasso.html')

@app.route('/map-lasso-search')
def map_lasso_search():
    return render_template('/map_lasso_search.html', geo_url=os.environ.get('GEO_SCHEME_DOMAIN_PORT', 'http://172.16.42.43:8005'))

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8001)
