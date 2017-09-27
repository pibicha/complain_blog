import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # wtf 防夸站脚本攻击需要的配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'NiShengRi'

    # sqlAlchemy相关配置
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # flask-mail相关设置，详见https://pythonhosted.org/Flask-Mail/
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    # MAIL_USE_TLS = True 163支持
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # 评论pagesize
    COMMENT_PER_PAGE = 8
    # 博客分页——每页datasize
    POSTS_PER_PAGE = 20
    # 默认分页大小
    PER_PAGE = 20

    # 由子类实现，类似java的模板方法，可以对app进行扩展
    @staticmethod
    def init_app(app):
        pass


class Dev(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL')


class ProductionConfig(Config):
    @classmethod
    def init_app(cls,app):
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

config = {
    'development': Dev,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': Dev
}
