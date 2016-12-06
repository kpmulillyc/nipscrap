from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import String,Column,Integer,DateTime,create_engine,ForeignKey
from sqlalchemy.orm import relationship
from dateutil.parser import parse
from pytz import timezone
import config
from sqlalchemy.engine.url import URL

#engine = create_engine(URL(**config.DATABASE))
Base = declarative_base()

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
    gameType = Column(String(50))
    datetime = Column(DateTime)
    event = Column(String(100))
    link = Column(String(200))
    status = Column(String(20))
    score = Column(String(10))
    twitchvods = relationship('Twitchvod',backref='match')
    def __init__(self,id, teamA, ALogo, teamB, BLogo,gameType, date, time,event, link, status):
        self.id = id
        self.teamA = teamA
        self.ALogo = ALogo
        self.teamB = teamB
        self.BLogo = BLogo
        self.gameType = gameType
        self.datetime = hkt(date,time)
        self.event = event
        self.link = tohttp(link)
        self.status = status

class Twitchvod(Base):
    __tablename__='twitchvod'
    id = Column(Integer,primary_key=True)
    link = Column(String(100))
    matchid= Column(Integer,ForeignKey('cs.id'))

#Base.metadata.create_all(bind=engine)