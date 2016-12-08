import config, bcrypt
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from database import match,Twitchvod, parseTwitchs,User
from sqlalchemy.sql import and_
from bs4 import BeautifulSoup as btf





engine = create_engine(URL(**config.DATABASE))
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()



