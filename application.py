#
# REST API project inspired/derived from Harvard CS50W
#
# Inspired to write this based on fixer.io's revised API terms (March 2019)
# which removed non-EUR base currency from their free tier.
# Note: I had to add the access_key requirement since there was no work-around.
#
# This is a Flask-based API that serves up a full forex rate lookup.
# It relies on fixer.io's free service which offers EUR-base rates.
#
# To use this, it suffice to setup Flask as appropriate and:
#
# $ export FLASK_APP=application.py
# $ flask run
# $ curl http://127.0.0.1:5000/api/v1/current?base=CAD&symbols=USD&access_key=<yourkey>
#

import requests

from flask import Flask, render_template, request

app = Flask(__name__)


# refer to https://fixer.io/documentation for details
FIXER_API_ROOT= "http://data.fixer.io/api"
FIXER_API_LATEST = FIXER_API_ROOT + "/latest"

def sigfig(f: float, fig: int = 6):
    # there's a whole lot of ideas on truncation and rounding at:
    #   https://stackoverflow.com/questions/783897/truncating-floats-in-python
    # but none for significant figure which is required for exchange rates.
    # Most rates probably would be okay since the number is close to 1.
    # But for GBP-JPY (and similar pairing) where the rate is >100 one way,
    # the reverse rate is easily three places to the right of the decimal
    # point (e.g., 0.00742...) which leads to a significant loss of
    # precision if we naively take 6 digits to the right of the decimal point.
    # we need to do better

    # TODO: but we're lazy at this time and this is mainly to test
    # github integration inside atom...
    fstr = str(f)

    return float(fstr[:fstr.find('.') + fig + 1])


#
# this is the core function to retrieve and calculates the rates
# note that s & t must both be valid currency
#
# Param:
#   api: API endpoint to call
#   s: source currency (e.g., "CAD")
#   t: target currency (e.g., "USD")
#   key: fixer.io access key for calling API
#
# Return:
#   <float>: exchange rate from currency s to currency t (1 s = <float> t)
#
def rate_core(api: str, s: str, t: str, key: str, apiver: int=1):

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
    rate = rate_calculator( s, t, data["rates"][s], data["rates"][t] )

    if (apiver == 1):
        return rate
    else:
        # apiver == 2
        return sigfig(rate, 6)

#
# this is the core function to derive the rate indirectly
#
# This calculates the exchange rate of two arbitrary currencies based on
# knowing the rate of each of currencies to a third fixed currency (EUR).
# Understand that that the rate calculated thus is not valid/accurate for
# all uses since real-world exchange rates reflect the specific conditions
# between the source and target currency. But this calculation is reasonable
# for deriving a number that's in the ball-park.
#
# Param:
#   sourceCurr: source currency (e.g., "CAD")
#   targetCurr: target currency (e.g., "USD")
#   r1: exchange rate of EUR to sourceCurr
#   r2: exchange rate of EUR to targetCurr
#
# Return:
#   <float>: exchange rate from sourceCurr to targetCurr
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
            
    return rate

@app.route("/")
def index():
    return render_template("index.html")


#
# the latest here refer to the latest API version
# v2 adds (TODO:fake) sig-figs
#
@app.route("/api/latest/historical/<string:history>", methods=["GET"])
@app.route("/api/v2/historical/<string:history>", methods=["GET"])
def historical(history: str):

    # TODO: probably a good idea to validate history conforms
    # to YYYY-MM-DD before use
    historical_api = FIXER_API_ROOT + "/" + history

    sourceCurr = request.args.get('base', default = 'EUR', type = str)
    targetCurr = request.args.get('symbols', default = 'EUR', type = str)
    accesskey = request.args.get('access_key', type = str)

    # note that we invoke apiver=2
    trate = rate_core(historical_api, sourceCurr, targetCurr, accesskey, 2)

    return ( f"1 {sourceCurr} was worth {trate} {targetCurr} on {history}" )

# v1 does not do sig-fig truncation
@app.route("/api/v1/historical/<string:history>", methods=["GET"])
def historical_v1(history: str):

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
