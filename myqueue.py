#coding:utf-8
'''
MongoQueue是一个利用MongoDB数据库制作的队列，主要用来管理URL及其状态。
push方法：将一个URL加入到队列中，设置初始状态为1，subcat是子类，要进行函数间的传递，所以也保存起来。
pop方法：将指定函数名字的、状态为起始状态的数据提取出来，并把状态改成正在处理。
complete方法：将指定的URL的状态改为已完成。
push_fail方法:将指定的URL状态改为失败，faild。
pop_fail方法：获取一个状态为fail 的数据，返回。
pop_process方法：获取一个状态为process的数据，并返回。
'''
from pymongo import MongoClient
class MongoQueue():
    # 起始状态，url刚入列的状态
    init_status = 1
    # URL被提取，开始请求的状态
    processing = 2
    # URL请求成功，并处理完成的状态
    completed = 3
    # URL请求失败的状态
    faild = 4
    def __init__(self,db,collection):
        # 连接mongodb
        self.client = MongoClient()
        self.Client = self.client[db]
        self.db = self.Client[collection]
    def push(self,url,def_name,subcat):
        # 将一个URL加入到队列中，subcat是子类，要进行函数间的传递，所以也保存起来
        try:
            self.db.insert({'_id':url,'def_name':def_name,'status':self.init_status,'subcat':subcat})
            print '插入成功'
        except Exception,e:
            print str(e)
            print 'url已经在队列中'
    def pop(self,def_name):
        #取出一个URL
        # record记录，查询出想要的URL
        # 默认按照插入顺序查找，显示一条，并把状态更改成为正在处理
        record = self.db.find_and_modify(
            query = {'status':self.init_status,'def_name':def_name},
            update = {'$set':{'status':self.processing}}
        )
        if record:
            # 返回URL，子类名称
            return {'url':record['_id'],'subcat':record['subcat']}
        else:
            print 'keyerror'
    def complete(self,url):
        # 把已经完成的URL状态改成已完成
        self.db.update({'_id': url}, {'$set': {'status': self.completed}})
    def push_fail(self,url,def_name):
        # 插入一条失败的URL，就是更改状态
        self.db.update({'_id': url,'def_name': def_name}, {'$set': {'status': self.faild}})
    def pop_fail(self):
        # 取出一个爬取失败的URL
        # record记录，查询出想要的URL
        # 默认按照插入顺序查找，显示一条
        record = self.db.find_and_modify(
            query={'status': self.faild},
            update={'$set': {'status': self.processing}}
        )
        if record:
            return {'url':record['_id'],'def_name':record['def_name'],'subcat':record['subcat']}
        else:
            print 'keyerror'
    def pop_process(self):
        # 取出一个爬取中断的URL
        # record记录，查询出想要的URL
        # 默认按照插入顺序查找，显示一条
        record = self.db.find_one({'status': self.processing})
        if record:
            return {'url':record['_id'],'def_name':record['def_name'],'subcat':record['subcat']}
        else:
            print 'keyerror'

if __name__ == "__main__":
    myqueue = MogoQueue('pngtree','test')
    # myqueue.push('www.duu2.com','deatil','a')
    # myqueue.push('www.duu3.com', 'deatil','b')
    # myqueue.push('www.duuqq.com', 'deatil','b')
    print myqueue.pop_process()
    print 8