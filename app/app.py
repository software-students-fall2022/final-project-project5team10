from flask import Flask, jsonify, render_template, request, redirect, flash, url_for
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, send, join_room, leave_room 

import pymongo
import time
import datetime
from bson.objectid import ObjectId
import sys, os

# modules useful for user authentication
import flask_login
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

################## setup ##################
app = Flask(__name__)
app.secret_key = os.urandom(24)

################## flask_socketio setup ##################
socketio = SocketIO(app, cors_allowed_origins="*")
ROOMS = ['lounge','news','games','coding']

# set up flask-login for user authentication
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

################## routes ##################

client = pymongo.MongoClient(host='db', port=27017)
db = client["project5"]

# a class to represent a user
class User(flask_login.UserMixin):
    # inheriting from the UserMixin class gives this blank class default implementations of the necessary methods that flask-login requires all User objects to have
    # see some discussion of this here: https://stackoverflow.com/questions/63231163/what-is-the-usermixin-in-flask
    def __init__(self, data):
        '''
        Constructor for User objects
        @param data: a dictionary containing the user's data pulled from the database
        '''
        self.id = data['_id'] # shortcut to the _id field
        self.data = data # all user data from the database is stored within the data field

def locate_user(user_id=None, username=None):
    '''
    Return a User object for the user with the given id or email address, or None if no such user exists.
    @param user_id: the user_id of the user to locate
    @param username: the username of the user to locate
    '''
    if user_id:
        # loop up by user_id
        criteria = {"_id": ObjectId(user_id)}
    else:
        # loop up by email
        criteria = {"username": username}
    doc = db.users.find_one(criteria) # find a user with this username
    if doc: 
                # return a user object representing this user
        user = User(doc)
        return user
    # else
    return None
    

    

@login_manager.user_loader
def user_loader(user_id):
    ''' 
    This function is called automatically by flask-login with every request the browser makes to the server.
    If there is an existing session, meaning the user has already logged in, then this function will return the logged-in user's data as a User object.
    @param user_id: the user_id of the user to load
    @return a User object if the user is logged-in, otherwise None
    '''
    return locate_user(user_id=user_id) # return a User object if a user with this user_id exists


# set up any context processors
# context processors allow us to make selected variables or functions available from within all templates

@app.context_processor
def inject_user():
    # make the currently-logged-in user, if any, available to all templates as 'user'
    return dict(user=flask_login.current_user)

################## routes ##################
# set up the routes
@app.route('/')
def authenticate():
    #Route for the home page
    return render_template("login.html", message = "Please login or sign up!", rooms = ROOMS)

@app.route('/home')
@flask_login.login_required
def home():
    docs = db.books.find({"user_id":{"$ne": flask_login.current_user.id}})
    return render_template("home.html", docs=docs)

# route to handle the submission of the login form
@app.route('/signup', methods=['POST'])
def signup():
    # grab the data from the form submission
    username = request.form['fusername']
    password = request.form['fpassword']
    if username == "" or password == "" or username.isspace():
        return render_template("login.html", message = "Invalid username or password")
    hashed_password = generate_password_hash(password) # generate a hashed password to store - don't store the original
    
    # check whether an account with this email already exists... don't allow duplicates
    if locate_user(username = username):
        # flash('An account for {} already exists.  Please log in.'.format(username))
        return render_template("login.html", message = "This username already exists.")

    # create a new document in the database for this new user
    user_id = db.users.insert_one({"username": username, "password": hashed_password}).inserted_id # hash the password and save it to the database
    if user_id:
        # successfully created a new user... make a nice user object
        user = User({
            "_id": user_id,     
            "username": username,
            "password": hashed_password,
        })
        flask_login.login_user(user) # log in the user using flask-login
        # flash('Thanks for joining, {}!'.format(user.data['username'])) # flash can be used to pass a special message to the template we are about to render
        return redirect(url_for('home'))
    # else
    return 'Signup failed'

# route to handle the submission of the login form
@app.route('/login', methods=['POST'])
def login():
    username = request.form['fusername']
    password = request.form['fpassword']
    if username == "" or password == "" or username.isspace():
        return render_template("login.html", message = "Invalid username or password")
    user = locate_user(username=username) # load up any existing user with this email address from the database
    # check whether the password the user entered matches the hashed password in the database
    if user and check_password_hash(user.data['password'], password):
        flask_login.login_user(user) # log in the user using flask-login
        # flash('Welcome back, {}!'.format(user.data['email'])) # flash can be used to pass a special message to the template we are about to render
        return redirect(url_for('home'))
    
    return render_template("login.html", message = "Incorrect Username or Password or Account Does Not Exist.")

