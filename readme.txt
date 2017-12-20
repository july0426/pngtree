项目综述：pngtree.com网站进行爬取
目标数据：图片及相关信息。
编程语言：Python
数据  库：MySQL MongoDB
主要难点：该网站需要登陆才可以下载图片，且每个用户每天只能下载3张。
解决方案：利用临时邮箱网站进行账号注册，然后每天爬取一定量的图片。
主要技术：
        requsets/urllib 模拟请求
        xpath/正则  数据解析
        selenium 自动注册账号
主要文件：
        pngtree:数据爬取及存储
        pngtree_pic_download:图片下载
        pngtree_regist_guerrilla:账号自动注册
        myqueue：队列，管理URL
业务流程：
        1.自动注册一些账号，保存cookie
        2.爬取网站的数据、图片下载地址
        3.利用cookie，下载图片
