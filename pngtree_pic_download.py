#coding:utf-8
'''
pngtree_pic_downloads是一个用来下载图片的类，
通过从MySQL数据库中提取要下载的连接，发起请求，将图片以二进制的形式进行保存。

使用了python的re,MySQLdb,requests,json模块

download方法：这个类的主要方法，取出连接，下载图片，其他方法都是他的辅助
get_url方法：从数据库中取出URL并返回，把状态进行变更，改成已下载
get_cookie方法：从数据库中取出用户的cookie并返回，把状态更改成已登陆（或者时间戳）。
pic_download方法：根据提供的参数URL，发起请求，进行图片的下载
add_proxies方法：从数据库中提取代理并返回，更改状态（时间戳）。

pic_download方法需要3个参数，URL参数是获取图片连接的URL，cook是用来模拟登录的cookies，txt是图片的格式。
其他方法不需要参数。
'''
import re,MySQLdb,requests,json
class pngtree_pic_downloads():
    def __init__(self):
        # 连接mysql数据库
        self.db = MySQLdb.connect('localhost','root','123456','pngtree_201712')
        self.cursor = self.db.cursor()
    def download(self):
        # 从数据库中读取一条数据
        url = self.get_url()
        png_url = url[1]
        psd_url = url[2]
        eps_url = url[3]
        ai_url = url[4]
        # 从数据库中获取cookie，转成字典格式
        cook = self.get_cookie()[1]
        print cook
        cookies = eval(cook)
        # 用i进行计数，请求一次加1，超过3次从新计数，并且更换cookie（用户，每个用户每天最多下载3张图片）
        i = 1
        # 图片下载URL，如果没有该格式图片，URL是None，根据图片的类型，判断文件的格式
        if png_url != 'None':
            if i < 4:
                self.pic_download(png_url,cookies,'png')
                i += 1
            else:
                i = 1
                cookies = json.dumps(self.get_cookie()[1])
                self.pic_download(png_url, cookies,'png')
        if psd_url != 'None':
            if i < 4:
                self.pic_download(png_url,cookies,'zip')
                i += 1
            else:
                i = 1
                cookies = json.dumps(self.get_cookie()[1])
                self.pic_download(png_url, cookies,'zip')
        if eps_url != 'None':
            if i < 4:
                self.pic_download(png_url,cookies,'zip')
                i += 1
            else:
                i = 1
                cookies = json.dumps(self.get_cookie()[1])
                self.pic_download(png_url, cookies,'zip')
        if ai_url != 'None':
            if i < 4:
                self.pic_download(png_url,cookies,'zip')
                i += 1
            else:
                i = 1
                cookies = json.dumps(self.get_cookie()[1])
                self.pic_download(png_url, cookies,'zip')
    def get_url(self):
        # 去数据库中取出一条要下载的URL的相关数据
        sql = 'SELECT id,download_url,download_url_psd,eps_download_url,ai_download_url FROM my_pngtree_pdts WHERE status=0 LIMIT 1'
        try:
            self.cursor.execute(sql)
            pic_url = self.cursor.fetchone()
            id = pic_url[0]
            # 把状态更新，代表已经下载
            sql = "update my_pngtree_pdts set status=1 where id=%d" % id
            try:
                self.cursor.execute(sql)
                self.db.commit()
            except Exception, e:
                print str(e)
                self.db.rollback()
            print pic_url
            return pic_url
        except Exception, e:
            print sql
            print str(e)
    def get_cookie(self):
        sql = 'SELECT id,cookie FROM pngtree_user WHERE status=100 LIMIT 1'
        try:
            self.cursor.execute(sql)
            cookie = self.cursor.fetchone()
            id = cookie[0]
            # 更新cookie的使用状态，代表已经使用过
            sql = "update pngtree_user set status=111 where id=%d" % id
            try:
                self.cursor.execute(sql)
                self.db.commit()
            except Exception, e:
                print str(e)
                self.db.rollback()
            print cookie
            return cookie
        except Exception, e:
            print sql
            print str(e)
    def pic_download(self,url,cook,txt):
        # 根据传入的url进行请求，获取指定的ID及csrf
        response = requests.get(url,cookies=cook)
        id_html = response.text
        # print id_html
        res = re.compile(r'data-id="(\d+)?"')
        id = re.search(res,id_html).group(1)
        re_par = re.compile(r'name="csrf-token".*?content="(.*?)"')
        csrf = re.findall(re_par, id_html)[0]
        data = {
            "id":str(id),
            '_csrf':str(csrf),
            'type':'1',
            'down_file_code':'0',
            'dec':'1',
        }
        print data
        headers = {
            'authority': 'pngtree.com',
            'method': 'POST',
            'path': '/element/download-file',
            'scheme': 'https',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'content-length': '107',
            'content-type': 'application/x-www-form-urlencoded',
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        # 对download API进行post请求，获取图片url
        cookie = {
            'auth_uid': cook['auth_uid'],
            '_csrf': '8c0a33ace128c6d0004274760f1af66da99f1b0e8e8acfec066506f31c7b5430a%3A2%3A%7Bi%3A0%3Bs%3A5%3A%22_csrf%22%3Bi%3A1%3Bs%3A32%3A%22A9apYkHC6CDjhMJ1r4DxQLoNQyzCE9p3%22%3B%7D'
        }
        res = requests.post('https://pngtree.com/element/download-file', data=data, headers=headers , cookies=cookie)
        print res.text,res
        url_json = eval(res.text)
        pic_url = url_json['url']
        # 下载图片，发起请求，以二进制方式写入文件
        pic = requests.get(pic_url).content
        filename = url.replace('https://pngtree.com/element/down?', '')
        with open('./png/' + filename + '.' + txt, 'wb') as f:
            f.write(pic)
    def add_poxies(self):
        # 从数据库中取出代理
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
            self.db.commit()
            return proxy
        except Exception, e:
            print sql
            print str(e)
            self.db.rollback()



if __name__ == '__main__':
    down = pngtree_pic_downloads()
    down.download()
