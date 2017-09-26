from flask import render_template, session, redirect, url_for, current_app, abort, flash
from .. import db
from ..models import User, Role, Post
from . import main
from .forms import NameForm, EditProfileForm, EditProfileAdminForm, \
    PostForm

from flask_login import login_required, current_user
from .. import admin_permission, user_permission, Permission, UserNeed
from flask import request

from flask_principal import Principal, Identity, AnonymousIdentity, \
    identity_changed, IdentityContext


@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if form.validate_on_submit():
        # current_user是轻度封装，_get_current_object才是类似于user的对象
        user_permission = Permission(UserNeed(current_user._get_current_object().id))
        if user_permission.can():
            post = Post(body=form.body.data,
                        author=current_user._get_current_object())
            db.session.add(post)
            return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    # posts = Post.query.order_by(Post.timestamp.desc()).all()
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    return render_template('index.html', form=form, posts=pagination.items, pagination=pagination)


@main.route("/user/<username>")
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    return render_template("user.html", user=user, posts=pagination.items, pagination=pagination)


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
        return redirect(url_for(".user", username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me = current_user.about_me
    return render_template("edit_profile.html", form=form)


# 　管理员级别的编辑资料
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


# 文章分享
@main.route("/post/<int:id>")
def post(id):
    post = Post.query.get_or_404(id)
    return render_template('post.html', posts=[post])


# 编辑文章
@main.route("/edit/<int:id>", methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if not admin_permission.can() and current_user != post.author:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash("内容已更新！")
        return redirect(url_for('main.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)


# 关注
@main.route('/follow/<username>')
@login_required
@user_permission.require()
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("找不到{}哦！".format(username))
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash("你已经关注过{}啦！".format(username))
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    flash('你已关注%s.' % username)
    return redirect(url_for('.user', username=username))


# 取消关注
@main.route('/unfollow/<username>')
@login_required
@user_permission.require()
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("找不到{}哦！".format(username))
        return redirect(url_for('.index'))
    current_user.unfollow(user)
    flash('你已取消关注%s.' % username)
    return redirect(url_for('.user', username=username))


# 查看他人粉丝
@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("找不到{}哦！".format(username))
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="的粉丝",
                           endpoint='.followers', pagination=pagination,
                           follows=follows)


# 查看他关注的人
@main.route('/followed_by/<username>')
@login_required
@user_permission.require()
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("找不到{}哦！".format(username))
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="的关注",
                           endpoint='.followers', pagination=pagination,
                           follows=follows)


# 上下文处理,可以在jinja2判断是否有执行权限
@main.app_context_processor
def context():
    admin = IdentityContext(admin_permission)
    user = IdentityContext(user_permission)
    return dict(admin_p=admin, user_p=user)
