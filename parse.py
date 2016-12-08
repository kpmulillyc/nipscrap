from bs4 import BeautifulSoup as btf
import config
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
import requests
from database import match, parseTwitchs,tohttp, Twitchvod
from sqlalchemy.orm import sessionmaker

engine = create_engine(URL(**config.DATABASE))
url = "http://www.hltv.org/matches/"
hh = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1'}
read = requests.get(url, headers=hh)
soup = btf(read.text,"lxml")
matches = soup.find_all("div",class_="matchListRow")
Session = sessionmaker(bind=engine)
session = Session()
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
        e = team.find('div',class_='matchScoreCell').text.replace('\n','').replace('vs','')
        check = session.query(session.query(match).filter_by(id=id).exists()).scalar()
        checkvod = session.query(session.query(Twitchvod).filter_by(matchid=id).exists()).scalar()
        TBA = session.query(match).filter_by(id=id).first()
        if check is False:
            mat = match(id, a, aLogo, b, bLogo, e, date, c, link, status='-')
            session.add(mat)
            session.commit()
            parseTwitchs(id, tohttp(link))
        elif check is True and 'TBA' in TBA.gameType:
            TBA.gameType = e
            session.commit()
        if checkvod is False:
            parseTwitchs(id, tohttp(link))
    except:
        pass

