from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField
from wtforms.validators import Required, Length, Email, Regexp, ValidationError, DataRequired
from ..models import User, Role


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[Required("必填项")])
    submit = SubmitField('Submit')


# 普通用户的编辑资料
class EditProfileForm(FlaskForm):
    name = StringField('真实姓名', validators=[Length(0, 64)])
    location = StringField('家庭住址', validators=[Length(0, 64)])
    about_me = TextAreaField('个性签名')
    submit = SubmitField('提交')


# 管理员级别的编辑资料
class EditProfileAdminForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired("必填项"), Length(1, 64),
                                          Email()])
    username = StringField('用户名', validators=[
        DataRequired("必填项"), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                   '用户名必须为字母、数字、下划线组成')])
    confirmed = BooleanField('是否认证')
    role = SelectField('权限角色', coerce=int)
    name = StringField('真实姓名', validators=[Length(0, 64)])
    location = StringField('家庭住址', validators=[Length(0, 64)])
    about_me = TextAreaField('个性签名')
    submit = SubmitField('提交')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已被注册')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已被使用')

# 文章
class PostForm(FlaskForm):
    body = TextAreaField("你在想什么？",validators=[Required()])
    submit = SubmitField("提交")