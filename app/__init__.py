from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

from flask.ext.login import current_user
from flask_principal import Principal, Permission, RoleNeed,identity_loaded,UserNeed

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
login_manager = LoginManager()
# 使用principal实现权限管理
principals = Principal()

# Create a permission with a single Need, in this case a RoleNeed.
user_permission = Permission(RoleNeed('user'))
moderator_permission = Permission(RoleNeed('moderate'))
amdin_permission = Permission(RoleNeed('admin'))

# 自定义访问未授权资源时的闪现消息
login_manager.login_message = "请先登录！"

login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    principals.init_app(app)

    # principle权限相关
    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        # Set the identity user object
        identity.user = current_user

        # Add the UserNeed to the identity
        if hasattr(current_user, 'id'):
            identity.provides.add(UserNeed(current_user.id))

        # Assuming the User model has a list of roles, update the
        # identity with the roles that the user provides
        if hasattr(current_user, 'roles'):
            for role in current_user.roles:
                identity.provides.add(RoleNeed(role.name))

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    return app
