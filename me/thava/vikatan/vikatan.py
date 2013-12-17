'''
Created on May 2, 2013

@author: thava
'''

import urllib
import urllib2
import smtplib
import BeautifulSoup as bs
import sqlite3 as lite

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from BeautifulSoup import BeautifulSoup, SoupStrainer
import httplib
from mechanize import Browser


class Vikatan:
        URL = "http://www.vikatan.com/new/magazine.php?module=magazine&mid=1"
        efrom = "thavanathan.t@gmail.com"
        eto = "thavanathan.t@gmail.com"
        content = ""
        username = "thavanathan.t@gmail.com"
        password = ""
        
        magz = ['http://www.vikatan.com/new/magazine.php?module=magazine&mid=1',
                'http://www.vikatan.com/new/magazine.php?module=magazine&mid=2',
                'http://www.vikatan.com/new/magazine.php?module=magazine&mid=3',
                'http://www.vikatan.com/new/magazine.php?module=magazine&mid=6',
                'http://www.vikatan.com/new/magazine.php?module=magazine&mid=7',
                'http://www.vikatan.com/new/magazine.php?module=magazine&mid=17']
        namez = ['ananda vikatan',
                 'junior vikatan',
                 'aval vikatan',
                 'nanayam vikatan',
                 'motor vikatan',
                 'doctor vikatan']
    
        def __init__(self):
            self.con = lite.connect('vikatan.lite')
            self.cur = self.con.connect();
        
        def _closedb(self):
            """Close connection when the program exits."""
            self.con.close()
            
        def parse_vikatan(self, name, home_response):
#                print home_response
                for link in BeautifulSoup(home_response, parseOnlyThese=SoupStrainer('a')):
                        if link.has_key('href') and link['href'].find('article.php') != -1 and link['href'].find('news.vikatan.com') == -1:
                                url = link['href']
                                print name, url
                                self.read_and_send_article(name, url)
                
        def __init__(self):
                self._browser = Browser()
                self._login()
        
        def main(self):
                for name, link in zip(self.namez, self.magz):
                        ur = urllib2.urlopen(link)
                        content = ur.read()
                        self.parse_vikatan(name, content)
                return
        
        def _login(self):
                username = 'thavanathan.t@gmail.com'
                password = ''
                self._browser.open(self.URL)
                self._browser.select_form(nr=2)
                self._browser.form['user_id'] = username
                self._browser.form['password'] = password
                # logger.debug(self._browser.form)
                self._browser.submit()      
                                
        def read_and_send_article(self, name, url):
                f = open("Vikatan.txt", "r")
                sent_articles = f.readlines()
                f.close()
                if url + '\n' in sent_articles:
                        return

                content = self._browser.open(url).read()           
                soup = bs.BeautifulSoup(content)
                
                article = soup.find("div", {"class":"art_content"})
                server = smtplib.SMTP("smtp.gmail.com:587")
                server.starttls()
                server.login(self.username, self.password)
                
                msg = MIMEMultipart("alternative")
                msg['Subject'] = "[" + name + "] " + soup.title.string
                msg['To'] = "thavanathan.t@gmail.com"
                part1 = MIMEText('text', 'plain')
                part2 = MIMEText(str(article), 'html')
                msg.attach(part1)
                msg.attach(part2)
                server.sendmail(self.efrom, self.eto, msg.as_string())
                server.quit()
                f = open("Vikatan.txt", "a")
                f.write(url + '\n')
                f.close()
                
                
                
if __name__ == '__main__':
    Vikatan().main()
