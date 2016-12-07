from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import cast,Date, and_,or_
import config
from datetime import date, datetime
from database import match
from flask import Flask, render_template
app = Flask(__name__)
app.secret_key = '32190*!@jkfgsd;p2'
app.config.from_object(config.Database)
db = SQLAlchemy(app)

dllm = db.session.query(match).filter(cast(match.datetime,Date) >= date.today()).order_by(match.datetime).all()
nipftw = db.session.query(match).filter(and_(or_(match.teamA=='NiP',match.teamB=='NiP'),match.datetime>datetime.now())).order_by(match.datetime).all()

@app.route('/')
def index():
    return render_template("index.html", matches=dllm)

@app.route("/nip")
def nip():
    return render_template("nip.html", matches=nipftw)

if __name__ == '__main__':
    app.run(debug=True)
