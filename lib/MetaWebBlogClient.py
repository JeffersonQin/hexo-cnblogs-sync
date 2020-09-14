import xmlrpc.client as xmlrpclib
import json
import datetime
import time
import getpass

'''
配置字典：
type | description(example)
str  | metaWeblog url, 博客设置中有('https://rpc.cnblogs.com/metaweblog/1024th')
str  | appkey, Blog地址名('1024th')
str  | blogid, 这个无需手动输入，通过getUsersBlogs得到
str  | usr, 登录用户名
str  | passwd, 登录密码
str  | rootpath, 博文存放根路径（添加git管理）
'''

'''
POST:
dateTime	dateCreated - Required when posting.
string	description - Required when posting.
string	title - Required when posting.
array of string	categories (optional)
struct Enclosure	enclosure (optional)
string	link (optional)
string	permalink (optional)
any	postid (optional)
struct Source	source (optional)
string	userid (optional)
any	mt_allow_comments (optional)
any	mt_allow_pings (optional)
any	mt_convert_breaks (optional)
string	mt_text_more (optional)
string	mt_excerpt (optional)
string	mt_keywords (optional)
string	wp_slug (optional)
'''

class MetaWebBlogClient():
    def __init__(self, configpath):
        '''
        @configpath: 指定配置文件路径
        '''
        self._configpath = configpath
        self._config = None
        self._server = None
        self._mwb = None
    
    def createConfig(self):
        '''
        创建配置
        '''
        while True:
            cfg = {}
            for item in [("url", "MetaWebBlog URL: "),
                        ("appkey", "博客地址名(网址的用户部分): "),
                        ("usr", "登录用户名: ")]:
                cfg[item[0]] = input("输入" + item[1])
            cfg['passwd'] = getpass.getpass('输入登录密码: ')
            try:
                server = xmlrpclib.ServerProxy(cfg["url"])
                userInfo = server.blogger.getUsersBlogs(cfg["appkey"], cfg["usr"], cfg["passwd"])
                print(userInfo[0])
                # {'blogid': 'xxx', 'url': 'xxx', 'blogName': 'xxx'}
                cfg["blogid"] = userInfo[0]["blogid"]
                break
            except:
                print("发生错误！")
        with open(self._configpath, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=4, ensure_ascii=False)
        
    def existConfig(self):
        '''
        返回配置是否存在
        '''
        try:
            with open(self._configpath, "r", encoding="utf-8") as f:
                try:
                    cfg = json.load(f)
                    if cfg == {}:
                        return False
                    else:
                        return True
                except json.decoder.JSONDecodeError:  # 文件为空
                    return False
        except:
            with open(self._configpath, "w", encoding="utf-8") as f:
                json.dump({}, f)
                return False

    def readConfig(self):
        '''
        读取配置
        '''
        if not self.existConfig():
            self.createConfig()

        with open(self._configpath, "r", encoding="utf-8") as f:
            self._config = json.load(f)
            self._server = xmlrpclib.ServerProxy(self._config["url"])
            self._mwb = self._server.metaWeblog

    def getUsersBlogs(self):
        '''
        获取博客信息
        @return: {
            string  blogid
            string	url
            string	blogName
        }
        '''
        userInfo = self._server.blogger.getUsersBlogs(self._config["appkey"], self._config["usr"], self._config["passwd"])
        return userInfo

    def getRecentPosts(self, num):
        '''
        读取最近的博文信息
        '''
        return self._mwb.getRecentPosts(self._config["blogid"], self._config["usr"], self._config["passwd"], num)

    def newPost(self, post, publish):
        '''
        发布新博文
        @post: 发布内容
        @publish: 是否公开
        '''
        while True:
            try:
                postid = self._mwb.newPost(self._config['blogid'], self._config['usr'], self._config['passwd'], post, publish)
                break
            except:
                time.sleep(5)
        return postid

    def editPost(self, postid, post, publish):
        '''
        更新已存在的博文
        @postid: 已存在博文ID
        @post: 发布内容
        @publish: 是否公开发布
        '''
        self._mwb.editPost(postid, self._config['usr'], self._config['passwd'], post, publish)

    def deletePost(self, postid, publish):
        '''
        删除博文
        '''
        return self._server.blogger.deletePost(self._config['appkey'], postid, self._config['usr'], self._config['passwd'], publish)

    def getCategories(self):
        '''
        获取博文分类
        '''
        return self._mwb.getCategories(self._config['blogid'], self._config['usr'], self._config['passwd'])

    def getPost(self, postid):
        '''
        读取博文信息
        @postid: 博文ID
        @return: POST
        '''
        return self._mwb.getPost(postid, self._config['usr'], self._config['passwd'])

    def newMediaObject(self, file):
        '''
        资源文件（图片，音频，视频...)上传
        @file: {
            base64	bits
            string	name
            string	type
        }
        @return: URL
        '''
        return self._mwb.newMediaObject(self._config['blogid'], self._config['usr'], self._config['passwd'], file)
    
    def newCategory(self, categoray):
        '''
        新建分类
        @categoray: {
            string	name
            string	slug (optional)
            integer	parent_id
            string	description (optional)
        }
        @return : categorayid
        '''
        return self._server.wp.newCategory(self._config['blogid'], self._config['usr'], self._config['passwd'], categoray)