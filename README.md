## 易班EGPA值

**使用Python封装部分易班接口 模拟登录、文章发布以及管理员确认、模拟浏览文章、点赞评论投票等功能**

### egpa3/features/login.py

实现易班手机版和网页版的模拟登录，主要使用requests实现

**加密：** RSA 非对称加密 1024

代码参考：https://github.com/hfldqwe/encrypt

**模拟登陆**

验证码部分使用了第三方接口

### egpa3/features/yiban.py

- 实现管理员文章的确认，这个地方用了`websocket`
- 对文章上传，发布做了一个封装

### egpa3/models/article.py

- 获取数据库中的文章
- 对redis相关操作(文章的id和cookies等内容)封装
