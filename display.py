from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import cast,Date, and_,or_
import config, bcrypt,subprocess,requests,re
from datetime import date, datetime,timedelta
from database import match, User
from flask import Flask, render_template, request, redirect
from flask_login import LoginManager, login_user, logout_user
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from bs4 import BeautifulSoup as btf
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler


app = Flask(__name__)
app.secret_key = 'jdkljsalkd&#@!Ksdapg'
lm = LoginManager()
app.config.from_object(config.Database)
db = SQLAlchemy(app)
lm.init_app(app)
jobstores = {
    'default': SQLAlchemyJobStore(url=config.dburl)
}
executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}
sched = BackgroundScheduler(jobstores=jobstores, job_defaults=job_defaults,executors=executors)

def bigJob(matchid):
    getmatch = db.session.query(match).filter_by(id=matchid).first()
    sched.add_job(func=recordTwitch,args=[getmatch.id],trigger='date', run_date=getmatch.datetime,  id=(str(matchid)+' record'),executor='processpool')
    getmatch.status = '<font color="orange">Pending</font>'
    db.session.commit()

def recordTwitch(matchid):
    getmatch = db.session.query(match).filter_by(id=matchid).first()
    link = getmatch.link
    mheaders = {'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.0.3; ko-kr; LG-L160L Build/IML74K) AppleWebkit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30'}
    read = requests.get(link, headers=mheaders)
    soup = btf(read.text, "lxml")
    vodlink = soup.find('div', class_='panel-heading', string=re.compile('Streams')).find_next('a')
    sched.add_job(func=checkLive, trigger='interval', minutes=5, id=(str(matchid) + ' isLive'), args=[link, matchid],replace_existing=True,executor='default')
    getmatch.status = '<font color="red">Recording</font>'
    db.session.commit()
    cmd = ["streamlink -o '%s/UN %s VS %s %s.mp4' %s best" % (config.cspath,getmatch.teamA,getmatch.teamB,
                                                          getmatch.event, vodlink)]
    subprocess.call(cmd, shell=True)

def checkLive(link,matchid):
    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = (
        'Mozilla/5.0 (Linux; U; Android 4.0.3; ko-kr; LG-L160L Build/IML74K) AppleWebkit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30')
    driver = webdriver.PhantomJS(executable_path=config.homepath+'/phantomjs/bin/phantomjs',desired_capabilities=dcap, service_log_path=config.homepath+'/ghostdriver.log')
    driver.get(link)
    html = driver.page_source
    driver.quit()
    soup = btf(html, 'lxml')
    try:
        time = soup.find('span', class_="label-danger label").text
        if time == 'Match over':
            subprocess.call('pkill streamlink', shell=True)
            sched.remove_job(str(matchid) + ' isLive')
            getmatch = db.session.query(match).filter_by(id=matchid).first()
            getmatch.status = '<font color="green">Done</font>'
            db.session.commit()
    except:
        pass


sched.start()

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
    sched.remove_job(matchid+' record')
    getmatch=db.session.query(match).filter_by(id=matchid).first()
    getmatch.status = '-'
    db.session.commit()
    return ('', 204)

@app.route('/stop')
def stop():
    matchid = request.args.get('stopid')
    matchid = matchid.replace('del','')
    cmd = ['pkill streamlink']
    subprocess.call(cmd,shell=True)
    sched.remove_job(matchid + ' isLive')
    getmatch = db.session.query(match).filter_by(id=matchid).first()
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
