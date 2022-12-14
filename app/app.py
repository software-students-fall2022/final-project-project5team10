# ======================================================#
#                        imports                       #
# ======================================================#

# flask
from flask import Flask, jsonify, render_template, request, redirect, flash, url_for
from werkzeug.utils import secure_filename
import requests

# mongodb
import pymongo
import time
import datetime
from bson.objectid import ObjectId
import codecs
import gridfs
from gridfs_helper import gridfs_helper_tool

# user authentication
import flask_login
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

# testing
import sys
import os
from prodict import Prodict

# allowed file types for upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


# ======================================================#
#                        setup                         #
# ======================================================#
app = Flask(__name__)
app.secret_key = os.urandom(24)

# set up flask-login for user authentication
login_manager = flask_login.LoginManager()
login_manager.init_app(app)


client = pymongo.MongoClient("mongodb://team10:EqM2PLtVjNyv3JUk@ac-i0x99nf-shard-00-00.jtrjkpd.mongodb.net:27017,ac-i0x99nf-shard-00-01.jtrjkpd.mongodb.net:27017,ac-i0x99nf-shard-00-02.jtrjkpd.mongodb.net:27017/?ssl=true&replicaSet=atlas-8i6mtc-shard-0&authSource=admin&retryWrites=true&w=majority")
db = client["PROJECT5"]

grid_fs = gridfs.GridFS(db)

# a class to represent a user


class User(flask_login.UserMixin):
    # inheriting from the UserMixin class gives this blank class default implementations of the necessary methods that flask-login requires all User objects to have
    # see some discussion of this here: https://stackoverflow.com/questions/63231163/what-is-the-usermixin-in-flask
    def __init__(self, data):
        '''
        Constructor for User objects
        @param data: a dictionary containing the user's data pulled from the database
        '''
        self.id = data['_id']  # shortcut to the _id field
        self.data = data  # all user data from the database is stored within the data field


def locate_user(user_id=None, username=None, col=db.users):
    '''
    Return a User object for the user with the given id or email address, or None if no such user exists.
    @param user_id: the user_id of the user to locate
    @param username: the username of the user to locate
    '''
    if user_id:
        # loop up by user_id
        criteria = {"_id": ObjectId(user_id)}
    else:
        # loop up by username
        criteria = {"username": username}
    doc = col.find_one(criteria)  # find a user with this username
    if doc:
        # return a user object representing this user
        user = User(doc)
        return user
    # else
    return None


def allowed_file(filename):
    '''
    check for allowed extensions
    '''
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@login_manager.user_loader
def user_loader(user_id):
    ''' 
    This function is called automatically by flask-login with every request the browser makes to the server.
    If there is an existing session, meaning the user has already logged in, then this function will return the logged-in user's data as a User object.
    @param user_id: the user_id of the user to load
    @return a User object if the user is logged-in, otherwise None
    '''
    return locate_user(user_id=user_id)  # return a User object if a user with this user_id exists


# set up any context processors
# context processors allow us to make selected variables or functions available from within all templates
@app.context_processor
def inject_user():
    # make the currently-logged-in user, if any, available to all templates as 'user'
    return dict(user=flask_login.current_user)


# ======================================================#
#                     helper functions                 #
# ======================================================#

def isfloat(num):
    '''
    function checks if a string isfloat or not 
    '''
    try:
        float(num)
        return True
    except ValueError:
        return False

def findBookCollByQuery(reqForm, col=db.books):
    # make the criteria dictionary to be passed onto the dictionary
        doc = {}
        query = reqForm['query']
        if flask_login.current_user.is_authenticated:
            doc["user_id"] = {"$ne": flask_login.current_user.id}
        else:
            doc["user_id"] = {"$ne": "542c2b97bac0595474108b51" }
        if query != "":
            doc['title'] = query
        if reqForm['edition'] != "":
            doc['edition'] = reqForm['edition']
        if reqForm['publisher'] != "":
            doc['publisher'] = reqForm['publisher']
        if reqForm['condition'] != "":
            doc['condition'] = reqForm['condition']
        
        return col.find(dict(doc))

