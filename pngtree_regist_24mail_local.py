#coding:utf-8
import requests,urllib,urllib2,re,random,MySQLdb
from selenium import webdriver
from selenium.webdriver.common import keys

import time
from lxml import etree
class register():
    def __init__(self,url):
        self.url = url
        self.s = requests.session()
        self.db = MySQLdb.connect('localhost', 'root', '123456', 'pngtree_201712')
        self.cursor = self.db.cursor()
    def send_mail(self,data):
        username = data[1]
        email = data[2].split('@')[0] +'@027168.com'
        password = data[3]
        # 创造一个浏览器
        browser1 = webdriver.PhantomJS(executable_path=r"/Users/qiyue/myxuni/phantomjs-2.1.1/bin/phantomjs",)  # //内核 webkkit
        browser1.get('https://pngtree.com/')
        browser1.find_element_by_id('base-public-register-button').click()
        # print browser.page_source
        browser1.find_element_by_id('base-public-login-username-regiser-text').send_keys(username)
        browser1.find_element_by_id('base-public-login-email-regiser-text').send_keys(email)
        browser1.find_element_by_id('base-public-login-password-regiser-text').send_keys(password)
        browser1.find_element_by_id('base-sub-regist-Btn').click()
        time.sleep(5)
        browser1.quit()
        # browser1.close()
    '''根据数据库取出的数据,去注册一个邮箱'''
    def get_email(self,user_data):
        mail = user_data[2].split('@')[0]
        print mail
        email = mail + '@027168.com'
        # 注册一个新邮箱
        url = 'http://24mail.chacuo.net/'
        post_data = {
            'data':mail,
            'type':'set',
            'arg':'d=027168.com_f='
        }
        # try:
        self.s.get(url)
        res = self.s.post(url,data=post_data)
        # print res.text
        if '"info":"ok"' in res.text:
            print 'set Temp_mail Sucess! It is ',email
            return email
        else:
            print 'set Temp_mail Faild...'
            return False
        # except Exception as e:
        #     print str(e)
        #     print 'proxy May Disabled!'
        # 返回注册的邮箱
    '''获取pngtree的收件箱的地址'''
    def get_inbox(self,mail):
        mail_name = mail.split('@')[0]
        base_url = 'http://24mail.chacuo.net/'
        post_data = {
            'data': mail_name,
            'type': 'refresh',
            'arg':'',
        }
        inbox_text = self.s.post(base_url,data=post_data).text
        print inbox_text
        inbox_re = re.compile(r'pngtree<pngtree@email.pngtree.com>","SUBJECT":"E-mail verification","MID":(\w+),')
        inbox_href = re.search(inbox_re,inbox_text)
        if inbox_href:
            png_id = inbox_href.group(1)
            print 'get Png_uid Sucess!  It is ',png_id
            return png_id
        else:
            print 'inbox_href Match Faild'
            return False
    '''获取验证链接'''
    def get_feed_href(self,id,mail):
        mail_name = mail.split('@')[0]
        arg = 'f='+id
        post_data = {
            'data': mail_name,
            'type': 'mailinfo',
            'arg':arg,
        }
        href_res = self.s.post('http://24mail.chacuo.net/',data=post_data)
        text = href_res.text
        href_re = re.compile(r'link below to complete the verification:<\\/p><p><a href=\\"(.*)?">E-mail verification')
        href = re.search(href_re, text)
        if href:
            href = href.group(1).replace('\\','')
            print 'get Verify_href Sucess!  It is ',href
            return href
        else:
            print 'get Verify_href Faild....'
            return False
    def get_verify(self,href,data):
        # headers = {
        #     'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
        # }
        # self.s.headers = headers
        png = self.s.get(href)
        png_text = png.text
        pngtree_re = re.compile(r'<span class="user-name">(\w+)?</span>')
        png_username = re.search(pngtree_re, png_text)
        if png_username:
            png_username = png_username.group(1)
            # print png_text
            mail_name = data[2].split('@')[0]
            id = data[0]
            if png_username == mail_name:
                print 'pngtree.com Verify Sucess!'
                cookie = str(requests.utils.dict_from_cookiejar(self.s.cookies))
                sql = 'UPDATE pngtree_accounts SET status=%d,cookie="%s" WHERE id=%d' % (int(time.time()), cookie, id)
                try:
                    self.db = MySQLdb.connect('localhost', 'root', '123456','pngtree_201712')
                    self.cursor = self.db.cursor()
                    self.cursor.execute(sql)
                    self.db.commit()
                    print 'cookie Saved'
                    self.db.close()
                except Exception, e:
                    print sql
                    print str(e)
                    print 'cookie Save Faild'
                    self.db.rollback()
                    self.db.close()
        else:
            print 'pngtree.com Verify Faild......'
    def mysql_get_userdata(self):
        sql = 'SELECT id,user_name,email,password FROM pngtree_accounts WHERE status=0 LIMIT 1'
        try:
            self.cursor.execute(sql)
            user_data = self.cursor.fetchone()
            if user_data:
                id = user_data[0]
                sql = 'UPDATE pngtree_accounts SET status=1 WHERE id=%d' % id
                self.cursor.execute(sql)
                self.db.commit()
                self.db.close()
                return user_data
        except Exception, e:
            print sql
            print str(e)
            self.db.close()

if __name__ == '__main__':
    reg = register('https://pngtree.com')
    # 从数据取出一套数据
    user_data = reg.mysql_get_userdata()
    # 注册一个临时邮箱
    email_data = reg.get_email(user_data)
    if email_data:
        # 去pngtree网站注册
        reg.send_mail(user_data)
        time.sleep(30)
        # 获取收件箱的邮件
        png_id = reg.get_inbox(email_data)
        if png_id:
            png_url = reg.get_feed_href(png_id,email_data)
            if png_url:
            # 验证pngtree,并保存cookie
                reg.get_verify(png_url,user_data)
    else:
        print 'get Temp_email Faild....'

