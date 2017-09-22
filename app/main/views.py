from flask import render_template, session, redirect, url_for, current_app, abort, flash
from .. import db
from ..models import User,Role
from . import main
from .forms import NameForm, EditProfileForm,EditProfileAdminForm

from flask_login import login_required, current_user
from .. import admin_permission

@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@main.route("/user/<username>")
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    return render_template("user.html", user=user)


# 普通用户的编辑资料
@main.route("/edit-profile", methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash("更新成功！")
        return redirect(url_for(".user",username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me = current_user.about_me
    return render_template("edit_profile.html",form=form)

#　管理员级别的编辑资料
@main.route("/edit-profile/<int:id>", methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.roles = []
        user.roles.append(Role.query.get(form.role.data))
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('个人资料已更新！')
        return redirect(url_for('main.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.roles
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)