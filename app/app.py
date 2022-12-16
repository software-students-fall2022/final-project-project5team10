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



################## routes ##################



################## run server ##################
if __name__=='__main__':
    app.run(port=3000)