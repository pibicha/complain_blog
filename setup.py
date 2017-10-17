# -*-coding:utf8-*-
from setuptools import setup, find_packages

setup(
    long_description=__doc__,  # 从代码中获取文档注释
    name='complain_blog',  # 应用名
    version='0.1',  # 版本号
    packages=find_packages(),  # 包括在安装包内的Python包
    include_package_data=True,  # 启用清单文件MANIFEST.in
    py_modules=["manage", "config"],
)
