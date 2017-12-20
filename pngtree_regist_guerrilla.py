#coding:utf-8
'''
register是一个自动注册账号的类。
先申请一个临时邮箱，然后去pngtree网站进行注册，获取到验证邮件后，请求验证地址，将cookie存入MySQL数据库。

引用的库： 原生库：urllib,re,time  第三方库：MySQLdb,selenium,requests
数据库：采用了MySQL数据库进行数据的提取及存储

get_email方法：从数据库中获取用户信息，去临时邮箱网站注册一个临时邮箱。
send_email方法：利用selenium驱动PHANTOMJS浏览器，进行pngtree网站的用户注册，让其发送一个验证邮件到我们的临时邮箱里。
get_inbox方法：刷新临时邮箱，获取验证邮箱的ID。
get_pngemail方法：根据ID获取到pngtree的验证邮件并返回。
get_verify方法：根据获取到的URL进行请求，获取到登陆后的cookie，存入到MySQL数据库
mysql_get_userdata方法：从数据库中获取一条用户信息并返回。
add_proxies方法：从数据库中获取一条代理，加在请求上，并返回代理，给selenium使用。
'''
import requests,urllib,re,MySQLdb,time
from selenium import webdriver
from selenium.webdriver.common import keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.proxy import ProxyType
class register():
    def __init__(self,url):
        self.url = url
        # 初始化一个session会话，用来发起请求，主要是最终保持cookie
        self.s = requests.session()
        # 连接mysql数据库
        self.db = MySQLdb.connect('localhost', 'root', '123456', 'pngtree_201712')
        self.cursor = self.db.cursor()
    def get_email(self,user_data):
        # 注册一个新邮箱
        username = user_data[1]
        url = 'https://www.guerrillamail.com/ajax.php?f=set_email_user'
        data = {
            'email_user': username,
            'lang': 'en',
            'site': 'guerrillamail.com'
        }
        res = self.s.post(url, data=data)
        print "新注册的邮箱：",data,res.text
    def send_mail(self,user_data,proxie):
        # 去pngtree网站进行注册，给申请的临时邮箱发送一封验证邮件
        id = user_data[0]
        username = user_data[1]
        email = user_data[2].replace('yopmail','sharklasers')
        password = user_data[3]
        # 创造一个浏览器
        browser1 = webdriver.PhantomJS(executable_path=r"/Users/qiyue/myxuni/phantomjs-2.1.1/bin/phantomjs", )  # //内核 webkkit
        # 代理ip
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
        # 填写注册信息
        browser1.find_element_by_id('base-public-login-username-regiser-text').send_keys(username)
        browser1.find_element_by_id('base-public-login-email-regiser-text').send_keys(email)
        browser1.find_element_by_id('base-public-login-password-regiser-text').send_keys(password)
        browser1.find_element_by_id('base-sub-regist-Btn').click()
        time.sleep(10)
        browser1.save_screenshot('regist.png')
        browser1.quit()
        # 把用户信息状态更改为1，代表已经注册过
        sql = 'UPDATE pngtree_user SET status=1 WHERE id=%d' % id
        try:
            self.cursor.execute(sql)
            self.db.commit()
        except Exception, e:
            print sql
            print str(e)
            self.db.rollback()
        # browser1.close()
    def get_inbox(self,data):
        t = time.time()
        i = int(t * 100)
        # 刷新查看收件箱
        url1 = 'https://www.guerrillamail.com/ajax.php?f=check_email&seq=1&site=guerrillamail.com&_=%s' % int(t * 100)
        para = {
            'f': 'check_email',
            'seq': '1',
            '_': str(i)
        }
        re1 = self.s.get(url1, params=para)
        text = str(re1.text)
        re_mail = re.compile(r'"mail_id":"(.*)?","mail_from":"pngtree@email.pngtree.com"')
        # 获取指定邮件的id
        mail_id = re.search(re_mail,text).group(1)
        print 'mail_id:  ',mail_id
        return mail_id
    def get_pngemail(self,mail_id):
        t = time.time()
        i = int(t * 100)
        # 找到pngtree的验证邮件id，发起请求获取验证邮件
        pngtree_url = 'https://www.guerrillamail.com/ajax.php?f=fetch_email&email_id=mr_%s&site=guerrillamail.com&_=%s' % (mail_id, int(t * 100))
        print 'pngtree eamial: ',pngtree_url
        paras = {
            'f': 'fetch_email',
            'email_id': 'mr_%s' % mail_id,
            'site': 'guerrillamail.com',
            '_': str(i)
        }
        re11 = self.s.get(pngtree_url, params=paras)
        text12 = str(re11.text).replace('true', '1')
        re_png = re.compile(r'href=\\"(.*)?">E-mail', re.S)
        # 匹配出pngtree的登陆链接，发起请求
        pngtree_link = re.findall(re_png, text12)[0].replace('\\', '')
        print 'pngtree login url: ',pngtree_link
        return pngtree_link
    def get_verify(self,href,user_data):
        id = user_data[0]
        username = user_data[1]
        # get请求验证链接，完成注册pngtree
        pngtree = self.s.get(href)
        png_text = pngtree.text
        pngtree_re = re.compile(r'<span class="user-name">(\w+)?</span>')
        # 如果登陆成功，就把cookie存到数据库中
        png_username = re.search(pngtree_re,png_text).group(1)
        if png_username == username:
            cookie = str(requests.utils.dict_from_cookiejar(self.s.cookies))
            sql = 'UPDATE pngtree_user SET status=100,cookie="%s" WHERE id=%d' % (cookie,id)
            try:
                self.cursor.execute(sql)
                self.db.commit()
                print 'cookie保存成功'
            except Exception, e:
                print sql
                print str(e)
                self.db.rollback()
    def mysql_get_userdata(self):
        # 去mysql数据库中获取用户信息
        sql = 'SELECT id,user_name,email,password FROM pngtree_user WHERE status=0 LIMIT 1'
        try:
            self.cursor.execute(sql)
            user_data = self.cursor.fetchone()
            if user_data:
                return user_data
        except Exception, e:
            print sql
            print str(e)
    def add_proxies(self):
        # 从数据库中取出代理，给session会话加代理，返回代理信息，给phantomjs也加上代理
        sql = "select * from pngtree_proxy order by status asc limit 1"
        try:
            self.cursor.execute(sql)
            proxies = self.cursor.fetchone()
            # 更新代理时间戳
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
if __name__ == '__main__':
    reg = register('https://pngtree.com')
    # proxie = reg.add_proxies()
    proxie = '123.118.1.198:8118'
    userdata = reg.mysql_get_userdata()
    print userdata, type(userdata)
    # 注册一个邮箱
    email_data = reg.get_email(userdata)
    # 用新注册的邮箱去pngtree注册账号
    reg.send_mail(userdata,proxie)
    time.sleep(5)
    # 刷新收件箱，获取指定的邮件id
    mail_id = reg.get_inbox(email_data)
    # 获取pngtree的登陆链接
    feed_href = reg.get_pngemail(mail_id)
    # 通过邮件进行验证
    reg.get_verify(feed_href, userdata)
