#======================================================#
#                        imports                       #
#======================================================#

# flask
from flask import Flask, jsonify, render_template, request, redirect, flash, url_for
from werkzeug.utils import secure_filename

# mongodb
import pymongo
import time, datetime
from bson.objectid import ObjectId
import codecs, gridfs

# user authentication
import flask_login
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

# testing
import sys, os

# allowed file types for upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}



#======================================================#
#                        setup                         #
#======================================================#
app = Flask(__name__)
app.secret_key = os.urandom(24)

# set up flask-login for user authentication
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

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
        self.id = data['_id']  # shortcut to the _id field
        self.data = data  # all user data from the database is stored within the data field


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
    doc = db.users.find_one(criteria)  # find a user with this username
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




#======================================================#
#                     main routes                      #
#======================================================#

@app.route('/')
def authenticate():
    # Route for the home page
    return render_template("login.html")

@app.route('/home', methods=['GET', 'POST'])
@flask_login.login_required
def home():
    if request.method == 'POST':
        query = request.form['query']

        books = db.books.find({'title': query})
        return render_template('search_results.html', books=books)

    '''
    find all the books currently on sale by other users
    '''
    docs = db.books.find({"user_id": {"$ne": flask_login.current_user.id}}
                         )  # return all the book documents from the books collection that do not have the current user's id
    # render the home template with those documents
    return render_template("home.html", docs=docs)




#======================================================#
#                   signup/register                    #
#======================================================#


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
    email    = request.form['femail']
    if len(username) < 6 or len(password) < 6:
        return render_template('signup.html', crederror="Username or password must be at least 6 characters")
    # generate a hashed password to store - don't store the original
    hashed_password = generate_password_hash(password)

    # check if there is a space in username
    if username.isspace():
        return render_template('signup.html', blankerror="Username or password cannot contain spaces")
    # check whether an account with this email already exists... don't allow duplicates
    if locate_user(username=username):
        # flash('An account for {} already exists.  Please log in.'.format(username))
        return render_template('signup.html', unerror="This username already exists.")

    # create a new document in the database for this new user
    # hash the password and save it to the database
    user_id = db.users.insert_one(
        {"username": username, "password": hashed_password}).inserted_id
    if user_id:
        # successfully created a new user... make a nice user object
        user = User({
            "_id": user_id,
            "username": username,
            "email"   : email,
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
        return render_template("home.html")
    return render_template("login.html", message="Username or Password is incorrect")

@app.route('/logout')
def logout():
    '''
    route to end the current user's session 
    '''
    flask_login.logout_user()
    # flash('You have been logged out.  Bye bye!') # pass a special message to the template
    return redirect(url_for('authenticate'))




#======================================================#
#                      book CRUD                       #
#======================================================#


@app.route('/add_book', methods=["GET", "POST"])
@flask_login.login_required
def add_book():
    '''
    route that adds a book to the books collection with the user_id 
    field set to the current user's id 
    '''
    user = flask_login.current_user
    if request.method == "GET":
        return render_template("add_book.html")

    # POST REQUEST FROM FORM
    if request.method == "POST":
        book = {}
        book["title"] = request.form['ftitle']
        book["publisher"] = request.form['fpublisher']
        book["user_id"] = user.id
        book["edition"] = request.form['fedition']
        book["condition"] = request.form['fcondition']
        book["price"] = float(request.form['fprice'])

        # use gridfs to save uploaded image to database

        # if file is not in requests, add book into the books collection and
        # render account page
        if 'file' not in request.files:
            db.books.insert_one(book)


        # get uploaded file
        file = request.files['file']

        if file and allowed_file((file.filename)):  # check for allowed extensions
            filename = secure_filename(file.filename)
            user = flask_login.current_user
            # unique file name: user id + filename
            name = str(user.id) + "_" + str(filename)
            # upload file in chunks into the db using grid_fs
            id = grid_fs.put(file, filename=name)
            # document to be inserted into the images collection
            query = {
                "user": user.id,
                "book_name": book["title"],
                "img_id": id
            }
            # add gridfs id to the image field of the book document to be queried into the books collection
            book["image"] = id
            # get image chunks, read it, encode it, add the encoding to the "image_base64" field to be able to render it using html
            image = grid_fs.get(id)
            base64_data = codecs.encode(image.read(), 'base64')
            image = base64_data.decode('utf-8')
            book['image_base64'] = image
            # add the image query into the images collection
            db.images.insert_one(query)
        db.books.insert_one(book)
        return redirect(url_for('display_account'))


@app.route('/edit/<bookid>',methods=['GET'])
@flask_login.login_required
def edit_book(bookid):
    '''
    record existing attributes of book and pass them to template
    as existing field values after removing book from db
    '''
    book_record = db.books.find_one({"_id": ObjectId(bookid)})
    db.books.delete_one({"_id": ObjectId(bookid)})
    return render_template('edit_book.html', book=book_record)


@app.route('/delete/<bookid>', methods=['GET'])
@flask_login.login_required
def delete_book(bookid):
    '''
    delete book from database given a book_id
    '''
    db.books.delete_one({"_id": ObjectId(bookid)})
    # print("deleted book with id: " + str(bookid), file=sys.stderr)
    return redirect(url_for('display_account'))





#======================================================#
#                     book viewing                     #
#======================================================#

# @app.route('/my_book_for_sale<bookid>', methods=['GET', 'POST'])
# @flask_login.login_required


@app.route('/book_info/<bookid>', methods=['GET', 'POST'])
@flask_login.login_required
def book_info(bookid):
    '''
    route to show the selected book that is for sale on the home page 
    '''
    book = db.books.find_one({"_id": ObjectId(bookid)})

    # conditional rendering: present options to edit/delete on page only if user owns the book
    user = flask_login.current_user
    is_owner = book["user_id"] == user.id

    if request.method == 'GET':
        return render_template('book_info.html', book=book, is_owner=is_owner)

    if request.method == 'POST':
        # the user requests to swap one of their books for this book
        # redirects to a list of the current users books to choose for the swap
        return redirect(url_for('choose_book', otherbookid=book["_id"]))


@app.route('/book_to_swap/<otherbookid>', methods=['GET','POST'])
@flask_login.login_required
def choose_book(otherbookid):
    '''
    route that shows all the user's books and allows them to choose one 
    to swap for the book they want (links to send_swap for the chosen book)
    @param otherbookid: id of the other user's book
    '''
    user = flask_login.current_user
    myBooks = db.books.find({"user_id": user.id})
    otherbook = db.books.find_one({"_id": ObjectId(otherbookid)})
    return render_template('book_to_swap.html', books=myBooks, otherbook=otherbook)


# # curent user's books
# @app.route('/book_for_sale/<bookid>', methods=['GET'])
# @flask_login.login_required
# def for_sale(bookid):
#     '''
#     route to show the selected book that is for sale on the home page
#     '''
#     book = db.books.find_one({"_id":ObjectId(bookid)})
#     return render_template('book_for_sale.html',book=book)





#======================================================#
#                         chat                         #
#======================================================#

@app.route('/view_chat')
@flask_login.login_required
def view_chat():
    '''
    TODO: to be implemented 
    '''
    pass




#======================================================#
#                        account                       #
#======================================================#


@app.route('/account')
@flask_login.login_required
def display_account():
    '''
    display all the documents with the user_id field set
    to the current user's id 
    '''
    user = flask_login.current_user
    docs = db.books.find({"user_id": user.id})
    # render the account template with the user's username and the books they have up for sale
    return render_template("account.html", username=user.data["username"], docs=docs)




#======================================================#
#                     swap routes                      #
#======================================================#

@app.route('/send_swap/<bookid>/<otherbookid>', methods=['GET', 'POST'])
@flask_login.login_required
def send_swap(bookid, otherbookid):
    '''
    route that shows the information of the user's book they want to swap for another 
    @param bookid: id of current user's book
    @param otherbookid: id of the other user's book
    '''
    user = flask_login.current_user
    if request.method == 'GET':
        book = db.books.find_one({"_id": ObjectId(bookid)})
        return render_template('send_swap.html', book=book, otherbookid=otherbookid)
    if request.method == 'POST':
        # the user chooses not to send the request for this book
        if 'fcancel' in request.form:
            return redirect(url_for('choose_book', otherbookid=otherbookid))
        # the user sends the request to the other user
        elif 'fsend' in request.form:
            make_request(user,bookid,otherbookid)
            return redirect('/home')
            #return redirect(url_for('chat'))

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
        "sender": ObjectId(user.id),  # current user
        "reciever": ObjectId(otheruserid),  # other user
        "booktoswap": ObjectId(bookid),  # book the current user has
        "bookrequested": ObjectId(otherbookid)  # book the current user wants
    })


