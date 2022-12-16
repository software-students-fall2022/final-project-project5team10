from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
#from pymongo import MongoClient
import os, sys

################## setup ##################
app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://db:27017/project5'

#client = MongoClient(host='db',
#                         port=27017)

"""def get_db(client):
    try:
        # verify the connection works by pinging the database
        # The ping command is cheap and does not require auth.
        client.admin.command('ping')
        # if we get here, the connection worked!
        print(' *', 'Connected to MongoDB!',file=sys.stderr)
    except Exception as e:
        # the ping command failed, so the connection is not available.
        # render_template('error.html', error=e) # render the edit template
        print(' *', "Failed to connect to MongoDB")
        return
    db = client.project_five
    return db
"""
################## routes ##################


# temp data
user = {
    "email": "abc123@gmail.com",
    "books": [{"name": "Harry Potter"},{"name": "The Hobbit"},{"name": "The Batman"},{"name": "Scream"}]
}

# db for all books on the site?
# create book object, add to the user and to all books
#bookshelf = {
#    "Harry Potter"

#}

@app.route('/chat',methods=['GET','POST'])
def chat():
    return render_template('/chat.html')


@app.route('/book_to_swap', methods=['GET','POST'])
def choose_book():
    #myBooks = flask_login.current_user.books
    myBooks = user["books"]
    return render_template('book_to_swap.html', books = myBooks)

@app.route('/send_swap/<bookname>', methods=['GET','POST'])
def send_swap(bookname):
    if request.method == 'GET':
        #book = db.books.find{"name": bookname} #replace with object_id later
        for i in range(len(user["books"])):
            if user["books"][i]["name"] == bookname:
                return render_template('send_swap.html',book= user["books"][i])
                #break
        #book = user["books"][bookname]
        #print("chicken",file=sys.stdout)
        return render_template('send_swap.html')
    else:
        # send the request to the othe user
        return redirect('/chat')




################## run server ##################
if __name__=='__main__':
    app.run(port=3000)