from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登录')

class ArticleForm(FlaskForm):
    title = StringField('文章标题', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('文章内容 (支持 Markdown)', validators=[DataRequired()])
    submit = SubmitField('发布')