def add_book_helper(reqForm, testing=False):
    if '' in [reqForm['ftitle'], reqForm['fpublisher'], reqForm['fedition']]:
        flash('Please fill out all fields')
        return render_template('add_book.html',
                                title=request.form['ftitle'],
                                publisher=request.form['fpublisher'],
                                edition=request.form['fedition']
                                )

    book = {}
    book["title"] = reqForm['ftitle']
    book["publisher"] = reqForm['fpublisher']
    if not testing:
        book["user_id"] = flask_login.current_user.id
    else:
        book["user_id"] = "542c2b97bac0595474108b52"
    book["edition"] = reqForm['fedition']
    book["condition"] = reqForm['fcondition']
    return book

def book_info_helper(bookid, reqMethod, coll=db.books, currUser=flask_login.current_user, testing=False):
    book = coll.find_one({"_id": ObjectId(bookid)})

    # conditional rendering: present options to edit/delete on page only if user owns the book
    is_owner = book["user_id"] == currUser.id if not testing else True

    if reqMethod == 'GET':
        return render_template('book_info.html', book=book, is_owner=is_owner)

    if reqMethod == 'POST':
        # the user requests to swap one of their books for this book
        # redirects to a list of the current users books to choose for the swap
        return redirect(url_for('choose_book', otherbookid=book["_id"]))


def edit_book_helper(bookid,col=db.books):
    book_record = col.find_one({"_id": ObjectId(bookid)})
    col.delete_one({"_id": ObjectId(bookid)})
    return book_record

def choose_book_helper(otherbookid, curr_user=flask_login.current_user, book_col=db.books, user_col=db.users, testing=False):
    user = curr_user
    myBooks = book_col.find({"user_id": user.id, 'status': 'swappable'}) if not testing else book_col.find({"user_id": user["user_id"], 'status': 'swappable'})
    otherbook = book_col.find_one({"_id": ObjectId(otherbookid)})
    otheruser = user_col.find_one({'_id': ObjectId(otherbook['user_id'])})
    return render_template('book_to_swap.html',
                           books=myBooks,
                           otherbook=otherbook,
                           swapper_name=otheruser['username'])
def display_account_helper(currUser=flask_login.current_user, col=db.books, testing=False):
    user = flask_login.current_user if not testing else currUser
    user_id = user.id if not testing else user["user_id"]
    docs_swappable = col.find(
        {
            "user_id": user_id,
            'status': 'swappable'
        }
    )

    # render the account template with the user's username and the books they have up for sale
    username = user.data["username"] if not testing else user["username"]
    return render_template("account.html",
                           username=username,
                           docs_swappable=docs_swappable)
def send_swap_helper(req, bookid, otherbookid, user, col=db.books, testing=False):
    if req.method == 'GET':
        book = col.find_one({"_id": ObjectId(bookid)})
        return render_template('send_swap.html', book=book, otherbookid=otherbookid)

    # run when user chooses to either make swap or cancel
    if req.method == 'POST':
        # the user chooses not to send the request for this book
        if 'fcancel' in req.form:
            return redirect(url_for('choose_book', otherbookid=otherbookid))
        # the user sends the request to the other user
        elif 'fsend' in req.form:
            update_book_status(bookid, 'pending', otherbookid, 'pending')
            if not testing:
                make_request(user, bookid, otherbookid)
            return redirect(url_for('home'))
            
# ======================================================#
#                     main routes                      #
# ======================================================#

@app.route('/')
def authenticate():
    # Route for the home page
    return render_template("login.html")


@app.route('/home', methods=['GET', 'POST'])
# @flask_login.login_required
def home():
    if request.method == 'POST':
        if flask_login.current_user.is_anonymous:
            return render_template("login.html")
        # make the criteria dictionary to be passed onto the dictionary
        # query = request.form['query']
        # doc = {}
        # doc["user_id"] = {"$ne": flask_login.current_user.id}
        # if query != "":
        #     doc['title'] = query
        # if request.form['edition'] != "":
        #     doc['edition'] = request.form['edition']
        # if request.form['publisher'] != "":
        #     doc['publisher'] = request.form['publisher']
        # if request.form['condition'] != "":
        #     doc['condition'] = request.form['condition']


        # books = db.books.find(dict(doc))
        books = findBookCollByQuery(request.form)

        return render_template('search_results.html', books=books)

    '''
    find all the books currently on sale by other users
    '''
    # return all the book documents from the books collection that do not have the current user's id
    # and are able to be swapped
    docs = list(db.books.find(
        {
            "user_id": {"$ne": flask_login.current_user.id},
            'status': 'swappable'
        }
    ))

    for doc in docs:
        doc['owner'] = db.users.find_one(
            {'_id': ObjectId(doc['user_id'])})['username']

    # print(doc, file=sys.stderr)
    return render_template("home.html", docs=docs)


