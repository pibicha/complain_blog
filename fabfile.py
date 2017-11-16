from fabric.api import *

# 使用远程命令的用户名
env.user = 'XXX'
env.password = 'XXX'
# 执行命令的服务器
env.hosts = ['XX.XX.XX.XX']


def pack():
    # 创建一个新的分发源，格式为tar压缩包
    local('python3 setup.py sdist --formats=gztar', capture=False)


def deploy():
    run('rm -rf /tmp/myapp /tmp/myapp.tar.gz')
    # 定义发布版本的名称和版本号
    dist = local('python3 setup.py --fullname', capture=True).strip()
    # 把tar压缩包格式的源代码上传到服务器的临时文件夹
    put('dist/%s.tar.gz' % dist, '/tmp/myapp.tar.gz')
    # 创建一个用于解压缩的文件夹，并进入该文件夹
    run('mkdir /tmp/myapp')
    with cd('/tmp/myapp'):
        run('tar xzf /tmp/myapp.tar.gz')
        # 使用虚拟环境的python解释器来安装包
        install_order = '/root/python-venv/bin/python /tmp/myapp/%s/setup.py install' % dist
        run(install_order)
    run('cp -rf /tmp/myapp/%s /root/python-venv' % dist)
    run('rm -rf /tmp/myapp /tmp/myapp.tar.gz')
    # 启动程序
    run('/root/python-venv/bin/python /root/python-venv/%s/manage.py runserver -h 192.168.1.90' % dist)


def start():
    # 定义发布版本的名称和版本号
    dist = local('python3 setup.py --fullname', capture=True).strip()
    # 启动程序
    # 'nohup python manage.py runserver -h 192.168.1.90 > flush.log >&1 &'

    # 使用虚拟环境的python解释器来启动程序，
    run(
        '/root/python-venv/bin/python -u /root/python-venv/%s/manage.py runserver -h XX.XX.XX.XX' % dist)
