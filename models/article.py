import pymysql
import redis
import private

class ArticleModel():
    def __init__(self,*args,**kwargs):
        self.con = pymysql.connect(
            host = private.MYSQL_HOST,
            port = private.MYSQL_PORT,
            user = private.MYSQL_USER,
            password = private.MYSQL_PASSWORD,
            db = private.MYSQL_DB,
        )
        self.cursor = self.con.cursor()

    @property
    def max_article_id(self):
        sql = "SELECT MAX(`id`) FROM `fa_cms_archives`"
        self.cursor.execute(sql)
        return int(self.cursor.fetchone()[0])

    def select_article(self, id):
        sql = "SELECT `channel_id`, `title` FROM `fa_cms_archives` WHERE id='{}'".format(id)
        self.cursor.execute(sql)
        return self.cursor.fetchone()

    def select_content(self, id):
        sql = "SELECT `content` FROM `fa_cms_addonnews` WHERE id={}".format(id)
        self.cursor.execute(sql)
        return self.cursor.fetchone()


class ManageIds():
    def __init__(self):
        host,port,password,db = private.REDIS_HOST, private.REDIS_PORT, private.REDIS_PASS, private.REDIS_DB
        self.re = redis.Redis(host=host,port=port,password=password,db=db,charset="utf-8",decode_responses=True)
        self.material_name = "YiBan:All:MaterialID:set"
        self.not_publish_name = "YiBan:NotPublish:MaterialID:set"
        self.build_name = "YiBan:Build:MaterialID:str"

        # 初始化redis中的数据，发布以及上传的id
        if not self.new_build_id:
            self.re.set(self.build_name, "1")

    def get_publish(self):
        ''' 返回需要进行发布的素材id '''
        return self.re.smembers(self.not_publish_name)

    def rm_publish_id(self, id):
        ''' 将已发布的素材从未发布中移除 '''
        self.re.srem(self.not_publish_name, id)

    def add_material(self, id):
        ''' 将id放入material总记录中 '''
        self.re.sadd(self.material_name, id)

    def get_all_material(self):
        ''' 获取所有的记录 '''
        return self.re.smembers(self.material_name)

    def rm_id(self, id):
        ''' 删除总记录中某条记录 '''
        self.re.srem(self.material_name, id)

    def add_not_publish(self, id):
        ''' 将id放入未发布的记录中 '''
        self.re.sadd(self.not_publish_name, id)

    def is_in_record(self, id):
        ''' 判断id是否已经加入记录 '''
        if self.re.sismember(self.material_name, id):
            return True

    def incr_build_id(self):
        ''' 设置上传的id '''
        self.re.incr(self.build_name)

    @property
    def new_build_id(self):
        ''' 获取上传的最新id '''
        res = self.re.get(self.build_name)
        return res

if __name__ == '__main__':
    # article = ArticleModel()
    # print(article.max_article_id)

    # 测试redis
    manage = ManageIds()
    print(manage.get_all_material())
