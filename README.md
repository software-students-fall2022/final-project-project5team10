[![App Testing](https://github.com/software-students-fall2022/final-project-project5team10/actions/workflows/build-app.yaml/badge.svg)](https://github.com/software-students-fall2022/final-project-project5team10/actions/workflows/build-app.yaml)
[![App CD](https://github.com/software-students-fall2022/final-project-project5team10/actions/workflows/docker-cd.yaml/badge.svg)](https://github.com/software-students-fall2022/final-project-project5team10/actions/workflows/docker-cd.yaml)
# Bookshare

Bookshare aims to make college textbooks more affordable through the exchange of used books.

## Project Description
Bookshare consists of two subsystems: </br>
* **Flask Web App**: Displays user-supplied data and displays data fetched via Google Books API to display relevant data. Allows different users, after authentication, to send requests and view listings supplied by other users.
* **MongoDB Database**: Stores user credentials and data per user
## User Cases

Users can register for an account. With an account, one can:

* search for books
* check book previews via Google Books API
* upload books to your account to put them up for trade
* upload pictures and details regarding your listing

## How to Run Project Locally
1. While running Docker, at the root directory of the project: </br>
   </br>`docker compose up --build`</br>

2. The database container will be created and the Flask Web Application will run on `localhost:3000` or `127:0.0.1:3000` </br>
3. Create a username and password (constrained to minimum 6 characters each), login and start viewing other users' listings or add your own listing by navigating to the 'My Account' link on the top right corner.
4. You will be able to view all listings on the homepage and click on the title of each listing to learn more detail about the listing and add a trade request for one of your own listings.
5. Once both parties confirm the trade in the 'My Account>View Trade Requests', use the contact information provided to finalize the trade. 

## Docker Hub
[Docker Hub Image](https://hub.docker.com/r/sarahaltowaity1/bookshare)

## Digital Ocean
[Deployed Link](https://bookshares-app-ap28r.ondigitalocean.app/)

## Code Coverage
```txt
Name                    Stmts   Miss  Cover
-------------------------------------------
app/app.py                267     43    84%
app/gridfs_helper.py       23     17    26%
app/tests/__init__.py       0      0   100%
app/tests/conftest.py      17      0   100%
app/tests/test_app.py     284      0   100%
-------------------------------------------
TOTAL                     591     60    90%
```

## Authors

[Sarah Al-Towaity](https://github.com/sarah-altowaity1) \
[Rachel Andoh](https://github.com/rachel0lehcar) \
[Brian Lee](https://github.com/shl622) \
[Danilo Montes](https://github.com/danilo-montes) \
[Bhavig Pointi](https://github.com/bpointi) \
[Misha Seo](https://github.com/mishaseo)

## **DISCLAIMER**
On the Digital Ocean deployment, the site sometimes gives a page saying that you are unauthorized to view that page.
However, if you wait a bit and refresh, it will let you through.
We believe this to be an issue on Digital Ocean's part, possibly a slow handling of flask user authentication that causes the site to not load the user's 'logged in' status quickly enough.
This issue appears sometimes, and other times doesn't.
We tried to fix it but since it seems to be an issue with Digital Ocean itself, approaching a fix proved difficult.