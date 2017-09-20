from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from . import mail
#　使邮件模板支持中文 http://www.jianshu.com/p/f2b72faf268e
from email import charset
charset.add_charset('utf-8', charset.SHORTEST, charset.BASE64, 'utf-8')


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message('吐槽社区' + subject,
                  sender=current_app.config['MAIL_USERNAME'], recipients=[to],
                  charset='utf-8')#charset='utf-8' 使模板支持中文
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr
