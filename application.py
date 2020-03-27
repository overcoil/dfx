#
# REST API project inspired/derived from Harvard CS50W 
#
# Inspired to write this based on fixer.io's revised API terms (March 2019)
# which removed non-EUR base currency from their free tier.
# Note: I had to add the access_key requirement since there was no work-around.
#

import requests

from flask import Flask, render_template, request

app = Flask(__name__)

# TODO: remove the following key if this source is published
GC_KEY= "fc46042aac0359752c3dad6ad9fd54e6"

# refer to https://fixer.io/documentation for details
FIXER_API_ROOT= "http://data.fixer.io/api" 
FIXER_API_LATEST = FIXER_API_ROOT + "/latest"


#
# this is the core function to retrieve and calculates the rates
# note that s & t must both be valid currency
#
def rate_core(api: str, s: str, t: str, key: str):

    if key is None:
        raise Exception("ERROR: missing access key.")

    res = requests.get(api, 
                       params={"access_key": key, "base": "EUR"} )

    if res.status_code != 200:
        raise Exception("ERROR: dependent API request to fixer.io unsuccessful.")
    data = res.json()

    # note that the 2 rates are guaranteed to exist since we have a default
    # value of EUR for both currency. If this guarantee isn't in place,
    # you will need to validate the existence of the rates!
    return rate_calculator( s, t, data["rates"][s], data["rates"][t] )


#
# this is the core function to derive the rate indirectly
#
def rate_calculator(sourceCurr: str, targetCurr: str, 
                    r1: float, r2: float):
    if sourceCurr == 'EUR':
        if targetCurr == 'EUR':
            # obviously, 1 EUR is 1 EUR
            rate = 1.0
        else:
            # we use the rate verbatim since fixer's base is EUR
            rate = r2 
    else:
        if targetCurr == 'EUR':
            # we calculate the inverse of what fixer supplies
            rate = 1.0 / r1
        else:
            # we do a bit of gymnastic ((1/r1) / (1/r2))
            rate = r2 / r1 

    # TODO: do some sig-fig trimming
    return rate



@app.route("/")
def index():
    return render_template("index.html")


#
# the latest here refer to the latest API version
# the v1 anticipates potential future changes
#
@app.route("/api/latest/historical/<string:history>", methods=["GET"])
@app.route("/api/v1/historical/<string:history>", methods=["GET"])
def historical(history: str):

    # TODO: probably a good idea to validate history conforms
    # to YYYY-MM-DD before use
    historical_api = FIXER_API_ROOT + "/" + history

    sourceCurr = request.args.get('base', default = 'EUR', type = str)
    targetCurr = request.args.get('symbols', default = 'EUR', type = str)
    accesskey = request.args.get('access_key', type = str)

    rate = rate_core(historical_api, sourceCurr, targetCurr, accesskey)
    return ( f"1 {sourceCurr} was worth {rate} {targetCurr} on {history}" )


#
# the latest here refer to the latest API version
# the v1 anticipates potential future changes
#
@app.route("/api/latest/current", methods=["GET"])
@app.route("/api/v1/current", methods=["GET"])
def latest():
    sourceCurr = request.args.get('base', default = 'EUR', type = str)
    targetCurr = request.args.get('symbols', default = 'EUR', type = str)
    accesskey = request.args.get('access_key', type = str)

    rate = rate_core(FIXER_API_LATEST, sourceCurr, targetCurr, accesskey)
    return ( f"1 {sourceCurr} is worth {rate} {targetCurr}" )


