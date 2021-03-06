from flask import Flask, flash, render_template, redirect, request, session, json
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
import sqlite3 as sql
from flask_session import Session
from tempfile import mkdtemp
from functools import wraps
import os

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))


#configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

#add function to connect to getbase and get back dictionary for each row
def get_db():
    conn = sql.connect(os.path.join(THIS_FOLDER, 'climbs.db'))
    conn.row_factory = sql.Row
    return conn

# Configure session to use filesystem (instead of signed cookies)
#app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#function to ensure login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

#Climbing difficulty scale conversion: https://www.rei.com/learn/expert-advice/climbing-bouldering-rating.html
grades = ["5.7", "5.8", "5.9", "5.10a", "5.10b", "5.10c", "5.10d", "5.11a", "5.11b", "5.11c", "5.11d", 
"5.12a", "5.12b", "5.12c", "5.12d", "5.13a", "5.13b"]

boulders = ["NA", "VB", "V0", "NA", "NA", "V1", "NA", "V2", "V3", "NA", "NA", "V4", "V5", "V6", "NA", "V7", "V8"]



#welcome page
@app.route('/', methods = ['GET', 'POST'])
def login():
    #forget old user id
    session.clear()

    if request.method == "GET":
        return render_template("login.html")

    else: 
        user_name = request.form.get('username')

        conn = get_db()
        rows = conn.execute('SELECT * FROM users WHERE username = ?', (user_name, )).fetchall()
        conn.close()

        #check that username is valid
        if len(rows) != 1: 
            error = 'Not a User. Please create username using the new user box'
            return render_template("login.html", error = error)
        
        #remember which user logged in
        session['user_id'] = rows[0]['user_id']
    
        #redirect user to main page
        return redirect("/homepage")


@app.route("/register", methods = ['GET', 'POST'])
def register():
    if request.method == "GET":
        return render_template("login.html")
    
    else:
        name = request.form.get('username')
        if not name:
            error = "Please enter a name."
            return render_template("login.html", error = error)

        conn = get_db()
        rows = conn.execute("SELECT username FROM users").fetchall()
        conn.close()

        #see if the name is already taken
        for row in rows:
            if name == row['username']:
                error = "Username already taken. Please enter another name."
                return render_template("login.html", error = error) #add error message - username already taken

        #if the name is free, add it to the database and redirect user to login
        conn = get_db()
        conn.execute("INSERT INTO users (username) VALUES (?)", (name, ))
        conn.commit()
        conn.close()
        return redirect("/")

        


#main page - for indoor climbs
@app.route("/homepage", methods =['GET', 'POST'])
@login_required
def homepage():

    user = session['user_id']

    if request.method == "POST":
        send_type = request.form.get('send_type')
        grade = request.form.get('grade')
        type = request.form.get('type')
        date = request.form.get('date')
        number = request.form.get('num_routes')

        if not number or not date:
            flash("missing date or number of routes")
            return redirect("/homepage")

        if int(number) <= 0:
            flash("Enter a positive integer for routes")
            return redirect("/homepage")

        conn = get_db()
        #add new climb to DB
        conn.execute("INSERT INTO indoor (user_id, date, grade, type, num_routes, send_type) VALUES (?, ?, ?, ?, ?, ?)", (user, date, grade, type, number, send_type))
        conn.commit()
        conn.close()

        return redirect("/homepage")

    #Reached via GET
    else:
        conn = get_db()
        #get username
        users = conn.execute("SELECT username FROM users WHERE user_id = ?", (user, )).fetchall()
        person = users[0]['username']

        #get chart data for total climbs chart
        chart_rows = conn.execute("SELECT date, SUM(num_routes) FROM indoor WHERE user_id = ? GROUP BY date", (user,) ).fetchall()

        #get chart data for max climbs chart
        max_chart_rows = conn.execute("SELECT date, grade, type, send_type FROM indoor WHERE user_id = ?",(user,) ).fetchall()

        #Transform data to json
        object_list = []
        for row in chart_rows:
            d = {}
            d['date'] = row[0]
            d['routes'] = row[1]
            object_list.append(d)

        #transform data for max difficulty chart
        max_list = []
        for row in max_chart_rows:
            d = {}
            d['date'] = row[0]
            d['grade'] = row[1]
            d['type'] = row[2]
            d['sendType'] = row[3]
            if row[2] == "boulder":
                d['difficulty'] = boulders.index(row[1])
            else:
                d['difficulty'] = grades.index(row[1])
            max_list.append(d)

        

        return render_template('index.html', person = person, chart_data = object_list, max_data = max_list)


#outdoor climbs page
@app.route("/outdoor", methods = ['GET', 'POST'])
@login_required
def outdoor():
    user = session['user_id']

    if request.method == "POST":
        send_type = request.form.get('send_type')
        grade = request.form.get('grade')
        type = request.form.get('type')
        date = request.form.get('date')
        name = request.form.get('route_name')
        location = request.form.get('location')
        height = request.form.get('height')
        pitches = request.form.get('pitches')

        if not name or not location or not date or not height or not pitches: 
            flash("Missing information. Try again.")
            return redirect("/outdoor")

        if int(height) <= 0:
            flash("Enter a positive integer for height")
            return redirect("/outdoor")

        if int(pitches) <= 0:
            flash("Enter a positive integer for height")
            return redirect("/outdoor")

        conn = get_db()
        #add new climb to DB
        conn.execute("INSERT INTO outdoor (user_id, date, grade, name, location, height, pitches, type, send_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (user, date, grade, name, location, height, pitches, type, send_type))
        conn.commit()
        conn.close()

        return redirect("/outdoor")
    
    else:
        conn = get_db()
        #get all climbs in DB to pass to html
        rows = conn.execute('SELECT * FROM outdoor WHERE user_id = ?', (user,) ).fetchall()
        users = conn.execute("SELECT username FROM users WHERE user_id = ?", (user, )).fetchall()
        person = users[0]['username']
        conn.close()

        new_list = []
        for row in rows:
            d = {}
            d['grade'] = row[2]
            d['name'] = row[3]
            d['location'] = row[4]
            d['height'] = row[5]
            d['pitches'] = row[6]
            d['type'] = row[7]
            d['send_type'] = row[8]
            if row[7] == "boulder":
                d['difficulty'] = boulders.index(row[2])
            else:
                d['difficulty'] = grades.index(row[2])
            new_list.append(d)

        print(new_list)
        return render_template('outdoor.html', person = person, rows = rows, data = new_list)

#history page with full table
@app.route("/history")
@login_required
def history():

    user = session['user_id']

    #get all indoor climbs in DB to pass to html
    conn = get_db()
    rows = conn.execute('SELECT rowid, * FROM indoor WHERE user_id = ?', (user,) ).fetchall()
    conn.close()

    return render_template("history.html", rows = rows)

#delete rows from history table
@app.route("/delete", methods = ['POST'])
def delete():
    list = request.form.getlist('delete')
    print(list)

    conn = get_db()
    for climb in list:
        conn.execute("DELETE FROM indoor WHERE rowid = ?", (climb,))
    conn.commit()
    conn.close()

    return redirect("/history")


@app.route("/logout")
def logout():
    #end session and return to login page
    session.clear()
    return redirect("/")


        



    
