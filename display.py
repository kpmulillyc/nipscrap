from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import cast,Date, and_,or_
import config, bcrypt
from datetime import date, datetime
from database import match, User
from flask import Flask, render_template, request, redirect
from flask_login import LoginManager, login_user, logout_user

app = Flask(__name__)
app.secret_key = '32190*!@jkfgsd;p2'
lm = LoginManager()
lm.init_app(app)
app.config.from_object(config.Database)
db = SQLAlchemy(app)

dllm = db.session.query(match).filter(cast(match.datetime,Date) >= date.today()).order_by(match.datetime).all()
nipftw = db.session.query(match).filter(and_(or_(match.teamA=='NiP',match.teamB=='NiP'),match.datetime>datetime.now())).order_by(match.datetime).all()
onlytoday = db.session.query(match).filter(and_(cast(match.datetime,Date) == date.today(), match.datetime>datetime.now())).order_by(match.datetime).all()

@lm.user_loader
def user_loader(user_id):
    return db.session.query(User).get(user_id)


@app.route('/')
def index():
    return render_template("index.html", matches=dllm)

@app.route("/nip")
def nip():
    return render_template("nip.html", matches=nipftw)

@app.route("/today")
def today():
    return render_template("today.html", matches=onlytoday)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    username = request.form['username']
    pw = db.session.query(User).filter_by(id=username).first()
    exist = db.session.query(db.session.query(User).filter_by(id=username).exists()).scalar()
    if exist:
        if bcrypt.checkpw(request.form['password'].encode('utf-8'),pw.password.encode('utf-8')):
            login_user(pw,remember=True)
            return redirect('/')
        else:
            return redirect("http://www.google.com")
    else:
        return redirect("http://www.google.com")

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=False)