# ======================================================#
#                   signup/register                    #
# ======================================================#


@app.route('/signupPage', methods=['GET'])
def signupPage():
    return render_template("signup.html")


# route to handle the submission of the login form
@app.route('/signup', methods=['POST'])
def signup():
    '''
    route to sign up a new user.
    '''
    # grab the data from the form submission
    username = request.form['fusername']
    password = request.form['fpassword']
    email = request.form['femail']
    if len(username) < 6 or len(password) < 6:
        return render_template('signup.html', crederror="Username or password must be at least 6 characters")
    # generate a hashed password to store - don't store the original
    hashed_password = generate_password_hash(password)

    # check if there is a space in username
    if ' ' in username:
        return render_template('signup.html', blankerror="Username or password cannot contain spaces")
    # check whether an account with this email already exists... don't allow duplicates
    if locate_user(username=username):
        # flash('An account for {} already exists.  Please log in.'.format(username))
        return render_template('signup.html', unerror="This username already exists.")

    # create a new document in the database for this new user
    # hash the password and save it to the database
    user_id = db.users.insert_one(
        {"username": username, 'email' : email, "password": hashed_password}).inserted_id
    if user_id:
        # successfully created a new user... make a nice user object
        user = User({
            "_id": user_id,
            "username": username,
            "email": email,
            "password": hashed_password,
        })
        flask_login.login_user(user)  # log in the user using flask-login
        return redirect(url_for('home'))


# route to handle the submission of the login form
@app.route('/login', methods=['POST'])
def login():
    '''
    route that logs in a registered user 
    '''
    # get username and password from form
    username = request.form['fusername']
    password = request.form['fpassword']
    # check for empty input or spaces in the username; display an error message accordingly
    if username == "" or password == "" or username.isspace():
        return render_template("login.html", message="Username or Password is incorrect")
    # load up any existing user with this email address from the database
    user = locate_user(username=username)
    # check whether the password the user entered matches the hashed password in the database
    if user and check_password_hash(user.data['password'], password):
        flask_login.login_user(user)  # log in the user using flask-login
        # flash('Welcome back, {}!'.format(user.data['email'])) # flash can be used to pass a special message to the template we are about to render
        return redirect(url_for('home'))
    return render_template("login.html", message="Username or Password is incorrect")


@app.route('/logout')
def logout():
    '''
    route to end the current user's session 
    '''
    flask_login.logout_user()
    # flash('You have been logged out.  Bye bye!') # pass a special message to the template
    return redirect(url_for('authenticate'))


# ======================================================#
#                      book CRUD                       #
# ======================================================#


