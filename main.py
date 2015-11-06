"""
Flask web app connects to Mongo database.
Keep a simple list of dated memoranda.

Representation conventions for dates: 
   - In the session object, date or datetimes are represented as
   ISO format strings in UTC.  Unless otherwise specified, this
   is the format passed around internally. Note that ordering
   of ISO format strings is consistent with date/time order
   - User input/output is in local (to the server) time
   - Database representation is as MongoDB 'Date' objects
   Note that this means the database may store a date before or after
   the date specified and viewed by the user, because 'today' in
   Greenwich may not be 'today' here. 
"""

import flask
from flask import render_template
from flask import request
from flask import url_for
from flask import jsonify

import json
import logging

# Date handling 
import arrow # Replacement for datetime, based on moment.js
import datetime # But we may still need time
from dateutil import tz  # For interpreting local times

# Mongo database
from pymongo import MongoClient
from bson.objectid import ObjectId


###
# Globals
###
import CONFIG

app = flask.Flask(__name__)

try: 
    dbclient = MongoClient(CONFIG.MONGO_URL)
    db = dbclient.memos
    collection = db.dated

except:
    print("Failure opening database. Is Mongo running? Correct password?")
    sys.exit(1)

import uuid
app.secret_key = str(uuid.uuid4())

###
# Pages
###

@app.route("/")
@app.route("/index")
def index():
  app.logger.debug("Main page entry")
  flask.session['memos'] = get_memos()
  for memo in flask.session['memos']:
      app.logger.debug("Memo: " + str(memo))
  return flask.render_template('index.html')


# We don't have an interface for creating memos yet
# @app.route("/create")
# def create():
#     app.logger.debug("Create")
#     return flask.render_template('create.html')


@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    return flask.render_template('page_not_found.html',
                                 badurl=request.base_url,
                                 linkback=url_for("index")), 404

#################
#
# Functions used within the templates
#
#################

# NOT TESTED with this application; may need revision
#@app.template_filter( 'fmtdate' )
# def format_arrow_date( date ):
#     try:
#         normal = arrow.get( date )
#         return normal.to('local').format("ddd MM/DD/YYYY")
#     except:
#         return "(bad date)"

@app.template_filter( 'humanize' )
def humanize_arrow_date( date ):
    """
    Date is internal UTC ISO format string.
    Output should be "today", "yesterday", "in 5 days", etc.
    Arrow will try to humanize down to the minute, so we
    need to catch 'today' as a special case.
    """
    try:
        then = arrow.get(date).to('local')
        now = arrow.utcnow().to('local')
        if then.date() == now.date():
            human = "Today"
        else: 
            human = then.humanize(now)
            if human == "in a day":
                human = "Tomorrow"
    except: 
        human = date
    return human


#############
#
# Functions available to the page code above
#
##############
def get_memos():
    """
    Returns all memos in the database, in a form that
    can be inserted directly in the 'session' object.
    """
    records = [ ]
    for record in collection.find( { "type": "dated_memo" } ).sort("date", 1):
        record['date'] = arrow.get(record['date']).isoformat()
        try:
          record['_id'] = str(record['_id'])
        except:
          del record['_id']
        records.append(record)
    return records


def put_memo(dt, mem):
    """
    Place memo into database
    Args:
       dt: Datetime (arrow) object
       mem: Text of memo
    NOT TESTED YET
    """
    #print(dt)
    date = arrow.get(dt, 'DD/MM/YYYY').to('utc').naive
    record = { "type": "dated_memo", 
               "date": date,
               "text": mem,
            }
    collection.insert(record)
    return


@app.route("/_createMemo")
def createMemo():
  """
  Call put_memo with user input
  """
  date = request.args.get('date', 0, type=str) # pull date
  memo = request.args.get('memo', 0, type=str) # pull memo text
  put_memo(date,memo) # insert date and text into a memo via put_memo function
  return jsonify(result="add success") # must return something, so why not success?
  


@app.route('/_delete')
def python_method_for_delete():
  """
  Deletes entry by ID
  """
  print("before")
  memoID = request.args.get('objectID', 0, type=str) # pull unique identifier for each entry
  print(memoID)
  collection.remove({'_id': ObjectId(memoID)}) # remove entry by ID
  print("after after")
  return jsonify(result="delete success") # must return something, so why not success?



if __name__ == "__main__":
    # App is created above so that it will
    # exist whether this is 'main' or not
    # (e.g., if we are running in a CGI script)
    app.debug=CONFIG.DEBUG
    app.logger.setLevel(logging.DEBUG)
    # We run on localhost only if debugging,
    # otherwise accessible to world
    if CONFIG.DEBUG:
        # Reachable only from the same computer
        app.run(port=CONFIG.PORT)
    else:
        # Reachable from anywhere 
        app.run(port=CONFIG.PORT,host="0.0.0.0")
