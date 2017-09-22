from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField
from wtforms.validators import Required, Length, Email, Regexp, ValidationError,DataRequired
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



