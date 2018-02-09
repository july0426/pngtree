#coding:utf-8
import requests,urllib,urllib2,re,random,MySQLdb
from selenium import webdriver
from selenium.webdriver.common import keys
from selenium.webdriver.common import keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.proxy import ProxyType
import time
from lxml import etree
class register():
    def __init__(self,url):
        self.url = url
        self.s = requests.session()
        self.db = MySQLdb.connect('localhost', 'aio_music', 'aio_music_pass', 'kiss_png')
        self.cursor = self.db.cursor()
    def add_poxies(self):
        sql = "select * from pngtree_proxy order by status asc limit 1"
        try:
            self.cursor.execute(sql)
            proxies = self.cursor.fetchone()
            sql = "update pngtree_proxy set status=%d where id=%d" % (int(time.time()),proxies[0])
            self.cursor.execute(sql)
            proxie = proxies[2]
            proxy = {
                'http':'http://%s' % proxie,
                'https': 'https://%s' % proxie,
            }
            self.s.proxies = proxy
            self.db.commit()
            return proxie
        except Exception, e:
            print sql
            print str(e)
            self.db.rollback()
    def send_mail(self,data,proxie):
        username = data[1]
        email = data[2].split('@')[0] + '@027168.com'
        password = data[3]
        # 创造一个浏览器
        browser1 = webdriver.PhantomJS(executable_path=r"/usr/local/bin/phantomjs",)  # //内核 webkkit
        proxy = webdriver.Proxy()
        proxy.proxy_type = ProxyType.MANUAL
        proxy.http_proxy = proxie
        # 将代理设置添加到webdriver.DesiredCapabilities.PHANTOMJS中
        proxy.add_to_capabilities(webdriver.DesiredCapabilities.PHANTOMJS)
        browser1.start_session(webdriver.DesiredCapabilities.PHANTOMJS)
        browser1.get('https://pngtree.com/')
        # 点击注册按钮
        browser1.find_element_by_id('base-public-register-button').click()
        # print browser.page_source
        browser1.find_element_by_id('base-public-login-username-regiser-text').send_keys(username)
        browser1.find_element_by_id('base-public-login-email-regiser-text').send_keys(email)
        browser1.find_element_by_id('base-public-login-password-regiser-text').send_keys(password)
        browser1.find_element_by_id('base-sub-regist-Btn').click()
        time.sleep(10)
        browser1.save_screenshot('regist.png')
        browser1.quit()

    '''根据数据库取出的数据,去注册一个邮箱'''
    def get_email(self, user_data):
        mail = user_data[2].split('@')[0]
        # 注册一个新邮箱
        print mail
        email = mail + '@027168.com'
        # 注册一个新邮箱
        url = 'http://24mail.chacuo.net/'
        post_data = {
            'data': mail,
            'type': 'set',
            'arg': 'd=027168.com_f='
        }
        try:
            self.s.get(url)
            res = self.s.post(url, data=post_data)
            # print res.text
            if '"info":"ok"' in res.text:
                print 'set Temp_mail Sucess! It is ', email
                return email
            else:
                print 'set Temp_mail Faild...'
                return False
        except Exception as e:
            print str(e)
            print 'proxy May Disabled!'
            return False
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
        png = self.s.get(href)
        png_text = png.text
        pngtree_re = re.compile(r'<span class="user-name">(\w+)?</span>')
        png_username = re.search(pngtree_re, png_text)
        if png_username:
            png_username = png_username.group(1)
            user_name = data[1]
            id = data[0]
            if png_username == user_name:
                print 'pngtree.com Verify Sucess!'
                cookie = str(requests.utils.dict_from_cookiejar(self.s.cookies))
                sql = 'UPDATE pngtree_accounts SET status=%d,cookie="%s" WHERE id=%d' % (int(time.time()), cookie, id)
                try:
                    self.db = MySQLdb.connect('localhost', 'aio_music', 'aio_music_pass', 'kiss_png')
                    self.cursor = self.db.cursor()
                    self.cursor.execute(sql)
                    self.db.commit()
                    self.db.close()
                    print 'cookie Saved'
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
    proxie = reg.add_poxies()
    # 从数据取出一套数据
    user_data = reg.mysql_get_userdata()
    # 注册一个临时邮箱
    email_data = reg.get_email(user_data)
    if email_data:
        # 去pngtree网站注册
        reg.send_mail(user_data,proxie)
        time.sleep(30)
        # 获取收件箱的邮件
        feed_id = reg.get_inbox(email_data)
        if feed_id:
            # 获取pngtree的验证链接
            href = reg.get_feed_href(feed_id,email_data)
            if href:
                # 验证pngtree,并保存cookie
                reg.get_verify(href, user_data)
    else:
        print 'get Temp_email Faild....'
