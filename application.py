import os
import re
from flask import Flask, jsonify, render_template, request

from cs50 import SQL
from helpers import lookup

# Configure application
app = Flask(__name__)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///mashup.db")

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    """Render map"""
    return render_template("index.html")


@app.route("/articles")
def articles():
    """Look up articles for geo"""

    # Store the 'geo' part of the URL as a string called 'geo'. Check 'geo' loaded, and produce runtime error if not.
    # e.g. '12589'
    geo = request.args.get("geo")
    if not geo:
        raise RuntimeError("missing geo")

    # Run 'geo' through 'lookup()' function, store resulting list of objects in 'rows'.
    # e.g. [{'link':'www.website1.com','title':'article_title1'},{'link':'www.website2.com','title':'article_title2'}]
    rows = lookup(geo)

    # Run 'rows' through 'jsonify()'' function, and return resulting dictionary w/ up to 5 objects. The 'jsonify()' function modifies the input to JSON.
    # e.g. [{'link':'www.website1.com','title':'article_title1'},{'link':'www.website2.com','title':'article_title2'}]
    if len(rows) > 5:
        return jsonify(rows[0], rows[1], rows[2], rows[3], rows[4])
    else:
        return jsonify(rows)


###THIS IS WORKING OK BUT IT NEEDS TO BE ABLE TO HANDLE MORE VARIATIONS OF INPUT###
@app.route("/search")
def search():
    """Search for places that match query"""

    # Store the 'q' part of the URL as a string called 'q'. Check 'q' loaded, and produce runtime error if not.
    # e.g. '12589'
    q = request.args.get("q")
    if not q:
        raise RuntimeError("missing location")

    # Rewrites user input as lowercase
    q = str.lower(q)

    # Select the entire row from database 'places' that at least contains the value of 'q' in one of the 'postal_code', 'place_name', or 'admin_name1' fields.
    # e.g. [{'country_code':'US','postal_code':'12589'}]
    q_info = db.execute("SELECT * FROM places WHERE postal_code LIKE :q OR LOWER(place_name) LIKE :q OR LOWER(admin_name1) LIKE :q LIMIT 10", q='%'+q+'%')

    # Run 'q_info' dict through 'jsonify()' function to convert some elements to JSON compatible(?)
    return jsonify(q_info)


@app.route("/update")
def update():
    """Find up to 10 places within view"""

    # Ensure parameters are present
    if not request.args.get("sw"):
        raise RuntimeError("missing sw")
    if not request.args.get("ne"):
        raise RuntimeError("missing ne")

    # Ensure parameters are in lat,lng format
    if not re.search("^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$", request.args.get("sw")):
        raise RuntimeError("invalid sw")
    if not re.search("^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$", request.args.get("ne")):
        raise RuntimeError("invalid ne")

    # Explode southwest corner into two variables
    sw_lat, sw_lng = map(float, request.args.get("sw").split(","))

    # Explode northeast corner into two variables
    ne_lat, ne_lng = map(float, request.args.get("ne").split(","))

    # Find 10 cities within view, pseudorandomly chosen if more within view
    if sw_lng <= ne_lng:

        # Doesn't cross the antimeridian
        rows = db.execute("""SELECT * FROM places
                          WHERE :sw_lat <= latitude AND latitude <= :ne_lat AND (:sw_lng <= longitude AND longitude <= :ne_lng)
                          GROUP BY country_code, place_name, admin_code1
                          ORDER BY RANDOM()
                          LIMIT 10""",
                          sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)

    else:

        # Crosses the antimeridian
        rows = db.execute("""SELECT * FROM places
                          WHERE :sw_lat <= latitude AND latitude <= :ne_lat AND (:sw_lng <= longitude OR longitude <= :ne_lng)
                          GROUP BY country_code, place_name, admin_code1
                          ORDER BY RANDOM()
                          LIMIT 10""",
                          sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)

    # Output places as JSON
    return jsonify(rows)
