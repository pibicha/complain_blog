from flask import render_template, redirect, request, url_for, flash
from flask.ext.login import login_user, login_required, logout_user, current_user
from . import auth
from .forms import LoginForm, RegistrationForm
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
        flash("请确认你的邮箱")
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)


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
            and request.endpoint() != 'static':
        return redirect(url_for("auth.uncofirmed"))


@auth.route("/unconfirmed")
def uncofirmed():
    if current_user.is_anonymous() or current_user.confirmed:
        return redirect(url_for("main.index"))
    return render_template("auth/uncofirmed.html")
