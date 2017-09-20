from flask import render_template, redirect, request, url_for, flash
from flask.ext.login import login_user, login_required, logout_user, current_user
from . import auth
from .forms import LoginForm, RegistrationForm, ChangePasswordForm
from ..models import User
from .. import db
from ..email import send_email


@auth.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('无效的用户名或密码')

    return render_template('auth/login.html', form=form)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("你已经退出登陆")
    return redirect(url_for("main.index"))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, '请确认你的账户', 'auth/email/confirm', user=user,
                   token=token)
        flash('注册验证邮件已发送，请查收')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)


# 重新获取验证邮件
@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, '请确认你的账户',
               'auth/email/confirm', user=current_user, token=token)
    flash('注册验证邮件已发送，请查收')
    return redirect(url_for('main.index'))


# 确认注册
@auth.route("/confirm/<token>")
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('注册完成~！')
    else:
        flash("无效的注册信息")
    return redirect(url_for('main.index'))


# 每次请求前检查登录状态和是否已经确认注册邮件
@auth.before_app_request
def before_request():
    if current_user.is_authenticated \
            and not current_user.confirmed \
            and request.endpoint[:5] != 'auth.' \
            and request.endpoint != 'static':
        return redirect(url_for("auth.uncofirmed"))


@auth.route("/unconfirmed")
def uncofirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for("main.index"))
    return render_template("auth/uncofirmed.html")


# 修改密码
@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash('你的密码已经更新~')
            return redirect(url_for('main.index'))
        else:
            flash('无效的密码.')
    return render_template("auth/change_password.html", form=form)
