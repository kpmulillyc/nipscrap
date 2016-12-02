from bs4 import BeautifulSoup as btf
import urllib,config
from urllib import request
from dateutil.parser import parse
from pytz import timezone
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import String,Column,Integer,DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL


engine = create_engine(URL(**config.DATABASE))
url = "http://www.hltv.org/matches/"
req = urllib.request.Request(url)
req.add_header('User-Agent', 'Mozilla/5.0')
read = urllib.request.urlopen(req).read().decode('utf-8')
soup = btf(read,"lxml")
matches = soup.find_all("div",class_="matchListRow")
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

class match(Base):
    __tablename__ = 'cs'
    id = Column(Integer,primary_key=True)
    teamA = Column(String(100))
    ALogo = Column(String(100))
    teamB = Column(String(100))
    BLogo = Column(String(100))
    datetime = Column(DateTime)
    link = Column(String(200))
    status = Column(String(20))
    def __init__(self,id, teamA, ALogo, teamB, BLogo, date, time, link, status):
        self.id = id
        self.teamA = teamA
        self.ALogo = ALogo
        self.teamB = teamB
        self.BLogo = BLogo
        self.datetime = hkt(date,time)
        self.link = tohttp(link)
        self.status = status


for team in matches:
    try:
        a=team.find('div',class_='matchTeam1Cell').text.replace('\n','').replace(' ','')
        b=team.find('div',class_='matchTeam2Cell').text.replace('\n','').replace(' ','')
        c= team.find('div',class_='matchTimeCell').text
        aLogo = team.find('div',class_='matchTeam1Cell').find('img').get('src')
        bLogo = team.find('div',class_='matchTeam2Cell').find('img').get('src')
        d = team.find('div',class_='matchActionCell').a
        link = d.get('href')
        id = d.get('href').split('/')[2].split('-')[0]
        date = str(team.parent.find_previous('div', class_='matchListDateBox').text)
        e = team.find('div',class_='matchScoreCell').text.replace('\n','').replace(' ','').replace('vs','')
        check = session.query(match).filter_by(id=id).first()
        if check:
            pass
        else:
            mat = match(id,a,aLogo,b,bLogo,date,c,link,status='None')
            session.add(mat)
    except:
        pass

session.commit()