@app.route('/add_book', methods=["GET", "POST"])
# @flask_login.login_required
def add_book():
    '''
    route that adds a book to the books collection with the user_id 
    field set to the current user's id 
    '''
    user = flask_login.current_user
    if user.is_anonymous:
        return render_template("login.html")
    if request.method == "GET":
        return render_template("add_book.html")

    # POST REQUEST FROM FORM
    if request.method == "POST":
        # validate input
        initbook = add_book_helper(request.form)
        # if '' in [request.form['ftitle'], request.form['fpublisher'], request.form['fedition']]:
        #     flash('Please fill out all fields')
        #     return render_template('add_book.html',
        #                            title=request.form['ftitle'],
        #                            publisher=request.form['fpublisher'],
        #                            edition=request.form['fedition']
        #                            )
        if not isinstance(initbook, dict): return initbook

        # book = {}
        # book["title"] = request.form['ftitle']
        # book["publisher"] = request.form['fpublisher']
        # book["user_id"] = user.id
        # book["edition"] = request.form['fedition']
        # book["condition"] = request.form['fcondition']

        #========end of add book helper===============#

        # get metadata from google books

        # google_api_response = requests.get( "https://www.googleapis.com/books/v1/volumes?q=" +
        #                                     book["title"] +
        #                                     "&key=AIzaSyBtBvjNsaxUyGijiKJdks4c1lVbWp_w2AE").json()  # publisher

        # # print(google_api_response,file=sys.stderr)
        # # print(google_api_response["items"][0]["volumeInfo"]["imageLinks"]["thumbnail"], file=sys.stderr)

        # response = google_api_response["items"][0]
        # # print(response, file=sys.stderr)
        # book["metadata"] = response
        # book["status"]   = 'swappable'
        # book['image_exists'] = False # a boolean to indicate whether an image has been uplaoded to form, initially set to False
        book = get_and_insert_metadata(initbook)

        #====gridfs helper======#

        gridfs_helper_tool(db, grid_fs, request.files, book, flask_login.current_user)

        # if 'file' in request.files:  # check for allowed extensions
        #     file = request.files['file']
        #     if allowed_file((file.filename)):
        #         filename = secure_filename(file.filename)
        #         user = flask_login.current_user
        #         # unique file name: user id + filename
        #         name = str(user.id) + "_" + str(filename)
        #         # upload file in chunks into the db using grid_fs
        #         id = grid_fs.put(file, filename=name)
        #         # document to be inserted into the images collection
        #         query = {
        #             "user": user.id,
        #             "book_name": book["title"],
        #             "img_id": id
        #         }
        #         # add gridfs id to the image field of the book document to be queried into the books collection
        #         book["image"] = id
        #         # get image chunks, read it, encode it, add the encoding to the "image_base64" field to be able to render it using html
        #         image = grid_fs.get(id)
        #         base64_data = codecs.encode(image.read(), 'base64')
        #         image = base64_data.decode('utf-8')
        #         book['image_base64'] = image
        #         # change the image_exists field to True once an image field is added to book document
        #         book['image_exists'] = True
        #         # add the image query into the images collection
        #         db.images.insert_one(query)
        # db.books.insert_one(book)

        #====gridfs helper======#
        return redirect(url_for('display_account'))


@app.route('/edit/<bookid>', methods=['GET'])
# @flask_login.login_required
def edit_book(bookid):
    '''
    record existing attributes of book and pass them to template
    as existing field values after removing book from db
    '''
    if flask_login.current_user.is_anonymous:
        return render_template("login.html")
    book_record=edit_book_helper(bookid)
    #============edit_book_helper============================
    # book_record = db.books.find_one({"_id": ObjectId(bookid)})
    # db.books.delete_one({"_id": ObjectId(bookid)})
    return render_template('edit_book.html', book=book_record)


@app.route('/delete/<bookid>', methods=['GET'])
# @flask_login.login_required
def delete_book(bookid):
    if flask_login.current_user.is_anonymous:
        return render_template("login.html")
    '''
    delete book from database given a book_id
    '''
    db.books.delete_one({"_id": ObjectId(bookid)})
    return redirect(url_for('display_account'))


# ======================================================#
#                     book viewing                     #
# ======================================================#

@app.route('/book_info/<bookid>', methods=['GET', 'POST'])
@flask_login.login_required
def book_info(bookid):
    if flask_login.current_user.is_anonymous:
        return render_template("login.html")
    '''
    route to show the selected book that is for sale on the home page 
    '''
    #===book info helper======
    # book = db.books.find_one({"_id": ObjectId(bookid)})

    # # conditional rendering: present options to edit/delete on page only if user owns the book
    # user = flask_login.current_user
    # is_owner = book["user_id"] == user.id

    # if request.method == 'GET':
        # return render_template('book_info.html', book=book, is_owner=is_owner)
        # return book_info_helper(bookid, request.method)

    # if request.method == 'POST':
    #     # the user requests to swap one of their books for this book
    #     # redirects to a list of the current users books to choose for the swap
        # return redirect(url_for('choose_book', otherbookid=book["_id"]))
    return book_info_helper(bookid, request.method)

    #===end book info helper======


