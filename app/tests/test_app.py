import pytest
import random
import string
import app
from bson.objectid import ObjectId
import flask_login
import mongomock
from app import locate_user
from app import user_loader
from app import inject_user
import sys


# client = mongomock.MongoClient()
# collection = client.db.collection

collection = mongomock.MongoClient().db.collection
collection2 = mongomock.MongoClient().db.collection2
collection3 = mongomock.MongoClient().db.collection2

# ======================================================#
#                     main routes tests                 #
# ======================================================#
# ROUTE: route handler for request to '/'


def test_authenticate(flask_app):
    url = '/'
    response = flask_app.get(url)
    assert response.status_code == 200

# ROUTE: route handler for post request to '/home'


def test_home_post(flask_app):
    url = '/home'
    response = flask_app.post(url, data=dict(query="book1"))
    assert response.status_code == 200
    assert response.request.base_url == "http://localhost/home"

# ======================================================#
#                   signup/register tests               #
# ======================================================#

# ROUTE: route handler for Get request to '/signupPage'


def test_signupPage(flask_app):
    url = '/signupPage'
    response = flask_app.get(url)
    assert response.status_code == 200

# ROUTE: route handler for Post request to '/signup'


def test_signup(flask_app):
    url = '/signup'
    username = ''.join(random.choices(
        string.ascii_uppercase+string.digits, k=10))
    password = ''.join(random.choices(
        string.ascii_uppercase+string.digits, k=10))
    email = ''.join(random.choices(string.ascii_uppercase +
                    string.digits, k=10)) + "@gmail.com"
    response = flask_app.post(url, data=dict(
        fusername=username, fpassword=password, femail=email))
    assert response.status_code == 302


def test_signup_empty(flask_app,captured_templates):
    url = '/signup'
    email = ''.join(random.choices(string.ascii_uppercase +
                    string.digits, k=10)) + "@gmail.com"
    response = flask_app.post(url, data=dict(
        fusername="", fpassword="password", femail=email))
    assert response.status_code == 200
    response = flask_app.post(url, data=dict(
        fusername="username", fpassword="", femail=email))
    assert response.status_code == 200
    assert len(captured_templates) == 2
    template, context = captured_templates[0]
    assert template.name == "signup.html"
    assert "crederror" in context
    assert context["crederror"] == "Username or password must be at least 6 characters"


def test_signup_space(flask_app,captured_templates):
    url = '/signup'
    email = ''.join(random.choices(string.ascii_uppercase +
                    string.digits, k=10)) + "@gmail.com"
    response = flask_app.post(url, data=dict(
        fusername="test space", fpassword="password", femail=email))
    assert response.status_code == 200
    assert len(captured_templates) == 1
    template, context = captured_templates[0]
    assert template.name == "signup.html"
    assert "blankerror" in context
    assert context["blankerror"] == "Username or password cannot contain spaces"

def test_signup_exist(flask_app,captured_templates):
    url = '/signup'
    email = ''.join(random.choices(string.ascii_uppercase +
                    string.digits, k=10)) + "@gmail.com"
    flask_app.post(url,data=dict(fusername='testingalready',fpassword='password',femail=email))
    response = flask_app.post(url, data=dict(
        fusername="testingalready", fpassword="password", femail=email))
    assert response.status_code == 200
    assert len(captured_templates) == 2
    template, context = captured_templates[0]
    assert template.name == "signup.html"
    assert "unerror" in context
    assert context["unerror"] == "This username already exists."




# ROUTE: route handler for Post request to '/login' with invalid input
def test_login_empty(flask_app):
    url = '/login'
    username = ""
    password = ""
    response = flask_app.post(url, data=dict(
        fusername=username, fpassword=password))
    assert response.status_code == 200


def test_login_with_space(flask_app):
    url = 'login'
    response = flask_app.post(url, data=dict(
        fusername="test space", fpassword="password"))
    assert response.status_code == 302


def test_login(flask_app):
    url = 'login'
    response = flask_app.post(url, data=dict(
        fusername="test", fpassword="password"))
    assert response.status_code == 200

# ROUTE: route handler for request to '/logout'


def test_logout(flask_app):
    url = '/logout'
    response = flask_app.get(url)
    assert response.status_code == 302

# ======================================================#
#                      book CRUD tests                  #
# ======================================================#

# ROUTE: route handler for Get request to '/add_book'


def test_add_book_get(flask_app):
    url = '/add_book'
    response = flask_app.get(url)
    assert response.status_code == 200

# ROUTE: route handler for Post request to '/add_book'


def test_add_book_post(flask_app):
    url = '/add_book'
    response = flask_app.post(url, data=dict(
        ftitle="testbook", fpublisher='testpublisher', fedition='testedition', fcondition='testcondition'))
    assert response.status_code == 200


