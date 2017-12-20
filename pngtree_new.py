#coding:utf-8
'''
pngtree是一个爬取pngtree.com图片及图片信息的爬虫类。
通过主页作为入口，先获取所有的子类，然后根据子类爬取所有的列表页，再从列表页爬取所有的详情页，
最终获取图片信息及图片下载的URL，存入MySQL数据库。

引用的库： 原生库：urllib,re,socket  第三方库：MySQLdb，lxml   自己的包：myqueue
数据库：采用了MySQL数据库进行数据的存储，用MongoDB进行URL的管理，正在进行或者失败，这样可以根据需要进行分布式的爬取。
数据解析：主要采用了xpath和正则相结合，xpath为主，正则为辅。
方法间通信：利用MongoDB作为队列，所有要爬取的URL都在这个队列中。

get_subcat方法：从主页获取到子类的链接，存入到利用MongoDB生成的队列中。
get_list方法：从队列中获取列表页的链接，匹配到详情页的链接，存入到队列中。
get_detail方法：从队列中取出详情页的链接，匹配到信息，存入到MySQL中。
get_html方法：根据传入的URL进行请求，把响应转化为xml，如果请求失败，就更改队列中的该URL的状态。
fail_handler方法：从队列中提取请求失败的链接，根据函数名称进行重新请求。
process_handler方法：从队列中提取意外中断的链接，根据函数名称进行重新请求。
'''
import urllib,re,socket,MySQLdb
from lxml import etree
from myqueue import MongoQueue
class pngtree():
    # 设置请求超时时间
    socket.setdefaulttimeout(50)
    def __init__(self):
        self.url = 'https://pngtree.com'
        # 实例化一个队列
        self.myqueue = MogoQueue('pngtree','url')
        # 连接mysql数据库
        self.db = MySQLdb.connect('localhost','root','123456','pngtree_201712')
        self.cursor = self.db.cursor()
    def get_subcat(self):
        html = self.get_html(self.url,self.get_subcat.__name__)
        # 顶部区域入口,子类的url
        href = html.xpath('//li[position()<=3]/div[@class="clearfix vfp-cont  tran"]')
        for i in href:
            url = i.xpath('./a/@href')
            for j in url:
                # 匹配出子分类
                if j == '/free-web-templates-psd':
                    subcat = 'web-templates'
                else:
                    subcat = j.split('-')[1]
                    print subcat
                # 匹配出子分类的url
                list_url = self.url + j + '/1'
                # 把子分类的url存入到队列中
                self.myqueue.push(list_url,'get_list',subcat)
    def get_list(self):
        #从队列中取出一个子类URL
        list_data = self.myqueue.pop('get_list')
        list_url = list_data['url']
        subcat = list_data['subcat']
        list_html = self.get_html(list_url,self.get_list.__name__)
        if list_html != 0:
            if list_html is not None:
                divs = list_html.xpath('.//div[@class="list-item"]')
                for div in divs:
                    detail_url = div.xpath('.//div[@class="img-hoder"]/a/@href')[0]
                    detail_url = self.url + detail_url
                    self.myqueue.push(detail_url,'get_detail',subcat)
                next_page = list_html.xpath('.//a[@class="nextPage "]/@href')[0]
                if 'javascript' not in next_page:
                    next_page = self.url + next_page
                    self.myqueue.push(next_page,'get_list',subcat)
                    print next_page
                    self.myqueue.complete(list_url)
                    # 如果有下一页，就继续爬取
                    self.get_list()
    def get_detail(self):
        # 从队列中取出一条数据，根据函数名称取出详情页的URL
        detail_data = self.myqueue.pop('get_detail')
        detail_url = detail_data['url']
        subcat = detail_data['subcat']
        detail_html = self.get_html(detail_url,self.get_detail.__name__)
        # 判断是否链接超时，链接超时返回是0
        if detail_html != 0 :
            if detail_html is not None:
            # 获取各种信息
                title = detail_html.xpath('.//h4/text()')
                if title:
                    title = title[0].replace(' ','').strip()
                    resource_hits = detail_html.xpath('.//div[@class="dr-num"]/span[1]/text()')[0].replace(' Views','')
                    resource_hits = int(resource_hits)
                    downloads = detail_html.xpath('.//div[@class="dr-num"]/span[1]/text()')[0].replace(' Downloads','')
                    cat = detail_html.xpath('.//div[@class="dr-infos"]/p/span[text()="Category:"]/following-sibling::span/text()')
                    if cat :
                        cat = cat[0].replace(' ','')
                    else:
                        cat = 'None'
                    type = detail_html.xpath('.//div[@class="dr-infos"]/p/span[text()="Format:"]/following-sibling::span/text()')[0]
                    type = re.sub(r'\s+','',type)
                    # print type
                    img_url = detail_html.xpath('//div[@class="dl-show"]/img/@src')[0]
                    tags = detail_html.xpath('.//div[@class="add-recommend"]/a/text()')
                    pic_desc = detail_html.xpath('.//div[@class="fl-l detail-left"]/div[2]//text()')
                    pic_desc = ''.join(pic_desc)
                    resolution = detail_html.xpath('.//div[@class="dr-infos"]/p/span[text()="Resolution:"]/following-sibling::span/text()')[0]
                    tag = detail_html.xpath('.//div[@class="dl-keyWords  clearfix"]/a/text()')
                    tag = list(set(tag + tags))
                    tag = ','.join(tag)
                    down_btn = detail_html.xpath('.//div[@class="dloadBtns clearfix"]//a')
                    for btn in down_btn:
                        types = btn.xpath('./text()')[0]
                        types = re.sub(r'\s+','',types).replace('Download','')
                        print types
                        url = btn.xpath('./@href')[0]
                        download_url = 'None'
                        ai_download_url = 'None'
                        eps_download_url = 'None'
                        download_url_psd = 'None'
                        if types == 'PNG':
                            download_url = self.url + url
                            print download_url
                        if types == 'AI':
                            ai_download_url = self.url + url
                        if types == 'EPS':
                            eps_download_url = self.url + url
                        if types == 'PSD':
                            download_url_psd = self.url + url
                        # print 'subcat: %s' % subcat
                    sql = 'INSERT INTO MY_PNGTREE_PDTS(url,status,download_url,img_status,publish_status,title,cat,type,resolution,hits,tag,picdesc,subcat,ai_download_url,eps_download_url,download_url_psd)' \
                    ' VALUES("%s",0,"%s",0,0,"%s","%s","%s","%s",%d,"%s","%s","%s","%s","%s","%s")' % (detail_url,download_url,title,cat,type,resolution,resource_hits,tag,pic_desc,subcat,ai_download_url,eps_download_url,download_url_psd)
                    try:
                        self.cursor.execute(sql)
                        self.db.commit()
                        self.myqueue.complete(detail_url)
                        # print '插入成功'
                    except Exception, e:
                        print sql
                        print str(e)
                        # print title,tag,pic_desc
                        # print '数据已存在'
                        self.db.rollback()
                    # print cat,title,resolution,resource_hits,type,pic_desc,downloads,img_url
    def get_html(self,url,def_name):
        try:
            # 加代理
            # proxy = {'http':'http://192.168.1.89.5216'}
            # request = urllib.urlopen(url,proxies = proxy)
            # 请求URL，获取他的html
            request = urllib.urlopen(url)
            response = request.read()
            html = etree.HTML(response)
            return html
        except Exception as e:
            print str(e)
            # 如果失败，就把这个URL的状态改为faild
            self.myqueue.push_fail(url,def_name)
            print 'fail_url : ',url
            return 0
    def fail_handler(self):
        # 处理请求失败的URL，重新发起请求，根据函数名字调用函数
        faild = self.myqueue.pop_fail()
        if faild is not None:
            try:
                def_name = faild['def_name']
                if def_name == 'get_detail':
                    self.get_detail()
                if def_name == 'get_list':
                    self.get_list()
                    self.get_detail()
            except Exception as e:
                print str(e)
    def process_handler(self):
        # 处理请求中断的URL，重新发起请求，根据函数名字调用函数
        process = self.myqueue.pop_process()
        if process is not None:
            try:
                def_name = process['def_name']
                if def_name == 'get_detail':
                    self.get_detail()
                if def_name == 'get_list':
                    self.get_list()
                    self.get_detail()
            except Exception as e:
                print str(e)



if __name__ == '__main__':
    # 实力化一个类
    png_test = pngtree()
    # 获取到所有的子类，及url
    # png_test.get_subcat()
    # 获取列表页
    # png_test.get_list()
    # 爬取详情页
    # while True:
    #     png_test.get_detail()
    # 如果有失败的，去重新爬取
    png_test.fail_handler()
    # 如果有处理半路终止的，从新爬取
    png_test.process_handler()

























#     # 定义一个协程列表
        # gev_list = []
        # x = 1
        # for div in divs:
        #     x += 1
        #     if x % 3:
        #         detail_url = div.xpath('.//div[@class="img-hoder"]/a/@href')[0]
        #         detail_url = self.url + detail_url
        #         # 添加到协程列表里
        #         gev_list.append(gevent.spawn(self.get_detail, detail_url, subcat))
        #         # 抓取要提取的数据
        #         # self.getTitle(list_url,subcat)
        #     else:
        #         # 当达到指定的数量后，协程开始
        #         # print gev_list
        #         gevent.joinall(gev_list)
        #         gev_list = []
        # # 最后还有几个协程，开启
        # if len(gev_list) >= 1:
        #     gevent.joinall(gev_list)
        # 获取下一页的URL，加入到队列中