# route to logout a user
@app.route('/logout')
def logout():
    flask_login.logout_user()
    # flash('You have been logged out.  Bye bye!') # pass a special message to the template
    return redirect(url_for('authenticate'))

@app.route('/add_book', methods=["GET", "POST"])
@flask_login.login_required
def add_book():
    user =flask_login.current_user
    if request.method == "GET":
        return render_template("add_book.html")
    
    # POST REQUEST FROM FORM 
    if request.method == "POST":
        book = {}
        book["title"] = request.form['ftitle']
        book["publisher"] = request.form['fpublisher']
        book["user_id"] =user.id
        book["edition"] = request.form['fedition']
        book["conditon"] = request.form['fcondition']
        book["price"] = float(request.form['fprice'])

        db.books.insert_one(book)
        return redirect(url_for('display_account'))

###------------------- live chat between users ---------------------------###
@app.route('/chat', methods = ["GET","POST"])
# @flask_login.login_required
# @socketio.on('view-chat')
def chat():
    #pass along username
    return render_template('chat.html', username = flask_login.current_user)

@socketio.on('message')
def message(data):
    # print(f"\n\n{data}\n\n")
    timestamp = time.strftime('%b-%d %I:%M%p', time.localtime())
    # room=data["room"]
    send({'msg': data['msg'], 'username': data['username'], 'timestamp':timestamp})

# @socketio.on('join')
# def join(data):
#     join_room(data['room'])
#     send({'msg': data['username']+" has joined the "+ data['room'] + " room."},
#     room=data['room'])

# @socketio.on('leave')
# def leave(data):
#     leave_room(data['room'])
#     send({'msg': data['username']+" has left the "+ data['room'] + " room."},
#     room=data['room'])

#---------------------------------------------------------------------------#
@app.route('/account')
@flask_login.login_required
def display_account():
    user =flask_login.current_user
    docs = db.books.find({"user_id": user.id})
    print(user.id, file=sys.stderr)
    print(docs, file=sys.stderr)

    return render_template("account.html", username=user.data["username"], docs=docs)

#----------------swap routes----------------#

@app.route('/searchresults',methods=['GET','POST'])
def show_books():
    user =flask_login.current_user
    books = db.books.find({"user_id": {"$ne": user.id}})
    return render_template('/searchresults.html',books=books)

@app.route('/book_for_sale<bookid>', methods=['GET','POST'])
def for_sale(bookid):
    print(bookid)
    book = db.books.find_one({"_id":ObjectId(bookid)})
    if request.method== 'GET':
        return render_template('book_for_sale.html',book=book)
    else:
        #bookid = book["_id"]
        return redirect(url_for('choose_book',otherbookid=book["_id"]))

@app.route('/book_to_swap/<otherbookid>', methods=['GET','POST'])
def choose_book(otherbookid):
    user =flask_login.current_user
    myBooks = db.books.find({"user_id": user.id})
    otherbook = db.books.find_one({"_id": ObjectId(otherbookid)})
    return render_template('book_to_swap.html', books=myBooks, otherbook=otherbook)

@app.route('/send_swap/<bookid>/<otherbookid>', methods=['GET','POST'])
def send_swap(bookid,otherbookid):
    user = flask_login.current_user
    if request.method == 'GET':
        myBooks = db.books.find({"user_id": user.id})
        for book in myBooks:
            if ObjectId(book["_id"]) == ObjectId(bookid):
                return render_template('send_swap.html',book=book,otherbookid=otherbookid)
        return render_template('send_swap.html')
    else:
        if 'fcancel' in request.form:
            #otherid = request.form.get('otherid')
            return redirect(url_for('choose_book',otherbookid=otherbookid))
        elif 'frequest' in request.form:
            # send the request to the other user
            otherbook = db.books.find_one({"_id": ObjectId(otherbookid)})
            otheruserid = otherbook["user_id"]
            username = db.users.find_one({"user_id": otheruserid})
            #reciever = locate_user(username=username) # get username from prev page
            db.requests.insert_one({"sender": ObjectId(user.id), "reciever": ObjectId(otheruserid), "booktoswap": ObjectId(bookid), "bookrequested": ObjectId(otherbookid)})
            return redirect(url_for('chat'))

################## run server ##################
if __name__=='__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    # app.run(host='0.0.0.0',debug=True, port=3000)