def test_add_book_helper():
    mockReq = dict(ftitle="testbook", fpublisher='testpublisher',
                   fedition='testedition', fcondition='testcondition')
    book = app.add_book_helper(
        reqForm=mockReq,
        testing=True)
    assert book["title"] == mockReq['ftitle']
    assert book["publisher"] == mockReq['fpublisher']
    assert book["user_id"] == "542c2b97bac0595474108b52"
    assert book["edition"] == mockReq["fedition"]
    assert book["condition"] == mockReq["fcondition"]


def test_add_book_helper_missing_field():
    # one field empty
    mockReq = dict(ftitle="testbook", fpublisher='',
                   fedition='testedition', fcondition='testcondition')
    html_render = app.add_book_helper(
        reqForm=mockReq,
        testing=True)
    assert "<h3>Please fill out all fields</h3>" in html_render

def test_book_info_helper():
    #book
    user = 'user'
    collection.insert_one({
        "_id": ObjectId("542c2b97bac0595474108b52")
    })
    book = collection.find_one({"_id": ObjectId("542c2b97bac0595474108b52")})
    # GET
    res = app.book_info_helper(book["_id"], "GET", coll=collection, currUser=user, testing=True)
    assert "<h3>Title: </h3>" in res
    # POST
    res = app.book_info_helper(book["_id"], "POST", coll=collection, currUser=user, testing=True)
    print(res)
    assert res.status_code == 302



# ======================================================#
#                     book viewing tests                #
# ======================================================#

# ROUTE: route handler for Get request to '/edit/<bookid>'
def test_edit(flask_app):
    url = '/edit/2'
    response = flask_app.get(url)
    assert response.status_code == 200


# ROUTE: route handler for request to '/delete/<bookid>'
def test_delete(flask_app):
    url = '/delete/2'
    response = flask_app.get(url)
    assert response.status_code == 200

# ======================================================#
#                     book viewing tests                #
# ======================================================#

# ROUTE: route handler for Get request to '/book_info/<bookid>'


def test_book_info_get(flask_app):
    url = '/book_info/542c2b97bac0595474108b48'
    response = flask_app.get(url)
    assert response.status_code == 200
    # assert b"<div class='bookInfo'>" in response.data

# ROUTE: route handler for Post request to '/book_info/<bookid>'

# ROUTE: route handler for Get request to '/book_to_swap/<otherbookid>'


def test_book_to_swap(flask_app):
    url = '/book_to_swap/2'
    response = flask_app.get(url)
    assert response.status_code == 200


# ======================================================#
#                        account test                   #
# ======================================================#

# ROUTE: route handler for request to '/account'
def test_account(flask_app):
    url = '/account'
    response = flask_app.get(url)
    assert response.status_code == 200

# ======================================================#
#                     swap routes tests                 #
# ======================================================#

# ROUTE: route handler for Get request to '/send_swap/<bookid>/<otherbookid>'


def test_send_swap_get(flask_app):
    url = '/send_swap/542c2b97bac0595474108b48/542c2b97bac0595474108b49'
    response = flask_app.get(url)
    assert response.status_code == 200

# ROUTE: route handler for Post request to '/send_swap/<bookid>/<otherbookid>'


def test_send_swap_post(flask_app):
    url = '/send_swap/542c2b97bac0595474108b48/542c2b97bac0595474108b49'
    response = flask_app.post(url, data='fcancel')
    assert response.status_code == 200
    response = flask_app.post(url, data='fsend')
    assert response.status_code == 200

# ROUTE: route handler for Get request to '/swap_requests'


def test_swap_requests(flask_app):
    url = '/swap_requests'
    response = flask_app.get(url)
    assert response.status_code == 200


# ROUTE: route handler for Get request to '/view_swap/<mybookid>/<otherbookid>'
def test_view_swap(flask_app):
    url = '/view_swap/542c2b97bac0595474108b48/542c2b97bac0595474108b48'
    response = flask_app.get(url)
    assert response.status_code == 200

# ROUTE: route handler for Post request to '/view_swap/<mybookid>/<otherbookid>'


def test_view_swap_post(flask_app):
    url = '/view_swap/542c2b97bac0595474108b48/542c2b97bac0595474108b48'
    response = flask_app.post(url, data="fapprove")
    assert response.status_code == 200
    response = flask_app.post(url, data="fdecline")
    assert response.status_code == 200


# -----------------------------UNAUTHORIZED and INVALID TESTS-------------------------------------

def test_book_to_swap_notID(flask_app):
    url = '/book_to_swap'
    response = flask_app.get(url)
    assert response.status_code == 404


def test_send_swap_noID(flask_app):
    url = '/send_swap'
    response = flask_app.get(url)
    assert response.status_code == 404


def test_signup_withoutInvalidForm(flask_app):
    url = '/signup'
    username = ''.join(random.choices(
        string.ascii_uppercase+string.digits, k=4))
    password = ''.join(random.choices(
        string.ascii_uppercase+string.digits, k=4))
    response = flask_app.post(url)
    assert response.status_code == 400


