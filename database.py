from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import String,Column,Integer,DateTime,create_engine,ForeignKey, Boolean
from dateutil.parser import parse
from pytz import timezone
import config
from sqlalchemy.engine.url import URL
from bs4 import BeautifulSoup as btf
from sqlalchemy.orm import sessionmaker,relationship
import requests, bcrypt


mheaders = {'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.0.3; ko-kr; LG-L160L Build/IML74K) AppleWebkit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30'}
engine = create_engine(URL(**config.DATABASE))
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

def tohttp(link):
    baseurl = 'http://hltv.org'
    link = '%s%s' % (baseurl,link)
    return link

def hkt(date, time):
    oridate = parse('%s %s:00' % (date, time))
    coptz = timezone('Europe/Copenhagen')
    coptime = coptz.localize(oridate)
    hktz = timezone('Asia/Hong_Kong')
    hktime = coptime.astimezone(hktz)
    return hktime

def parseEvent(link):
    read = requests.get(link,headers=mheaders)
    soup = btf(read.text, "lxml")
    event = soup.find_all('span', class_='label-primary label')[1]
    return event.text

class match(Base):
    __tablename__ = 'cs'
    id = Column(Integer,primary_key=True)
    teamA = Column(String(100))
    ALogo = Column(String(100))
    teamB = Column(String(100))
    BLogo = Column(String(100))
    gameType = Column(String(50))
    datetime = Column(DateTime)
    link = Column(String(200))
    event = Column(String(100))
    status = Column(String(100))
    score = Column(String(10))
    twitchvods = relationship('Twitchvod',backref='match', lazy='subquery')
    def __init__(self,id, teamA, ALogo, teamB, BLogo,gameType, date, time,link, status):
        self.id = id
        self.teamA = teamA
        self.ALogo = ALogo
        self.teamB = teamB
        self.BLogo = BLogo
        self.gameType = gameType
        self.datetime = hkt(date,time)
        self.link = tohttp(link)
        self.event = parseEvent(self.link)
        self.status = status

class Twitchvod(Base):
    __tablename__='twitchvod'
    id = Column(Integer,primary_key=True)
    title = Column(String(50))
    link = Column(String(100))
    matchid= Column(Integer,ForeignKey('cs.id'))
    def __init__(self,title,link,matchid):
        self.title = title
        self.link = link
        self.matchid = matchid

def parseTwitchs(matchid, url):
    read = requests.get(url, headers=mheaders)
    soup = btf(read.text, "lxml")
    details = soup.find('div', class_='panel panel-primary').find_all('a')
    for i in details:
        if i.get('title') is not None:
            link = i.get('href')
            if link[0] == '/':
                link = 'http://hltv.org'+link
            vod = Twitchvod(i.get('title'), link, matchid)
            session.add(vod)
            session.commit()

def addVod(matchid,url):
    findl = session.query(Twitchvod).filter_by(matchid=matchid).all()
    read = requests.get(url, headers=mheaders)
    soup = btf(read.text, "lxml")
    details = soup.find('div', class_='panel panel-primary').find_all('a')
    for i in details:
        if i.get('title') is not None:
            if i.get('href') not in [u.link for u in findl]:
                link = i.get('href')
                if link[0] == '/':
                    link = 'http://hltv.org' + link
                vod = Twitchvod(i.get('title'), link, matchid)
                session.add(vod)
                session.commit()



class User(Base):
    __tablename__ = 'user'
    id = Column(String(10), primary_key=True)
    password = Column(String(100))
    def __init__(self,id,password):
        self.id = id
        hashed = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())
        self.password = hashed
    def is_authenticated(self):
        return True
    def is_active(self):
        return True
    def is_anonymous(self):
        return False
    def get_id(self):
        return self.id

if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)