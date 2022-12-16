from flask import Flask, jsonify, render_template, request, redirect, flash
from dotenv import dotenv_values
from werkzeug.utils import secure_filename

import pymongo
import datetime
from bson.objectid import ObjectId
import sys, os

# modules useful for user authentication
import flask_login
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

################## setup ##################
app = Flask(__name__)






def locate_user(user_id=None, username=None):
    '''
    Return a User object for the user with the given id or email address, or None if no such user exists.
    @param user_id: the user_id of the user to locate
    @param email: the email address of the user to locate
    '''
    if user_id:
        # loop up by user_id
        criteria = {"_id": ObjectId(user_id)}
    else:
        # loop up by email
        criteria = {"username": username}
    doc = db.users.find_one(criteria) # find a user with this email
    # if user exists in he database, create a User object and return it
    if doc:
        # return a user object representing this user
        user = User(doc)
        return user

    return None

################## routes ##################

################## run server ##################
if __name__=='__main__':
    app.run(port=3000)