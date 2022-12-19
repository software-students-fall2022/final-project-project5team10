import pytest
import random
import string
import app
import flask_login
#import mongomock


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

#ROUTE: route handler for Get request to '/add_book'
def test_add_book_get(flask_app):
    url='/add_book'
    response=flask_app.get(url)
    assert response.status_code==200

#ROUTE: route handler for Post request to '/add_book'



#ROUTE: route handler for Get request to '/view_chat'


#ROUTE: route handler for request to '/account'

#-----------------------------SWAP ROUTE TESTS-------------------------------------------------
#ROUTE: route handler for Get request to '/for_sale'

#ROUTE: route handler for Post request to '/for_sale'

#ROUTE: route handler for Get request to '/choose_book'

#ROUTE: route handler for Post request to '/choose_book'

#ROUTE: route handler for Get request to '/send_swap'

#ROUTE: route handler for Post request to '/send_swap'

#ROUTE: route handler for request to '/make_request'

#ROUTE: route handler for Get request to '/swap_requests'

#ROUTE: route handler for request to '/view_swap'

#-----------------------------UNAUTHORIZED and INVALID TESTS-------------------------------------
def test_home_notAuthorized(flask_app):
    url='/home'
    response=flask_app.get(url)
    assert response.status_code==401

def test_add_book_notAuthorized(flask_app):
    url='/add_book'
    response=flask_app.get(url)
    assert response.status_code==401

def test_view_chat_notAuthorized(flask_app):
    url='/view_chat'
    response=flask_app.get(url)
    assert response.status_code==401

def test_account_notAuthorized(flask_app):
    url='/account'
    response=flask_app.get(url)
    assert response.status_code==401

def test_book_for_sale_noID(flask_app):
    url='/book_for_sale'
    response=flask_app.get(url)
    assert response.status_code==404

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
