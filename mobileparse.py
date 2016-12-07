import config
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from database import match,Twitchvod, parseTwitchs
from sqlalchemy.sql import and_
from bs4 import BeautifulSoup as btf





engine = create_engine(URL(**config.DATABASE))
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

test = session.query(match).filter(match.teamA=="LDLC").first()
parseTwitchs(test.id,test.link)