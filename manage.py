#!/usr/bin/env python
import os
from app import create_app, db
from app.models import User, Role, Post
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, Post=Post)


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def deploy():
    from flask_migrate import upgrade, init, migrate
    from app.models import User
    # 把数据库迁移到最新修订版本 ,
    # 在heroku server上创建的目录、文件跟web app根本不在一个环境里。所以，db migration三条命令(init/migrate/uprade)必须在Bash里一并运行完，不能一条条运行
    #init()
    migrate()
    upgrade()
    # 让所有用户都关注此用户
    User.add_self_follows()


@manager.command
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


if __name__ == '__main__':
    manager.run()
