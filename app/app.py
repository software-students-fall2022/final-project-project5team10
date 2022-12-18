
from flask import Flask, jsonify, render_template, request, redirect, flash, url_for
from werkzeug.utils import secure_filename

import pymongo
import datetime
from bson.objectid import ObjectId
import sys, os
import codecs
import gridfs

# modules useful for user authentication
import flask_login
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

# Allowed file types for upload 
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

################## setup ##################
app = Flask(__name__)
app.secret_key = os.urandom(24)

# set up flask-login for user authentication
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

################## routes ##################

client = pymongo.MongoClient(host='db', port=27017)
db = client["project5"]

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
        # loop up by username
        criteria = {"username": username}
    doc = db.users.find_one(criteria) # find a user with this username
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
    #Route for the login page
    return render_template("login.html", message = "Please login or sign up!")

@app.route('/home', methods=['GET','POST'])
@flask_login.login_required
def home():
    if request.method == 'POST':
        query = request.form['query']

        books = db.books.find({'title' : query})

        return render_template('search_results.html', books=books)

    '''
    find all the books currently on sale by other users
    '''
    docs = db.books.find({"user_id":{"$ne": flask_login.current_user.id}}) # return all the book documents from the books collection that do not have the current user's id 
    return render_template("home.html", docs=docs) # render the home template with those documents

# route to handle the submission of the login form
@app.route('/signup', methods=['POST'])
def signup():
    '''
    route to sign up a new user.
    '''
    # grab the data from the form submission
    username = request.form['fusername']
    password = request.form['fpassword']
    if username == "" or password == "" or username.isspace(): # check if the user entered nothing for the username or email and display an input error message accordingly 
        return render_template("login.html", message = "Invalid username or password")
    hashed_password = generate_password_hash(password) # generate a hashed password to store - don't store the original
    
    # check whether an account with this username already exists... don't allow duplicates
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
        return redirect(url_for('home'))
    return 'Signup failed'

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
    '''
    route to end the current user's session 
    '''
    flask_login.logout_user()
    # flash('You have been logged out.  Bye bye!') # pass a special message to the template
    return redirect(url_for('authenticate'))

@app.route('/add_book', methods=["GET", "POST"])
@flask_login.login_required
def add_book():
    '''
    route that adds a book to the books collection with the user_id 
    field set to the current user's id 
    '''
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

        # use gridfs to save uploaded image to database 

        # if file is not in requests, add book into the books collection and 
        # render account page 
        if 'file' not in request.files:
            db.books.insert_one(book)
            return redirect(url_for('display_account'))

        # get uploaded file 
        file = request.files['file']

        if file and allowed_file((file.filename)): # check for allowed extensions
            filename = secure_filename(file.filename)
            user = flask_login.current_user
            name = str(user.id) +"_" + str(filename) # unique file name: user id + filename
            id = grid_fs.put(file, filename = name) # upload file in chunks into the db using grid_fs
            # document to be inserted into the images collection 
            query = {
                "user": user.id, 
                "book_name": book["title"],
                "img_id": id
            }
            book["image"] = id # add gridfs id to the image field of the book document to be queried into the books collection
            # get image chunks, read it, encode it, add the encoding to the "image_base64" field to be able to render it using html 
            image = grid_fs.get(id)
            base64_data = codecs.encode(image.read(), 'base64')
            image = base64_data.decode('utf-8')
            book['image_base64'] = image 
            db.images.insert_one(query) # add the image query into the images collection 
        db.books.insert_one(book)
        return redirect(url_for('display_account'))

@app.route('/view_chat')
@flask_login.login_required
def view_chat():
    '''
    TODO: to be implemented 
    '''
    pass

@app.route('/account')
@flask_login.login_required
def display_account():
    '''
    display all the documents with the user_id field set
    to the current user's id 
    '''
    user =flask_login.current_user
    docs = db.books.find({"user_id": user.id})
    # render the account template with the user's username and the books they have up for sale
    return render_template("account.html", username=user.data["username"], docs=docs)



