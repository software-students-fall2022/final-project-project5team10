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


# ======================================================#
#                     main routes tests                 #
# ======================================================#
#ROUTE: route handler for request to '/'
def test_authenticate(flask_app):
    url='/'
    response=flask_app.get(url)
    assert response.status_code==200

#ROUTE: route handler for get request to '/home'
def test_home(flask_app):
    url='/home'
    response=flask_app.get(url)
    assert response.status_code==401


#ROUTE: route handler for post request to '/home'
def test_home_post(flask_app):
    url='/home'
    response=flask_app.post(url,data=dict(query="book1"))
    assert response.status_code==401

# ======================================================#
#                   signup/register tests               #
# ======================================================#

#ROUTE: route handler for Get request to '/signupPage'
def test_signupPage(flask_app):
    url='/signupPage'
    response=flask_app.get(url)
    assert response.status_code==200

#ROUTE: route handler for Post request to '/signup'
def test_signup(flask_app):
    url='/signup'
    username=''.join(random.choices(string.ascii_uppercase+string.digits,k=4))
    password=''.join(random.choices(string.ascii_uppercase+string.digits,k=4))
    email=''.join(random.choices(string.ascii_uppercase+string.digits,k=4)) + "@gmail.com"
    response=flask_app.post(url ,data=dict(fusername=username,fpassword=password,femail="email.com"))
    assert response.status_code==200

#ROUTE: route handler for Post request to '/login' with invalid input
def test_login_withIncorrect(flask_app):
    url='/login'
    username=""
    password=""
    response=flask_app.post(url,data=dict(fusername=username,fpassword=password))
    assert response.status_code==200

#ROUTE: route handler for Post request to '/login' 
# def test_login(flask_app):
#     url='/login'
#     flask_app.post('/signup',data=dict(fusername='testbook',fpassword='password',femail='booktest@gmail.com'))
#     username="testbook"
#     password="password"
#     response=flask_app.post(url,data=dict(fusername=username,fpassword=password))
#     assert response.status_code==200

#ROUTE: route handler for request to '/logout'
def test_logout(flask_app):
    url='/logout'
    response=flask_app.get(url)
    assert response.status_code==302

# ======================================================#
#                      book CRUD tests                  #
# ======================================================#

#ROUTE: route handler for Get request to '/add_book'
def test_add_book_get(flask_app):
    url='/add_book'
    response=flask_app.get(url)
    assert response.status_code==200

#ROUTE: route handler for Post request to '/add_book'
def test_add_book_post(flask_app):
    url='/add_book'
    response=flask_app.post(url,data=dict(ftitle="testbook",fpublisher='testpublisher',fedition='testedition',fcondition='testcondition'))
    assert response.status_code==200

# ======================================================#
#                     book viewing tests                #
# ======================================================#

#ROUTE: route handler for Get request to '/edit/<bookid>'
def test_edit(flask_app):
    url='/edit/2'
    response=flask_app.get(url)
    assert response.status_code==404


#ROUTE: route handler for request to '/delete/<bookid>'
def test_delete(flask_app):
    url='/delete/2'
    response=flask_app.get(url)
    assert response.status_code==404

# ======================================================#
#                     book viewing tests                #
# ======================================================#

#ROUTE: route handler for Get request to '/book_info/<bookid>'
def test_book_info_get(flask_app):
    url='/book_info/2'
    response=flask_app.get(url)
    assert response.status_code==404

#ROUTE: route handler for Post request to '/book_info/<bookid>'

#ROUTE: route handler for Get request to '/book_to_swap/<otherbookid>'
def test_book_to_swap_get(flask_app):
    url='/book_to_swap/2'
    response=flask_app.get(url)
    assert response.status_code==404

#ROUTE: route handler for Post request to '/book_to_swap/<otherbookid>'


# ======================================================#
#                        account test                   #
# ======================================================#

#ROUTE: route handler for request to '/account'
def test_account(flask_app):
    url='/account'
    response=flask_app.get(url)
    assert response.status_code==404

