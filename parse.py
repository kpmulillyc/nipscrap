from bs4 import BeautifulSoup as btf
import config,requests
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL
from database import match


engine = create_engine(URL(**config.DATABASE))
url = "http://www.hltv.org/matches/"
pcheaders={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1'}
mheaders={'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.0.3; ko-kr; LG-L160L Build/IML74K) AppleWebkit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30'}
req = requests.get(url,headers=pcheaders)
soup = btf(req.text,"lxml")
matches = soup.find_all("div",class_="matchListRow")
Base = declarative_base()
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
        event = link.split(b.lower())[-1].replace('-',' ')
        id = d.get('href').split('/')[2].split('-')[0]
        date = str(team.parent.find_previous('div', class_='matchListDateBox').text)
        e = team.find('div',class_='matchScoreCell').text.replace('\n','').replace('vs','')
        check = session.query(match).filter_by(id=id).first()
        if check:
            pass
        else:
            mat = match(id,a,aLogo,b,bLogo,e,date,c,event,link,status='None')
            session.add(mat)
    except:
        pass

session.commit()