#----------------swap routes----------------#

@app.route('/book_for_sale<bookid>', methods=['GET','POST'])
@flask_login.login_required
def for_sale(bookid):
    '''
    route to show the selected book that is for sale on the home page 
    '''
    book = db.books.find_one({"_id":ObjectId(bookid)})
    if request.method== 'GET':
        return render_template('book_for_sale.html',book=book)
    if request.method == 'POST':
        # the user requests to swap one of their books for this book
        # redirects to a list of the current users books to choose for the swap
        return redirect(url_for('choose_book',otherbookid=book["_id"]))

@app.route('/book_to_swap/<otherbookid>', methods=['GET','POST'])
@flask_login.login_required
def choose_book(otherbookid):
    '''
    route that shows all the user's books and allows them to choose one 
    to swap for the book they want (links to send_swap for the chosen book)
    @param otherbookid: id of the other user's book
    '''
    user =flask_login.current_user
    myBooks = db.books.find({"user_id": user.id})
    otherbook = db.books.find_one({"_id": ObjectId(otherbookid)})
    return render_template('book_to_swap.html', books=myBooks, otherbook=otherbook)

#-----------Send Swap Request--------------#

@app.route('/send_swap/<bookid>/<otherbookid>', methods=['GET','POST'])
@flask_login.login_required
def send_swap(bookid,otherbookid):
    '''
    route that shows the information of the user's book they want to swap for another 
    @param bookid: id of current user's book
    @param otherbookid: id of the other user's book
    '''
    user = flask_login.current_user
    if request.method == 'GET':
        book = db.books.find_one({"_id": ObjectId(bookid)})
        return render_template('send_swap.html',book=book,otherbookid=otherbookid)
    if request.method == 'POST':
        # the user chooses not to send the request for this book 
        if 'fcancel' in request.form:
            return redirect(url_for('choose_book',otherbookid=otherbookid))
        # the user sends the request to the other user
        elif 'fsend' in request.form:
            make_request(user,bookid,otherbookid)
            return redirect('/')
            #return redirect(url_for('chat'))

def make_request(user,bookid,otherbookid):
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
        "sender": ObjectId(user.id), # current user
        "reciever": ObjectId(otheruserid), # other user
        "booktoswap": ObjectId(bookid), # book the current user has
        "bookrequested": ObjectId(otherbookid) # book the current user wants
        })

#----------------------------------------#

@app.route('/swap_requests', methods=['GET'])
@flask_login.login_required
def view_swap_requests():
    """
    route that allows the user to see all of their recieved swap requests
    """
    user = flask_login.current_user
    requests = db.requests.find({"reciever": ObjectId(user.id)}).sort("_id",-1)
    # create an array of swap requests
    swapreqs = []
    for req in requests:
        mybookid = req["bookrequested"]
        otherbookid = req["booktoswap"]
        mybook= db.books.find_one({"_id": ObjectId(mybookid)}) # book the current user has
        otherbook= db.books.find_one({"_id": ObjectId(otherbookid)}) # book other user wants
        swapreqs.append({"mybook": mybook, "otherbook": otherbook})
    # display all requests
    return render_template('swap_requests.html', swapreqs=swapreqs)


#accept/decline request
@app.route('/view_swap/<mybookid>/<otherbookid>')
def view_swap(mybookid,otherbookid):
    """
    route that allows the user to view a specific swap request
    @param mybookid: id of the current user's book (that would be given from swap)
    @param otherbookid: id of the other user's book (that would be recieved from swap)
    """
    mybook = db.books.find_one({"_id": ObjectId(mybookid)})
    otherbook = db.books.find_one({"_id": ObjectId(otherbookid)})
    return render_template("view_swap.html", mybook=mybook, otherbook=otherbook)
    

################## run server ##################
if __name__=='__main__':
    app.run(host='0.0.0.0',debug=True, port=3000)