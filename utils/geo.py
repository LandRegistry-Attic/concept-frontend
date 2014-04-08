import json
import urllib
import re

def postcode_to_latlng(postcode):
	try:
		response_text = urllib.urlopen('http://mapit.mysociety.org/postcode/%s' % postcode).read()
		data = json.loads(response_text)
		return [data['wgs84_lat'], data['wgs84_lon']]
	except Exception, e:
		return False

def geocode_place_name(place_name):
	try:
		response_text = urllib.urlopen('http://api.geonames.org/searchJSON?featureClass=P&featureCode=PPL&countryBias=GB&continentCode=EU&q=%s&username=jobsort2 ' % urllib.quote(place_name)).read()
		data =  json.loads(response_text)
		return [float(data['geonames'][0]['lat']), float(data['geonames'][0]['lng'])]
	except Exception, e:
		return False

def nearby_place(lat, lng):
	try:
		response_text = urllib.urlopen('http://api.geonames.org/findNearbyPlaceNameJSON?lat=%s&lng=%s&username=jobsort2 ' % (lat, lng)).read()
		data =  json.loads(response_text)
		return {'name': data['geonames'][0]['name'], 'lat': float(data['geonames'][0]['lat']), 'lng': float(data['geonames'][0]['lng'])}
	except Exception, e:
		return False

def is_postcode(postcode):

		#See http://www.govtalk.gov.uk/gdsc/html/noframes/PostCode-2-1-Release.htm

		in_ = 'ABDEFGHJLNPQRSTUWXYZ';
		fst = 'ABCDEFGHIJKLMNOPRSTUWYZ';
		sec = 'ABCDEFGHJKLMNOPQRSTUVWXY';
		thd = 'ABCDEFGHJKSTUW';
		fth = 'ABEHMNPRVWXY';
		num = '0123456789';
		nom = '0123456789';
		gap = '\s\.';

		if re.findall("^[%s][%s][%s]*[%s][%s][%s]$" % (fst, num, gap, nom, in_, in_), postcode, re.IGNORECASE):
			return True
		elif re.findall("^[%s][%s][%s][%s]*[%s][%s][%s]$" % (fst, num, num, gap, nom, in_, in_), postcode, re.IGNORECASE):
			return True
		elif re.findall("^[%s][%s][%s][%s]*[%s][%s][%s]$" % (fst, sec, num, gap, nom, in_, in_), postcode, re.IGNORECASE):
			return True
		elif re.findall("^[%s][%s][%s][%s][%s]*[%s][%s][%s]$" % (fst, sec, num, num, gap, nom, in_, in_), postcode, re.IGNORECASE):
			return True
		elif re.findall("^[%s][%s][%s][%s]*[%s][%s][%s]$" % (fst, num, thd, gap, nom, in_, in_), postcode, re.IGNORECASE):
			return True
		elif re.findall("^[%s][%s][%s][%s][%s]*[%s][%s][%s]$" % (fst, sec, num, fth, gap, nom, in_, in_), postcode, re.IGNORECASE):
			return True
		else:
			return False
