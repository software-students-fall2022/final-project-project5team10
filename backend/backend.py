from flask import Flask, jsonify, render_template, request, redirect, flash

################## setup ##################
app = Flask(__name__)



################## routes ##################



################## run server ##################
if __name__=='__main__':
    app.run(port=3000)