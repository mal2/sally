from flask import Flask, render_template, redirect, url_for
from geopy.geocoders import Nominatim
from collections import defaultdict
import json
import csv

geolocator = Nominatim(scheme="http")
def resolve_location(lon, lat):
    return geolocator.reverse((lat, lon))

countries = eval(open("countries.list").read())
def getCountries():
    return countries

equaldex = json.load(open("equaldex_dump.json"))
equaldex = {k.upper():v for k, v in equaldex.items()}

sentiment = dict([['Banned (indefinite deferral)', -1], ['Illegal (imprisonment as punishment)', -1], ['Foreign same-sex marriages recognized only', 0], ['Banned (5-year deferral)', -1], ['ambiguous', -1], ["Don't Ask, Don't Tell", -1], ['Married couples only', 0], ['Equal', 0], ['Unequal', -1], ['Legal, but requires surgery', -1], ['Unregistered cohabitation', 0], ['Unrecognized, same-sex marriage and civil unions banned', -1], ['Not banned', 0], ['Sexual orientation only', 1], ['na', 0], ['Illegal (death penalty as punishment)', -1], ['Legal, surgery not required', 1], ['Legal', 1], ['Other type of partnership', 0], ['Lesbians, gays, bisexuals permitted, transgender people banned', -1], ['Banned (6-month deferral)', -1], ['Illegal (up to life in prison as punishment)', -1], ['varies', -1], ['Single only', -1], ['Illegal', -1], ['Civil unions', 1], ['Banned', -1], ['Not legal', -1], ['Male illegal, female uncertain', -1], ['No protections', -1], ['Unrecognized', -1], ['Illegal (other penalty)', -1], ['Step-child adoption only', 0], ['Male illegal, female legal', -1], ['Illegal in some contexts', -1], ['Sexual orientation and gender identity', 1], ['Banned (1-year deferral)', -1]])
us_states = {item["State"]:item["abbr"] for item in csv.DictReader(open("us-states.csv"), delimiter=";")}
print(us_states)


def judge_class(s):
    sent = sentiment.get(s, 0)
    if sent == -1:
        return "bad"
    elif sent == 1:
        return "good"
    else:
        return "neutral"

def stateAwareLocation(location):
    if location.raw["address"]["country_code"] == "us":
        return "us-" + us_states[location.raw["address"]["state"]]
    return location.raw["address"]["country_code"]

app = Flask(__name__)

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/compare/<longitude>/<latitude>/to/<comparison>')
def compare(longitude, latitude, comparison):
    location = resolve_location(longitude, latitude)
    right_location = stateAwareLocation(location)
    return redirect(url_for('compare_lr', left=comparison, right=right_location.upper()))



@app.route('/compare/<left>/to/<right>')
def compare_lr(left, right):
    left_data=equaldex.get(left.upper(), None)
    right_data=equaldex.get(right.upper(), None)
    differences = []
    if left_data and right_data:
      for key in left_data:
        if (left_data[key]["current_status"]["value"] != right_data[key]["current_status"]["value"]):
          differences.append(key)
    print(differences)
    return render_template('compare_lr.html',
                           judge_class=judge_class,
                           left=left,
                           right=right,
                           left_data=equaldex.get(left.upper(), None),
                           right_data=equaldex.get(right.upper(), None),
                           differences=differences,
                           categories=[["important", ["homosexuality",
                                                      "marriage"]],
                                        ["secondary", [
                                            "changing-gender",
                                            "adoption",
                                            "discrimination",
                                            "housing-discrimination",
                                            "employment-discrimination",
                                            "military",
                                            "blood",
                                            "age-of-consent",
                                            "conversion-therapy"]
                                        ]],)

@app.route('/settings')
def settings():
    return render_template('settings.html', countries=getCountries())
