from . import db

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request

from flask_misaka import markdown

from . import login_manager
from datetime import datetime

import hashlib

# 中间表不需要继承db.Model
users_roles = db.Table('users_roles',
                       db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                       db.Column('role_id', db.Integer, db.ForeignKey('roles.id')))


# 文章
class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # 生成假数据
    def generate_fake(count=100):
        from random import seed, randint
        # import forgery_py
        from faker import Faker
        fake = Faker("zh_CN")
        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            p = Post(body=fake.sentences(nb=3),
                     timestamp=fake.date_time(tzinfo=None),
                     author=u)
            db.session.add(p)
            db.session.commit()

    # 为了避免一页中渲染20条Post，设计一个字段专门保存body的html内容
    body_html = db.Column(db.Text)

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        target.body_html = markdown(value)


db.event.listen(Post.body, 'set', Post.on_changed_body)


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    def __repr__(self):
        return '<Role %r>' % self.name


# 关注——中间表
class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    # 关注表自引用：
    followed = db.relationship('Follow', foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic', cascade='all,delete-orphan')
    followers = db.relationship('Follow', foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic', cascade='all,delete-orphan')
    # 中间表映射关系
    roles = db.relationship(
        'Role',
        secondary=users_roles,
        backref=db.backref('users', lazy='dynamic'))

    # 判断用户是不是他人的关注者
    def is_following(self, user):
        return self.followed.filter_by(followed_id=user.id).first() is not None

    # 是否被别人关注
    def is_follwed_by(self, user):
        return self.followers.filter_by(follower_id=user.id) is not None

    # 关注别人
    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    # 取消关注
    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    # 获取所关注用户的文章
    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id) \
            .filter(Follow.follower_id == self.id)

    # 一对多
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)

    email = db.Column(db.String(64), unique=True, index=True)

    # 用于资料信息
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)

    # 缓存gravatar的hash值
    avatar_hash = db.Column(db.String(32))

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

        # 设置自己的是自己的粉丝
        self.follow(self)

        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()

    # 记录用户最近一次登录时间
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    # 密码相关===》》
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('还是不要看人密码了吧！！！')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # 《《===密码相关

    # 注册token校验===》》
    confirmed = db.Column(db.Boolean, default=False)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    # 重置邮箱需要先发送携带token的邮件到新邮箱中
    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    # 生成用户头像
    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    # 更新之前的用户，将自己设为自己的粉丝
    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    # 生成假数据
    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        # import forgery_py
        from faker import Faker
        fake = Faker("zh_CN")
        seed()
        for i in range(count):
            # u = User(email=forgery_py.internet.email_address(),
            #          username=forgery_py.internet.user_name(True),
            #          password=forgery_py.lorem_ipsum.word(),
            #          confirmed=True,
            #          name=forgery_py.name.full_name(),
            #          location=forgery_py.address.city(),
            #          about_me=forgery_py.lorem_ipsum.sentence(),
            #          member_since=forgery_py.date.date(True))
            u = User(email=fake.email(),
                     username=fake.user_name(),
                     password=fake.password(length=10, special_chars=True, digits=True, upper_case=True,
                                            lower_case=True),
                     confirmed=True,
                     name=fake.name(),
                     location=fake.city(),
                     about_me=fake.sentence(nb_words=6, variable_nb_words=True),
                     member_since=fake.date_time(tzinfo=None))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def __repr__(self):
        return '<User %r>' % self.username


# 使用flask-login需要实现的回调方法
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
