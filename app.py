#!/usr/bin/env python3

import os
import sys
import subprocess
import datetime
import flask
from flask import flash

from flask import Flask, render_template, request, redirect, url_for, make_response

# import logging
import sentry_sdk
from sentry_sdk.integrations.flask import (
    FlaskIntegration,
)  # delete this if not using sentry.io

# from markupsafe import escape
import pymongo
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId
from dotenv import load_dotenv

'''
# Connect to MongoDB
client = pymongo.MongoClient("mongodb://class-mongodb.cims.nyu.edu:27017/")  
db = client["cep454"]  


# Create a new collection
collection_name = "book_reviews" 
collection = db[collection_name]
'''

#MONGO_DBNAME=cep454
#MONGO_URI=mongodb://cep454:Yt6CP6he@class-mongodb.cims.nyu.edu:27017/cep454?authSource=cep454&retryWrites=true&w=majority

#SENTRY_DSN=https://b5052ab15a33cbbf60f0a3b988ff65d4@o4507087780249600.ingest.us.sentry.io/4507087790473216 # get by registering at https://sentrio.io and configuring new flask project there
#FLASK_APP=app.py
#FLASK_ENV=development
#GITHUB_REPO=https://github.com/https://github.com/dbdesign-students-spring2024/7-web-app-carapeddle.git # unnecessary for basic operations
#GITHUB_SECRET=your_github_secret # unnecessary for basic operations

load_dotenv(override=True)  # take environment variables from .env.

# initialize Sentry for help debugging... this requires an account on sentrio.io
# you will need to set the SENTRY_DSN environment variable to the value provided by Sentry
# delete this if not using sentry.io

import sentry_sdk



sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    # enable_tracing=True,
    # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions.
    # We recommend adjusting this value in production.
    #profiles_sample_rate=1.0,
    integrations=[FlaskIntegration()],
    send_default_pii=True,
)

# instantiate the app using sentry for debugging
app = Flask(__name__)

app.secret_key = 'r4nd0mk3y11'

# # turn on debugging if in development mode
app.debug = True if os.getenv("FLASK_ENV", "development") == "development" else False

# try to connect to the database, and quit if it doesn't work
try:
    cxn = pymongo.MongoClient(os.getenv("MONGO_URI"))
    db = cxn[os.getenv("MONGO_DBNAME")]  # store a reference to the selected database

    # verify the connection works by pinging the database
    cxn.admin.command("ping")  # The ping command is cheap and does not require auth.
    print(" * Connected to MongoDB!")  # if we get here, the connection worked!
except ConnectionFailure as e:
    # catch any database errors
    # the ping command failed, so the connection is not available.
    print(" * MongoDB connection error:", e)  # debug
    sentry_sdk.capture_exception(e)  # send the error to sentry.io. delete if not using
    sys.exit(1)  # this is a catastrophic error, so no reason to continue to live


# login
import flask_login
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user

login_manager = flask_login.LoginManager()

login_manager.init_app(app)

users={}
# registration form
class RegistrationForm:
    def __init__(self):
        self.email = ''
        self.password = ''
        self.confirm_password = ''

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if request.method == 'POST':
        # Handle form submission
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if not email:
            flash('All fields are required')
            return redirect(url_for('existing_reviews'))
        if not password:
            flash( 'All fields are required')
            return redirect(url_for('existing_reviews'))
        if not confirm_password:
            flash( 'All fields are required')
            return redirect(url_for('existing_reviews'))
        
        if password != confirm_password:
            flash( 'Passwords do not match')
            return redirect(url_for('existing_reviews'))
        
        if email in users:
            return redirect(url_for('login'))
        
        # Create a new user and add to the database
        users[email] = {"email": email, "password": password, "confirm_password": confirm_password,}

        return redirect(
            url_for("login")
        )
    
    # Render the registration form template for GET requests
    return render_template('register.html', form=form)

class User(flask_login.UserMixin):
    def __init__(self, user_id):
        self.id = user_id

    # Implement required methods
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)


@login_manager.user_loader

def user_loader(email):
    if email not in users:
        return None
    
    user = User(email)
    return user



@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    if email not in users:
        return

    user = User()
    user.id = email
    return user

@app.route("/login")
def getlogin():
    
    return render_template("login.html")  


@app.route("/login", methods=["POST"])
def login():
    email = flask.request.form['email']
    password = flask.request.form['password']
    user = users.get(email)
    if user and user['password'] == password:
        user_obj = User(email)
        flask_login.login_user(user_obj)
        return flask.redirect(flask.url_for('protected'))

    flash('Login Failed')
    return redirect(url_for('existing_reviews'))


@app.route('/protected')
@flask_login.login_required
def protected():
    '''
    User login works
    '''
    flash('Logged in as: ' + flask_login.current_user.id)
    return redirect(url_for('existing_reviews'))

@app.route('/logout')
def logout():
    '''
    Defines view to clear session and log user out
    '''
    flask_login.logout_user()
    return redirect(url_for('login'))

@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized', 401



# set up basic routes


@app.route("/")
def home():
    """
    Route for the home page.
    Returns to browser the content of index.html file.
    """
    return render_template("index.html")


@app.route("/existing_reviews")
def existing_reviews():
    """
    Route for GET requests to the existing_reviews page.
    Displays some information for the user with links to other pages.
    
    """
    docs = db.book_reviews.find({}).sort("title", -1)
    # sort in order of title
        
    return render_template("existing_reviews.html", docs=docs)  # render the existing_reviews template


