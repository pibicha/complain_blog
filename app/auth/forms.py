from flask.ext.wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp,EqualTo
from wtforms import ValidationError
from ..models import User


class LoginForm(FlaskForm):
    email = StringField('邮箱', validators=[Required("必填项"), Length(1, 64),
                                          Email()])
    password = PasswordField('密码', validators=[Required("必填项")])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登陆')


class RegistrationForm(FlaskForm):
    email = StringField("邮箱", validators=[Required("必填项"), Length(1, 64),
                                          Email()])
    username = StringField("用户名", validators=[Required("必填项"), Length(1, 64),
                                              Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                     '用户名必须是字母、数字、点和下划线组成')])
    password = PasswordField('密码',validators=[Required("必填项"),EqualTo('password2',
                                                                 message='两次输入的密码不相符！')])
    password2 = PasswordField('确认密码',validators=[Required("必填项")])

    submit = SubmitField('注册')

    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已经被注册.')
    def validate_username(self,field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已经被使用.')

# 修改密码
class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('原密码', validators=[Required("必填项")])
    password = PasswordField('新密码', validators=[
        Required("必填项"), EqualTo('password2', message='两次输入的密码不匹配')])
    password2 = PasswordField('确认新密码', validators=[Required("必填项")])
    submit = SubmitField('更新密码')

# 更新邮箱
class ChangeEmailForm(FlaskForm):
    email = StringField('新的邮箱地址', validators=[Required("必填项"), Length(1, 64),
                                                 Email()])
    password = PasswordField('密码', validators=[Required("必填项")])
    submit = SubmitField('更新邮箱地址')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已经被使用了!')