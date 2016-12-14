from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import cast,Date, and_,or_
import config, bcrypt,subprocess
from datetime import date, datetime,timedelta
from database import match, User, Twitchvod
from flask import Flask, render_template, request, redirect
from flask_login import LoginManager, login_user, logout_user
from flask_apscheduler import APScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from bs4 import BeautifulSoup as btf

class APconfig(object):
    SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(url=config.dburl)
    }
    SCHEDULER_EXECUTORS = {
        'default': {'type': 'processpool', 'max_workers': 5}
    }

app = Flask(__name__)
app.secret_key = '32190*!@jkfGsd;p2'
app.config.from_object(APconfig())
sched = APScheduler()
sched.init_app(app)
sched.start()
lm = LoginManager()
app.config.from_object(config.Database)
db = SQLAlchemy(app)
lm.init_app(app)

def bigJob(matchid):
    getmatch = db.session.query(match).filter_by(id=matchid).first()
    sched.add_job(func=recordTwitch,args=[getmatch.id],trigger='date', run_date=getmatch.datetime,  id=(str(matchid)+' record'))
    getmatch.status = '<font color="orange">Pending</font>'
    db.session.commit()

def recordTwitch(matchid):
    getmatch = db.session.query(match).filter_by(id=matchid).first()
    link = getmatch.link
    getvod = db.session.query(Twitchvod).filter_by(matchid=matchid).first()
    twitchlink = getvod.link
    sched.add_job(func=checkLive, trigger='interval', minutes=5, id=(str(matchid) + ' isLive'), args=[link, matchid])
    getmatch.status = '<font color="red">Recording</font>'
    db.session.commit()
    cmd = ["streamlink -o '/media/kpmu/data/owncloud/kpmulillyc/files/CS/UN-%s VS %s %s.mp4' %s best" % (getmatch.teamA,getmatch.teamB,getmatch.event, twitchlink)]
    subprocess.call(cmd, shell=True)

def checkLive(link,matchid):
    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = (
        'Mozilla/5.0 (Linux; U; Android 4.0.3; ko-kr; LG-L160L Build/IML74K) AppleWebkit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30')
    driver = webdriver.PhantomJS(desired_capabilities=dcap, service_log_path='/home/kpmu/ghostdriver.log')
    driver.get(link)
    html = driver.page_source
    soup = btf(html, 'lxml')
    time = soup.find('span', id='time').text
    driver.close()
    if time == 'Match over':
        subprocess.call('pkill streamlink', shell=True)
        sched.delete_job(str(matchid) + ' isLive')
        getmatch = db.session.query(match).filter_by(id=matchid).first()
        getmatch.status = '<font color="green">Done</font>'
        db.session.commit()

@lm.user_loader
def user_loader(user_id):
    return db.session.query(User).filter_by(id=user_id).first()

@app.route('/')
def index():
    dllm = db.session.query(match).filter(cast(match.datetime, Date) >= date.today()).order_by(match.datetime).all()
    return render_template("index.html", matches=dllm,checknow=datetime.now())

@app.route("/nip")
def nip():
    nipftw = db.session.query(match).filter(
        and_(or_(match.teamA == 'NiP', match.teamB == 'NiP'), match.datetime > datetime.now())).order_by(
        match.datetime).all()
    return render_template("nip.html", matches=nipftw,checknow=datetime.now())

@app.route("/today")
def today():
    onlytoday = db.session.query(match).filter(
        and_(cast(match.datetime, Date) == date.today(), match.datetime > datetime.now())).order_by(
        match.datetime).all()
    return render_template("today.html", matches=onlytoday,checknow=datetime.now())

@app.route("/past")
@app.route('/past/<datet>')
def past(datet = date.today() - timedelta(days=1)):
    pastt = db.session.query(match).filter(cast(match.datetime,Date)==datet).order_by(match.datetime).all()
    return render_template("past.html", matches=pastt,checknow=datetime.now())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    username = request.form['username']
    user = user_loader(username)
    if user is not None and bcrypt.checkpw(request.form['password'].encode('utf-8'),user.password.encode('utf-8')):
        login_user(user,remember=True)
        return redirect('/')
    return redirect("http://www.google.com")

@app.route('/record')
def record():
    matchid = request.args.get('matchid')
    bigJob(matchid)
    return ('', 204)

@app.route('/delete')
def delete():
    matchid = request.args.get('deid')
    matchid = matchid.replace('del','')
    sched.delete_job(matchid+' record')
    getmatch=db.session.query(match).filter_by(id=matchid).first()
    getmatch.status = '-'
    db.session.commit()
    return ('', 204)

@app.route('/pending')
def pending():
    penn = db.session.query(match).filter(or_(match.status=='<font color="orange">Pending</font>',match.status=='<font color="red">Recording</font>')).all()
    return render_template('pending.html',matches=penn,checknow=datetime.now())

@app.route('/done')
def done():
    donee = db.session.query(match).filter_by(status='<font color="green">Done</font>').all()
    return render_template('pending.html',matches=donee,checknow=datetime.now())

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=False,use_reloader=False)