@app.route("/write_review")
def write():
    """
    Route for GET requests to the write_review page.
    Displays a form users can fill out to create a new document.
    """
    return render_template("write_review.html")  # render the write_review template


@app.route("/write_review", methods=["POST"])
def write_review():
    """
    Route for POST requests to the write_review page.
    Accepts the form submission data for a new document and saves the document to the database.
    """
    username = request.form["username"]
    
    title = request.form["title"]
    author = request.form["author"]
    pages = request.form["pages"] #validate this
    if pages.isnumeric() == False:
        return "Invalid page input. Pages must be non-negative integer."
    elif int(pages) < 0:
        return "Invalid page input. Pages must be non-negative integer."
    rating = request.form["rating"] #validate this
    review = request.form["review"]
    valid_ratings = ['1', '2', '3', '4', '5']  # Valid ratings
    if rating not in valid_ratings:
        return "Invalid rating input. Please select a valid rating."

    # create a new document with the data the user entered
    doc = {"username": username, "title": title, "author": author, "pages": pages, "rating": rating, "review": review, "created_at": datetime.datetime.utcnow(),}
    db.book_reviews.insert_one(doc)  # insert a new document 

    return redirect(
        url_for("existing_reviews")
    )  # tell the browser to make a request for /existing_reviews route


@app.route("/edit/<mongoid>")
def edit(mongoid):
    """
    Route for GET requests to the edit page.
    Displays a form users can fill out to edit an existing record.
    User must have published origial review to be able to edit

    Parameters:
    mongoid (str): The MongoDB ObjectId of the record to be edited.
    """
    doc = db.book_reviews.find_one({"_id": ObjectId(mongoid)})
    if doc['user_id'] != flask_login.current_user.id:
        flash('You do not have permission to edit this post.')
        return redirect(url_for('existing_reviews'))
    return render_template(
        "edit.html", mongoid=mongoid, doc=doc
    )  # render the edit template


@app.route("/edit/<mongoid>", methods=["POST"])
def edit_post(mongoid):
    """
    Route for POST requests to the edit page.
    Accepts the form submission data for the specified document and updates the document in the database.
    User must have published origial review to be able to edit
    
    Parameters:
    mongoid (str): The MongoDB ObjectId of the record to be edited.
    """
    doc = db.book_reviews.find_one({"_id": ObjectId(mongoid)})
    if doc['user_id'] != flask_login.current_user.id:
        flash('You do not have permission to edit this post.')
        return redirect(url_for('existing_reviews'))
    

    username = request.form["username"]
    title = request.form["title"]
    author = request.form["author"]
    pages = request.form["pages"] #validate this
    if pages.isnumeric() == False:
        flash("Invalid page input. Pages must be non-negative integer.")
        return redirect(url_for('existing_reviews'))
    elif int(pages) < 0:
        return "Invalid page input. Pages must be non-negative integer."
    rating = request.form["rating"] #validate this
    review = request.form["review"]
    valid_ratings = ['1', '2', '3', '4', '5']  # Valid ratings
    if rating not in valid_ratings:
        flash("Invalid page input. Pages must be non-negative integer.")
        return redirect(url_for('existing_reviews'))
    

    doc = {
        "username": username, 
        "title": title, 
        "author": author, 
        "pages": pages, 
        "rating": rating, 
        "review": review, 
        "created_at": datetime.datetime.utcnow(),
    }


    db.book_reviews.update_one(
        {"_id": ObjectId(mongoid)}, {"$set": doc}  # match criteria
    )

    flash('Post updated successfully.')
    return redirect(url_for("existing_reviews"))  # tell the browser to make a request for the /existing_reviews route


@app.route("/delete/<mongoid>")
def delete(mongoid):
    """
    Route for GET requests to the delete page.
    Deletes the specified record from the database, and then redirects the browser to the read page.

    Parameters:
    mongoid (str): The MongoDB ObjectId of the record to be deleted.
    """
    db.book_reviews.delete_one({"_id": ObjectId(mongoid)})
    return redirect(
        url_for("existing_reviews")
    )  # tell the web browser to make a request for the /existing_reviews route.


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    GitHub can be configured such that each time a push is made to a repository, GitHub will make a request to a particular web URL... this is called a webhook.
    This function is set up such that if the /webhook route is requested, Python will execute a git pull command from the command line to update this app's codebase.
    You will need to configure your own repository to have a webhook that requests this route in GitHub's settings.
    Note that this webhook does do any verification that the request is coming from GitHub... this should be added in a production environment.
    """
    # run a git pull command
    process = subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE)
    pull_output = process.communicate()[0]
    # pull_output = str(pull_output).strip() # remove whitespace
    process = subprocess.Popen(["chmod", "a+x", "flask.cgi"], stdout=subprocess.PIPE)
    chmod_output = process.communicate()[0]
    # send a success response
    response = make_response(f"output: {pull_output}", 200)
    response.mimetype = "text/plain"
    return response


@app.errorhandler(Exception)
def handle_error(e):
    """
    Output any errors - good for debugging.
    """
    return render_template("error.html", error=e)  # render the edit template


# run the app
if __name__ == "__main__":
    # logging.basicConfig(filename="./flask_error.log", level=logging.DEBUG)
    app.run(load_dotenv=True)