@app.route('/book_to_swap/<otherbookid>', methods=['GET', 'POST'])
# @flask_login.login_required
def choose_book(otherbookid):
    if flask_login.current_user.is_anonymous:
        return render_template("login.html")
    '''
    route that shows all the user's books and allows them to choose one 
    to swap for the book they want (links to send_swap for the chosen book)
    @param otherbookid: id of the other user's book
    '''
    #===choose_book_helper===
    # user = flask_login.current_user
    # myBooks = db.books.find({"user_id": user.id, 'status': 'swappable'})
    # otherbook = db.books.find_one({"_id": ObjectId(otherbookid)})
    # otheruser = db.users.find_one({'_id': ObjectId(otherbook['user_id'])})
    # return render_template('book_to_swap.html',
    #                        books=myBooks,
    #                        otherbook=otherbook,
    #                        swapper_name=otheruser['username'])
    return choose_book_helper(otherbookid, curr_user=flask_login.current_user, book_col=db.books, user_col=db.users)


# ======================================================#
#                        account                       #
# ======================================================#


@app.route('/account')
# @flask_login.login_required
def display_account():
    '''
    display all the documents with the user_id field set
    to the current user's id 
    '''

    if flask_login.current_user.is_anonymous:
        return render_template("login.html")
    
    return display_account_helper()
    # user = flask_login.current_user
    # docs_swappable = db.books.find(
    #     {
    #         "user_id": user.id,
    #         'status': 'swappable'
    #     }
    # )

    # # render the account template with the user's username and the books they have up for sale
    # return render_template("account.html",
    #                        username=user.data["username"],
    #                        docs_swappable=docs_swappable)


# ======================================================#
#                     swap routes                      #
# ======================================================#

@app.route('/send_swap/<bookid>/<otherbookid>', methods=['GET', 'POST'])
# @flask_login.login_required
def send_swap(bookid, otherbookid):
    '''
    route that shows the information of the user's book they want to swap for another 
    @param bookid: id of current user's book
    @param otherbookid: id of the other user's book
    '''
    user = flask_login.current_user
    if user.is_anonymous:
        return render_template("login.html")
    return send_swap_helper(request, bookid, otherbookid, user)
    # if request.method == 'GET':
    #     book = db.books.find_one({"_id": ObjectId(bookid)})
    #     return render_template('send_swap.html', book=book, otherbookid=otherbookid)

    # # run when user chooses to either make swap or cancel
    # if request.method == 'POST':
    #     # the user chooses not to send the request for this book
    #     if 'fcancel' in request.form:
    #         return redirect(url_for('choose_book', otherbookid=otherbookid))
    #     # the user sends the request to the other user
    #     elif 'fsend' in request.form:
    #         update_book_status(bookid, 'pending', otherbookid, 'pending')
    #         make_request(user, bookid, otherbookid)
    #         return redirect(url_for('home'))

# def find_swappable_books():


# updates book statuses
# possible statuses are:
#   'swappable' - when a user lists a book on their account,
#                listed to be swapped
#   'pending'  - when two users have requested to swap,
#                but the swap has not yet been done in real life
def update_book_status(book_id_sender, status_sender, book_id_reciever, status_reciever, col=db.books):
    col.find_one_and_update(
        {
            '_id': ObjectId(book_id_sender)
        },
        {
            '$set': {'status': status_sender}
        }
    )
    col.find_one_and_update(
        {
            '_id': ObjectId(book_id_reciever)
        },
        {
            '$set': {'status': status_reciever}
        }
    )


def make_request(user, bookid, otherbookid):
    '''
    current user sends the swap request to the other user 
    @param user: the current user
    @param bookid: id of current user's book
    @param otherbookid: id of the other user's book
    '''
    otherbook = db.books.find_one({"_id": ObjectId(otherbookid)})
    otheruserid = otherbook["user_id"]
    # add request to the database (will be displayed on recievers swap requests page)
    db.requests.insert_one({
        "sender": ObjectId(user.id),      # current user
        "reciever": ObjectId(otheruserid),  # other user
        "booktoswap": ObjectId(bookid),       # book the current user has
        "bookrequested": ObjectId(otherbookid),  # book the current user wants
    })


@app.route('/swap_requests', methods=['GET', 'POST'])
# @flask_login.login_required
def view_swap_requests():
    """
    route that allows the user to see all of their recieved swap requests
    """
    user = flask_login.current_user
    if user.is_anonymous:
        return render_template("login.html")
    # requests = db.requests.find(
    #     {"reciever": ObjectId(user.id)}).sort("_id", -1)

    # create an array of swap requests
    swapreqs = req_array(user.id)

    # for req in requests:
    #     mybookid = req["bookrequested"]
    #     otherbookid = req["booktoswap"]
