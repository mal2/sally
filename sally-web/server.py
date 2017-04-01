from flask import Flask, render_template
from geopy.geocoders import Nominatim

geolocator = Nominatim()
def resolve_location(lon, lat):
    return geolocator.reverse((lat, lon))

app = Flask(__name__)

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/compare/<longitude>/<latitude>/to/<comparison>')
def compare(longitude, latitude, comparison):
    location = resolve_location(longitude, latitude)
    return render_template('compare.html', location=location, home=comparison)

@app.route('/settings')
def settings():
    return render_template('settings.html')