def test_login_badRequest(flask_app):
    url = '/login'
    username = "bookworm"
    password = "1234"
    response = flask_app.post(url)
    assert response.status_code == 400

# --------------------------------------HELPER FUNCTIONS------------------------------------------


def test_isfloat_true():
    assert app.isfloat(1.4) is True


def test_isfloat_false():
    assert app.isfloat('num') is False

# test allowed file


def test_allowed_file():
    test_file = "writing.png"
    assert app.allowed_file(test_file) is True


def test_get_and_insert_metadata():
    bookObj = {
        "title": "To Kill a Mockingbird"
    }
    app.get_and_insert_metadata(bookObj)
    assert bookObj["metadata"] is not None
    assert bookObj["status"] == "swappable"
    assert bookObj["image_exists"] == False


def test_find_book_coll_by_query():
    reqForm = {
        "query": "info present",
        "title": "Pride and Prejudice",
        "edition": "3",
        "publisher": "Pendant",
        "condition": "New"
    }
    books = app.findBookCollByQuery(reqForm, col=collection)
    assert books is not None


def test_update_book_status():
    senderBookObj = {
        "_id": ObjectId("542c2b97bac0595474108b48"),
        "status": "swappable"
    }
    receiverBookObj = {
        "_id": ObjectId("542c2b97bac0595474108b49"),
        "status": "pending"
    }
    insertArr = [senderBookObj, receiverBookObj]
    collection.insert_many(insertArr)

    app.update_book_status('542c2b97bac0595474108b48', 'pending',
                           '542c2b97bac0595474108b49', 'swappable', col=collection)

    # senderBookObj status changed from swappable to pending
    assert collection.find_one({"_id": ObjectId("542c2b97bac0595474108b48")})[
        "status"] == "pending"
    # receiverBookObj status changed from pending to swappable
    assert collection.find_one({"_id": ObjectId("542c2b97bac0595474108b49")})[
        "status"] == "swappable"
    collection.drop()


def test_remove_all():
    mybookid = "542c2b97bac0595474108b48"
    otherbookid = "542c2b97bac0595474108b49"
    req1 = {
        "sender": ObjectId("542c2b97bac0595474108b48"),
        "reciever": ObjectId("542c2b97bac0595474108b47"),
        "booktoswap": ObjectId("542c2b97bac0595474108b46"),
        "bookrequested": ObjectId("542c2b97bac0595474108b45"),
    }
    collection.insert_one(req1)
    collection2.insert_one({"_id": ObjectId(mybookid)})
    collection2.insert_one({"_id": ObjectId(otherbookid)})

    app.remove_all(mybookid, otherbookid, col=collection, col2=collection2)
    assert collection.find_one(
        {"_id": ObjectId("542c2b97bac0595474108b48")}) is None
    assert collection2.find_one({"_id": ObjectId(mybookid)}) is None
    assert collection2.find_one({"_id": ObjectId(otherbookid)}) is None
    collection.drop()
    collection2.drop()
# ------------------------------------SET UP---------------------------------------------


def test_locate_user():
    user1 = app.User({'_id': ObjectId("542c2b97bac0595474108b50")})
    collection.insert_one(
        {
            '_id': ObjectId("542c2b97bac0595474108b50"),
            "username": "username"
        }
    )
    result = locate_user('542c2b97bac0595474108b50',
                         'username', col=collection)
    assert result == user1
    result = locate_user(username='username', col=collection)
    assert result == user1
    collection.drop()


def test_inject_user():
    result = inject_user()
    assert type(result) == dict

def test_edit_book_helper():
    book = {
        "_id": ObjectId("542c2b97bac0595474108b48"),
        "status": "swappable"
    }
    collection.insert_one(book)
    result=app.edit_book_helper("542c2b97bac0595474108b48",col=collection)
    assert result==book
    collection.drop()



def test_req_array():
    userid = "542c2b97bac0595474108b50"
    otheruserid = "542c2b97bac0595474108b49"
    mybookid = "542c2b97bac0595474108b42"
    otherbookid = "542c2b97bac0595474108b43"

    recent_id = collection.insert_one({ # (requests collection)
        "sender": ObjectId(otheruserid),     
        "reciever": ObjectId(userid), # recieves the request
        "booktoswap": ObjectId(otherbookid),
        "bookrequested": ObjectId(mybookid), 
    }).inserted_id

    collection2.insert_one({"_id":ObjectId(mybookid), "user_id": userid})
    collection2.insert_one({"_id": ObjectId(otherbookid), "user_id": otheruserid})
    collection3.insert_one({"_id": ObjectId(userid)}) # insert user

    the_id = app.req_array(userid, col=collection, col2=collection2, col3=collection3)[0]["mybook"]["user_id"]
    
    assert collection.find_one({"_id":ObjectId(recent_id)})["reciever"] == ObjectId(the_id)
    collection.drop()
    collection2.drop()
    collection3.drop()
