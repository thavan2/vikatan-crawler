'''
Created on May 2, 2013

@author: thava
'''

import urllib2
import smtplib
import time
import sqlite3 as lite
import argparse

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from mechanize import Browser
import datetime

import vconf


class Vikatan:
    content = ""

    magz = [
        'http://www.vikatan.com/new/magazine.php?module=magazine&mid=1',
        'http://www.vikatan.com/new/magazine.php?module=magazine&mid=2',
        'http://www.vikatan.com/new/magazine.php?module=magazine&mid=3',
        'http://www.vikatan.com/new/magazine.php?module=magazine&mid=6',
        'http://www.vikatan.com/new/magazine.php?module=magazine&mid=7',
        'http://www.vikatan.com/new/magazine.php?module=magazine&mid=17'
    ]
    namez = [
        'ananda vikatan',
        'junior vikatan',
        'aval vikatan',
        'nanayam vikatan',
        'motor vikatan',
        'doctor vikatan'
    ]

    def __init__(self):
        self.email_server = None
        self.articles = []
        self.con = lite.connect(vconf.SQLITE_PATH)
        self.cur = self.con.cursor()
        self._browser = Browser()

        self._login()

    def _init_mail_server(self):
        print "logging in to email server..."
        self.email_server = smtplib.SMTP(vconf.SMTP_SERVER, vconf.SMTP_PORT)
        self.email_server.starttls()
        self.email_server.login(vconf.SMTPS_USERNAME, vconf.SMTPS_PASSWORD)

    def _get_links(self, html):
        links = []
        for token in html.split('"') + html.split("'"):
            if token.startswith("http") and "article" in token and "news" not in token \
                    and "mid" not in token and ".css" not in token:
                links.append(token)
        print links
        return set(links)

    def parse_vikatan(self, name, home_response):
        # print name, home_response
        for url in self._get_links(home_response):
            print name, url
            self.read_article(name, url)
            time.sleep(0.5)

        for item in self.articles:
            self.send_article(item[1], item[2], item[3])
            self.send_update(item[0])
            time.sleep(0.5)  # to avoid google blocking connections.
        self.articles = []

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
            self._init_mail_server()
            ur = urllib2.urlopen(link)
            content = ur.read()
            self.parse_vikatan(name, content)
            self.close_mail_server()
        self.cur.close()
        self.con.close()


    def _login(self):
        print "Logging into vikatan"
        self._browser.open(vconf.VIKATAN_LOGIN_URL)
        self._browser.select_form(nr=1)
        self._browser.form['user_id'] = vconf.VIKATAN_USERNAME
        self._browser.form['password'] = vconf.VIKATAN_PASSWORD
        # logger.debug(self._browser.form)
        self._browser.submit()
        print "login succesfull"

    def _isdup(self, down_link):
        max_days = 30
        min_date = datetime.datetime.now() - datetime.timedelta(max_days)
        query = "select article_id, link from articles where sent=1 and date > '%s'" % (min_date)
        print query
        self.cur.execute(query)
        result_set = self.cur.fetchall()
        for record in result_set:
            if record[1] == down_link:
                return True
        return False

    def close_mail_server(self):
        self.email_server.quit()

    def send_article(self, magazine, title, mail_content):
        print "sending article...", magazine, title
        msg = MIMEMultipart("alternative")
        msg['Subject'] = "[" + magazine + "] " + title
        msg['To'] = vconf.EMAIL_TO
        part1 = MIMEText('text', 'plain')
        part2 = MIMEText(str(mail_content), 'html')
        msg.attach(part1)
        msg.attach(part2)
        self.email_server.sendmail(vconf.EMAIL_FROM, vconf.EMAIL_TO, msg.as_string())
        print "mail sent successful..."

    def send_update(self, article_id):
        self.cur.execute(
            "update articles set sent=1 , date = datetime('now', 'localtime') where article_id=%s" % (article_id))
        self.con.commit()

    def read_article(self, name, url):
        if self._isdup(url):
            print "Not reading duplicate url: ", url
            return
        print "Not a dedup url"

        query = "insert into articles values (null, '%s', %s, %s, datetime('now', 'localtime'));" % (url, 0, 0)
        self.cur.execute(query)

        query = "select article_id from articles where link = '%s'" % (url)
        self.cur.execute(query)
        article_id = self.cur.fetchone()[0]

        content = self._browser.open(url).read()
        startindex = content.find('<div class="art_content">')
        print startindex
        endindex = content.find('<div class="cmt-link">')
        print endindex
        article = "<html><body>" + content[startindex: endindex] + "</body></html>"

        self.cur.execute(
            "update articles set downloaded = 1, date = datetime('now', 'localtime') where article_id=%s" % (
            article_id))
        title = content[content.find("<title>") + 7: content.find("</title>")]
        self.articles.append([article_id, name, title, article])
        print len(self.articles)


if __name__ == '__main__':
    Vikatan().main()