@app.route('/swap_requests', methods=['GET','POST'])
@flask_login.login_required
def view_swap_requests():
    """
    route that allows the user to see all of their recieved swap requests
    """
    user = flask_login.current_user
    requests = db.requests.find(
        {"reciever": ObjectId(user.id)}).sort("_id", -1)
    # create an array of swap requests
    swapreqs = []
    for req in requests:
        mybookid = req["bookrequested"]
        otherbookid = req["booktoswap"]
        # book the current user has
        mybook = db.books.find_one({"_id": ObjectId(mybookid)})
        otherbook = db.books.find_one(
            {"_id": ObjectId(otherbookid)})  # book other user wants
        swapreqs.append({"mybook": mybook, "otherbook": otherbook})
    # display all requests
    return render_template('swap_requests.html', swapreqs=swapreqs)



#accept/decline request
@app.route('/view_swap/<mybookid>/<otherbookid>', methods=['GET','POST'])
@flask_login.login_required
def view_swap(mybookid,otherbookid):
    """
    route that allows the user to view a specific swap request
    @param mybookid: id of the current user's book (that would be given from swap)
    @param otherbookid: id of the other user's book (that would be recieved from swap)
    """
    mybook = db.books.find_one({"_id": ObjectId(mybookid)})
    otherbook = db.books.find_one({"_id": ObjectId(otherbookid)})
    
    if request.method == 'GET':
        return render_template("view_swap.html", mybook=mybook, otherbook=otherbook)
    if request.method == 'POST':
        # approve swap
        if 'fapprove' in request.form:
            # remove all requests containing either of these books
            db.requests.delete_many({"bookrequested": ObjectId(mybookid)})
            db.requests.delete_many({"booktoswap": ObjectId(mybookid)})
            db.requests.delete_many({ "booktoswap": ObjectId(otherbookid)})
            db.requests.delete_many({ "bookrequested": ObjectId(otherbookid)})
            # remove books from database
            db.books.delete_one({"_id": ObjectId(mybookid)})
            db.books.delete_one({"_id": ObjectId(otherbookid)})
            #flash('Request has been Approved!')
            return redirect(url_for('view_swap_requests'))
        # decline swap
        if 'fdecline' in request.form:
            # remove this request from the database
            db.requests.delete_one(
                { "$and": [ {"bookrequested": ObjectId(mybookid)},
                { "booktoswap": ObjectId(otherbookid)} ] }
            )
            #flash('Request has been Declined')
            return redirect(url_for('view_swap_requests'))   




#======================================================#
#                         run                          #
#======================================================#
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=3000)