# ======================================================#
#                     swap routes tests                 #
# ======================================================#

#ROUTE: route handler for Get request to '/send_swap/<bookid>/<otherbookid>'
def test_sned_swap_get(flask_app):
    url='/send_swao/2/4'
    response=flask_app.get(url)
    assert response.status_code==404

#ROUTE: route handler for Post request to '/send_swap/<bookid>/<otherbookid>'

#ROUTE: route handler for Get request to '/swap_requests'
def test_swap_requests(flask_app):
    url='/swap_requests'
    response=flask_app.get(url)
    assert response.status_code==404


#ROUTE: route handler for Get request to '/view_swap/<mybookid>/<otherbookid>'
def test_view_swap(flask_app):
    url='/view_swap/2/4'
    response=flask_app.get(url)
    assert response.status_code==404

#ROUTE: route handler for Post request to '/view_swap/<mybookid>/<otherbookid>'


#-----------------------------UNAUTHORIZED and INVALID TESTS-------------------------------------
def test_home_notAuthorized(flask_app):
    url='/home'
    response=flask_app.get(url)
    assert response.status_code==401

def test_add_book_notAuthorized(flask_app):
    url='/add_book'
    response=flask_app.get(url)
    assert response.status_code==401

def test_account_notAuthorized(flask_app):
    url='/account'
    response=flask_app.get(url)
    assert response.status_code==401

def test_book_to_swap_notID(flask_app):
    url='/book_to_swap'
    response=flask_app.get(url)
    assert response.status_code==404

def test_send_swap_noID(flask_app):
    url='/send_swap'
    response=flask_app.get(url)
    assert response.status_code==404

def test_swap_requests_notAuthorized(flask_app):
    url='/swap_requests'
    response=flask_app.get(url)
    assert response.status_code==401

def test_signup_withoutInvalidForm(flask_app):
    url='/signup'
    username=''.join(random.choices(string.ascii_uppercase+string.digits,k=4))
    password=''.join(random.choices(string.ascii_uppercase+string.digits,k=4))
    response=flask_app.post(url)
    assert response.status_code==400

def test_login_badRequest(flask_app):
    url='/login'
    username="bookworm"
    password="1234"
    response=flask_app.post(url)
    assert response.status_code==400

#--------------------------------------HELPER FUNCTIONS------------------------------------------
def test_isfloat_true():
   assert app.isfloat(1.4) is True
 
def test_isfloat_false():
   assert app.isfloat('num') is False
 
# test allowed file
def test_allowed_file():
  test_file = "writing.png"
  assert app.allowed_file(test_file) is True



def test_update_book_status():
    senderBookObj = {
        "_id" : ObjectId("542c2b97bac0595474108b48"),
        "status": "swappable"
    }
    receiverBookObj = {
        "_id" : ObjectId("542c2b97bac0595474108b49"),
        "status": "pending"
    }
    insertArr = [senderBookObj, receiverBookObj]
    collection.insert_many(insertArr)

    app.update_book_status('542c2b97bac0595474108b48', 'pending', '542c2b97bac0595474108b49', 'swappable', col=collection )

    # senderBookObj status changed from swappable to pending
    assert collection.find_one({"_id": ObjectId("542c2b97bac0595474108b48")})["status"] == "pending"
    # receiverBookObj status changed from pending to swappable
    assert collection.find_one({"_id": ObjectId("542c2b97bac0595474108b49")})["status"] == "swappable"
    collection.drop()
#------------------------------------SET UP---------------------------------------------
def test_locate_user():
    user1 = app.User({'_id': ObjectId("542c2b97bac0595474108b50")})
    collection.insert_one(
        {
            '_id': ObjectId("542c2b97bac0595474108b50"),
            "username": "username"
        }
    )
    result = locate_user('542c2b97bac0595474108b50','username', testing=True, col=collection)
    assert result==user1
    collection.drop()

# def test_user_loader():
#     result=user_loader('1234')
#     assert result==None

def test_inject_user():
    result=inject_user()
    assert type(result)==dict

