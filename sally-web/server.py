from flask import Flask, render_template
from geopy.geocoders import Nominatim
import json


geolocator = Nominatim(scheme="http")
def resolve_location(lon, lat):
    return geolocator.reverse((lat, lon))

countries = eval(open("countries.list").read())
def getCountries():
    return countries

equaldex = json.load(open("equaldex_dump.json"))

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
    return render_template('settings.html', countries=getCountries())
