from features import login, yiban
from models import article
import private
import time
import random
import logging

login_pub = login.YiLogin(username=private.YIBAN_USERNAME, password=private.YIBAN_PASSWORD)
login_super = login.UisLoginMobile(ID=private.SUPER_ID)

material = yiban.Material()
manage_id = article.ManageIds()
article_model = article.ArticleModel()

# 登录 公共账号的账号密码，以及管理员账号密码
cookies_pub = login_pub.login()
cookies_super = login_super.login()

def material_loop(cookies):
    ''' 获取所有的material并存储 '''
    for i in range(1000):
        logging.info("获取material_id")
        time.sleep(random.random())
        id_titles = material.get_material_ids(cookies, page=i)
        if id_titles:
            for id,title in id_titles:
                # 判断是否为爬虫同步新闻
                if title.split("-")[-1] == "校园同步":
                    # 判断是否不在redis中, 不在的话添加到所有记录以及未发布记录中
                    if not manage_id.is_in_record(id):
                        manage_id.add_not_publish(id)
                        manage_id.add_material(id)
        else:
            logging.info("material_id获取完毕")
            return


def build_loop(cookies):
    ''' 将未上传的文章上传 '''
    for i in range(100):
        time.sleep(random.random()+random.randint(10,60))
        new_id = manage_id.new_build_id
        logging.info("上传素材中。。。{}".format(new_id))

        type_title = article_model.select_article(id=new_id)
        content = article_model.select_content(id=new_id)

        if not type_title or not content:
            if i < article_model.max_article_id:
                manage_id.incr_build_id()
                continue
            else:
                logging.info("上传素材完毕")
                return

        type, title = type_title
        if type == "3":
            manage_id.incr_build_id()
            continue
        title = "{}-校园同步".format(title)
        content = content[0]
        material.build(cookies, title, cover="http://img01.fs.yiban.cn/pic/5370552/web/thumb_640x0/3770211755db6f02e26f8c.png",
          showCover="false", summary="", content=content, mid="")
        # 文章发布之后， 发布id自增长1
        manage_id.incr_build_id()

def publish_loop(cookies, mobile_cookies):
    ''' 对未发布的文章进行发布 '''
    not_piblish_set = manage_id.get_publish()
    for i in not_piblish_set:
        logging.info("素材发布中。。。{}".format(i))
        material.publish(material_id=i, cookies=cookies, mobile_cookies=mobile_cookies)
        manage_id.rm_publish_id(id=i)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    def test_all():
        # build
        type_title = article_model.select_article(id=1)
        content = article_model.select_content(id=1)
        if type_title:
            type, title = type_title
            title = "{}-校园同步".format(title)
            content = content[0]
            material.build(cookies_pub, title,
                           cover="http://img01.fs.yiban.cn/pic/5370552/web/thumb_640x0/3770211755db6f02e26f8c.png",
                           showCover="false", summary="", content=content, mid="")

        # get_id
        id_titles = material.get_material_ids(cookies_pub, page=1)
        if id_titles:
            for id, title in id_titles:
                # 判断是否为爬虫同步新闻
                if title.split("-")[-1] == "校园同步":
                    # 判断是否不在redis中, 不在的话添加到所有记录以及未发布记录中
                    if not manage_id.is_in_record(id):
                        manage_id.add_not_publish(id)
                        manage_id.add_material(id)
        # pub
        publish_loop(cookies_pub, cookies_super)

    while 1:
        logging.info("start material_loop")
        material_loop(cookies_pub)
        logging.info("end material_loop")

        logging.info("start build_loop")
        build_loop(cookies_pub)
        logging.info("end build_loop")

        logging.info("start publish_loop")
        publish_loop(cookies_pub, cookies_super)
        logging.info("end publish_loop")
        time.sleep(60*60*2)