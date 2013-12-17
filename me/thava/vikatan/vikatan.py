'''
Created on May 2, 2013

@author: thava
'''

import urllib2
import smtplib
from bs4 import BeautifulSoup, SoupStrainer
import sqlite3 as lite
import argparse

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from mechanize import Browser
import datetime


class Vikatan:
        URL = "http://www.vikatan.com/new/magazine.php?module=magazine&mid=1"
        efrom = "thavanathan@global-analytics.com"
        eto = "thavanathan.t@gmail.com"
        content = ""
        username = "thavanathan.t@gmail.com"
        password = ""
        
        magz = ['http://www.vikatan.com/new/magazine.php?module=magazine&mid=1',]
#                 'http://www.vikatan.com/new/magazine.php?module=magazine&mid=2',
#                 'http://www.vikatan.com/new/magazine.php?module=magazine&mid=3',
#                 'http://www.vikatan.com/new/magazine.php?module=magazine&mid=6',
#                 'http://www.vikatan.com/new/magazine.php?module=magazine&mid=7',
#                 'http://www.vikatan.com/new/magazine.php?module=magazine&mid=17']
        namez = ['ananda vikatan',]
#                  'junior vikatan',
#                  'aval vikatan',
#                  'nanayam vikatan',
#                  'motor vikatan',
#                  'doctor vikatan']
    
        def __init__(self):
            self.parse_args()
            self.con = lite.connect('vikatan.lite')
            self.cur = self.con.cursor()
            self._browser = Browser()
            self._login()
        
        def _closedb(self):
            """Close connection when the program exits."""
            self.con.close()
            
        def parse_vikatan(self, name, home_response):
#                print home_response
                for link in BeautifulSoup(home_response, parse_only=SoupStrainer('a')):
                        if link.has_attr('href') and link['href'].find('article.php') != -1 and link['href'].find('news.vikatan.com') == -1:
                                url = link['href']
                                print name, url
                                self.read_and_send_article(name, url)
                
        def parse_args(self):
            help_text = """This program fetches articles from vikatan.com and emails the articles."""
            parser = argparse.ArgumentParser(add_help=help_text)
            parser.add_argument("-u", "--username", required=True)
            parser.add_argument("-p", "--password", required=True)
            
            parser.add_argument("-eu", "--email", required=True)
            parser.add_argument("-ep", "--emailpassword", required=True)
            
            self.args = vars(parser.parse_args())
              
        def main(self):
            for name, link in zip(self.namez, self.magz):
                    ur = urllib2.urlopen(link)
                    content = ur.read()
                    self.parse_vikatan(name, content)
            self.cur.close()
            self.con.close()
        
        def _login(self):
                self._browser.open(self.URL)
                self._browser.select_form(nr=2)
                self._browser.form['user_id'] = self.args['username']
                self._browser.form['password'] = self.args['password']
                # logger.debug(self._browser.form)
                self._browser.submit()      
                                
                                
        def _isdup(self, down_link):
            max_days = 30
            min_date = datetime.datetime.now() - datetime.timedelta(max_days)
            query = "select article_id, link from articles where date > '%s'" %(min_date)
            self.cur.execute(query)
            result_set = self.cur.fetchall()
            for record in result_set:
                if record == down_link:
                    return True
            return False
        
        def read_and_send_article(self, name, url):
            if self._isdup(url):
                print "duplicate url: ", url
                return;
            
            query = "insert into articles values (null, '%s', %s, %s, datetime('now', 'localtime'));" %(url, 0, 0)
            self.cur.execute(query)
            
            query = "select article_id from articles where link = '%s'" %(url)
            self.cur.execute(query)
            article_id = self.cur.fetchone()[0]
            
            content = self._browser.open(url).read()           
            soup = BeautifulSoup(content)
            
            article = soup.find("div", {"class":"art_content"})
            self.cur.execute("update articles set downloaded = 1, date = datetime('now', 'localtime') where article_id=%s" %(article_id))
            server = smtplib.SMTP("smtp.office365.com:587")
            server.starttls()
            server.login(self.args['email'], self.args['emailpassword'])
            
            msg = MIMEMultipart("alternative")
            msg['Subject'] = "[" + name + "] " + soup.title.string
            msg['To'] = self.args['email']
            part1 = MIMEText('text', 'plain')
            part2 = MIMEText(str(article), 'html')
            msg.attach(part1)
            msg.attach(part2)
            server.sendmail(self.args['email'], self.args['email'], msg.as_string())
            server.quit()
            self.cur.execute("update articles set sent=1 , date = datetime('now', 'localtime') where article_id=%s" %(article_id))
                
if __name__ == '__main__':
    Vikatan().main()