# 
    #     # book the current user has
    #     mybook = db.books.find_one({"_id": ObjectId(mybookid)})
    #     # book other user wants
    #     otherbook = db.books.find_one({"_id": otherbookid})
# 
    #     swapreqs.append({
    #         "mybook": mybook,
    #         "otherbook": otherbook,
    #         'otheruser': db.users.find_one({'_id': ObjectId(otherbook['user_id'])})
    #     })

    return render_template('swap_requests.html', swapreqs=swapreqs)

def req_array(userid, col=db.requests, col2=db.books, col3=db.users):
    """
    Creates an array of swap requests
    """
    requests = col.find(
        {"reciever": ObjectId(userid)}).sort("_id", -1)
    swapreqs = []
    for req in requests:
        mybookid = req["bookrequested"]
        otherbookid = req["booktoswap"]

        # book the current user has
        mybook = col2.find_one({"_id": ObjectId(mybookid)})
        # book other user wants
        otherbook = col2.find_one({"_id": otherbookid})

        swapreqs.append({
            "mybook": mybook,
            "otherbook": otherbook,
            'otheruser': col3.find_one({'_id': ObjectId(otherbook['user_id'])})
        })
    return swapreqs

# accept/decline request
@app.route('/view_swap/<mybookid>/<otherbookid>', methods=['GET', 'POST'])
# @flask_login.login_required
def view_swap(mybookid, otherbookid):
    """
    route that allows the user to view a specific swap request
    @param mybookid: id of the current user's book (that would be given from swap)
    @param otherbookid: id of the other user's book (that would be recieved from swap)
    """
    if flask_login.current_user.is_anonymous:
        return render_template("login.html")
    mybook = db.books.find_one({"_id": ObjectId(mybookid)})
    otherbook = db.books.find_one({"_id": ObjectId(otherbookid)})

    if request.method == 'GET':
        return render_template("view_swap.html",
                               mybook=mybook,
                               otherbook=otherbook,
                               otheruser=db.users.find_one(
                                   {'_id': ObjectId(otherbook['user_id'])})
                               )
    if request.method == 'POST':
        # approve swap
        if 'fapprove' in request.form:
            remove_all(mybookid, otherbookid)
            return redirect(url_for('view_swap_requests'))
        # decline swap
        if 'fdecline' in request.form:
            # remove this request from the database
            db.requests.delete_one(
                {"$and": [{"bookrequested": ObjectId(mybookid)},
                          {"booktoswap": ObjectId(otherbookid)}]}
            )
            update_book_status(mybookid, 'swappable', otherbookid, 'swappable')
            return redirect(url_for('view_swap_requests'))


def remove_all(mybookid, otherbookid, col=db.requests, col2=db.books):
    """
    removes all requests containing either of these books and removes the books from database
    @param mybookid: id of the current user's book (that would be given from swap)
    @param otherbookid: id of the other user's book (that would be recieved from swap)
    """
    # remove all requests containing either of these books
    col.delete_many({"bookrequested": ObjectId(mybookid)})
    col.delete_many({"booktoswap": ObjectId(mybookid)})
    col.delete_many({"booktoswap": ObjectId(otherbookid)})
    col.delete_many({"bookrequested": ObjectId(otherbookid)})
    # remove books from database
    col2.delete_one({"_id": ObjectId(mybookid)})
    col2.delete_one({"_id": ObjectId(otherbookid)})


def get_and_insert_metadata(bookObj):
    print(bookObj, file=sys.stderr)
    google_api_response = requests.get("https://www.googleapis.com/books/v1/volumes?q=" +
                                       bookObj["title"] +
                                       "&key=AIzaSyBtBvjNsaxUyGijiKJdks4c1lVbWp_w2AE").json()  # publisher

    # print(google_api_response,file=sys.stderr)
    # print(google_api_response["items"][0]["volumeInfo"]["imageLinks"]["thumbnail"], file=sys.stderr)

    response = google_api_response["items"][0]
    # print(response, file=sys.stderr)
    bookObj["metadata"] = response
    bookObj["status"] = 'swappable'
    # a boolean to indicate whether an image has been uplaoded to form, initially set to False
    bookObj['image_exists'] = False
    
    return bookObj


# ======================================================#
#                         run                          #
# ======================================================#
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=3000)
