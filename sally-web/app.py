# encoding=utf8  
import sys  

reload(sys)  
sys.setdefaultencoding('utf8')

from flask import Flask, render_template, redirect, url_for, request
from geopy.geocoders import Nominatim
from collections import defaultdict
import json
import csv
import dataset

geolocator = Nominatim(scheme="http")
def resolve_location(lon, lat):
    return geolocator.reverse((lat, lon))

countries = sorted(eval(open("countries.list").read()), key=lambda x: x[1])
def getCountries():
    return countries

equaldex = json.load(open("equaldex_dump.json"))
equaldex = {k.lower():v for k, v in equaldex.items()}


us_states = {item["State"]:item["abbr"] for item in csv.DictReader(open("us-states.csv"), delimiter=";")}

sentiment = {'adoption': {'Illegal':-1,
 'Legal':1,
 'Married couples only':0,
 'Single only':0,
 'Step-child adoption only':0,
 'ambiguous':0,
 'na':0,
 'varies':0},
'age-of-consent': {'Equal':1, 'Unequal':-1, 'ambiguous':0, 'na':0, 'varies':0},
'blood': {'Banned (1-year deferral)':-1,
 'Banned (5-year deferral)':-1,
 'Banned (6-month deferral)':-1,
 'Banned (indefinite deferral)':-1,
 'Legal':1,
 'ambiguous':0,
 'na':0},
'changing-gender': {'Illegal':-1,
 'Legal, but requires surgery':-1,
 'Legal, surgery not required':1,
 'ambiguous':0,
 'na':0,
 'varies':0},
'conversion-therapy': {'Banned':1, 'Not banned':-1, 'ambiguous':0, 'na':0, 'varies':0},
'discrimination': {'Illegal':1,
 'Illegal in some contexts':0,
 'No protections':-1,
 'na':-1},
'employment-discrimination': {'No protections':-1,
 'Sexual orientation and gender identity':1,
 'Sexual orientation only':0,
 'ambiguous':0,
 'na':0,
 'varies':0},
'homosexuality': {'Illegal (death penalty as punishment)':-1,
 'Illegal (imprisonment as punishment)':-1,
 'Illegal (other penalty)':-1,
 'Illegal (up to life in prison as punishment)':-1,
 'Legal':1,
 'Male illegal, female legal':-1,
 'Male illegal, female uncertain':-1,
 'ambiguous':0,
 'na':0,
 'varies':0},
'housing-discrimination': {'No protections':-1,
 'Sexual orientation and gender identity':1,
 'Sexual orientation only':0,
 'ambiguous':0,
 'na':0,
 'varies':0},
'marriage': {'Civil unions':0,
 'Foreign same-sex marriages recognized only':0,
 'Legal':1,
 'Not legal':-1,
 'Other type of partnership':0,
 'Unrecognized':-1,
 'Unrecognized, same-sex marriage and civil unions banned':-1,
 'Unregistered cohabitation':0,
 'ambiguous':0,
 'na':0,
 'varies':0},
'military': {"Don't Ask, Don't Tell":-1,
 'Illegal':-1,
 'Legal':1,
 'Lesbians, gays, bisexuals permitted, transgender people banned':-1,
 'ambiguous':0,
 'na':0}}


def judge_class(s, cat):
    sent = sentiment[cat].get(s, 0)
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

def retCountryCode(code):
    if code.lower().startswith("US-"):
        return geolocator.geocode({"country": "US", "state": code[-2:].lower()})
    else:
        return geolocator.geocode({"country": code})

app = Flask(__name__)

@app.route('/')
def welcome():
    return render_template('welcome.html')

def get_db():
    return dataset.connect('sqlite:///mydatabase.db')

@app.route('/vote', methods=["POST"])
def vote():
    db = get_db()
    db["votes"].insert(request.form)
    return "success"


@app.route('/compare/<longitude>/<latitude>/to/<comparison>')
def compare(longitude, latitude, comparison):
    location = resolve_location(longitude, latitude)
    right_location = stateAwareLocation(location)
    return redirect(url_for('compare_lr', left=comparison.lower(), right=right_location.lower()))

def compute_votes_ratio(country_code):
    db = get_db()
    votes = list(db.query('SELECT COUNT(*) as cnt, SUM(CASE WHEN response = \'yes\' THEN 1 ELSE 0 END) as yes, SUM(CASE WHEN response = \'no\' THEN 1 ELSE 0 END) as no FROM votes WHERE lower(country_code) = \'%s\' ' % country_code))[0]
    if not votes["yes"]:
        return dict(ratio=0, count=0)
    return dict(ratio=int(votes["yes"]*100/votes["cnt"]), count=votes["cnt"])

@app.route('/compare/<left>/to/<right>')
def compare_lr(left, right):
    left_data=equaldex.get(left.lower(), None)
    right_data=equaldex.get(right.lower(), None)
    differences = []
    if left_data and right_data:
      for key in left_data:
        if (left_data[key]["current_status"]["value"] != right_data[key]["current_status"]["value"]):
          differences.append(key)

    return render_template('compare_lr.html',
                           judge_class=judge_class,
                           left=left,
                           left_label=retCountryCode(left),
                           right=right,
                           right_label=retCountryCode(right),
                           left_data=equaldex.get(left.lower(), None),
                           right_data=equaldex.get(right.lower(), None),
                           differences=differences,
                           votes_left=compute_votes_ratio(left.lower()),
                           votes_right=compute_votes_ratio(right.lower()),
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
db = get_db()
db["votes"].insert({"response": "yes", "country_code": "doesnmtaterr"})

if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)