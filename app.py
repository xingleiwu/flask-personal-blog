from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import markdown
from markupsafe import Markup

from config import Config
from models import db, Article, AdminUser, SiteSetting
from forms import LoginForm, ArticleForm

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录'

@login_manager.user_loader
def load_user(username):
    if username == app.config['ADMIN_USERNAME']:
        return AdminUser(username)
    return None

VALID_PAGE_SIZES = [5, 10, 20, 50]

def get_per_page():
    value = SiteSetting.get('per_page', '10')
    per_page = int(value)
    if per_page not in VALID_PAGE_SIZES:
        per_page = 10
    return per_page

def init_db():
    with app.app_context():
        db.create_all()
        if Article.query.count() == 0:
            sample_articles = [
                Article(
                    title='欢迎来到我的博客',
                    content='# 欢迎\n\n这是我的第一篇博客文章！\n\n## 功能介绍\n\n- 支持 **Markdown** 语法\n- 代码高亮\n- 搜索功能\n\n```python\nprint("Hello, World!")\n```'
                ),
                Article(
                    title='Flask 入门指南',
                    content='# Flask 入门\n\nFlask 是一个轻量级的 Python Web 框架。\n\n## 快速开始\n\n```python\nfrom flask import Flask\napp = Flask(__name__)\n\n@app.route("/")\ndef hello():\n    return "Hello World!"\n```'
                ),
                Article(
                    title='SQLAlchemy 常用操作',
                    content='# SQLAlchemy 教程\n\n## 查询操作\n\n```python\n# 查询所有\narticles = Article.query.all()\n\n# 按条件查询\narticle = Article.query.get(1)\n\n# 排序\narticles = Article.query.order_by(Article.created_at.desc()).all()\n```'
                )
            ]
            db.session.add_all(sample_articles)
            db.session.commit()
            print('示例文章已添加')
        if not SiteSetting.get('per_page'):
            SiteSetting.set('per_page', '10')
            print('默认分页设置已初始化')

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = get_per_page()
    articles = Article.query.order_by(Article.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return render_template('index.html', articles=articles)

@app.route('/article/<int:article_id>')
def article_detail(article_id):
    article = Article.query.get_or_404(article_id)
    html_content = Markup(markdown.markdown(
        article.content,
        extensions=['fenced_code', 'codehilite', 'tables', 'toc']
    ))
    return render_template('article.html', article=article, html_content=html_content)

@app.route('/search')
def search():
    keyword = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = get_per_page()
    
    if keyword:
        articles = Article.query.filter(
            Article.title.contains(keyword)
        ).order_by(Article.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    else:
        articles = Article.query.order_by(Article.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    return render_template('index.html', articles=articles, keyword=keyword)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin'))
    
    form = LoginForm()
    if form.validate_on_submit():
        if (form.username.data == app.config['ADMIN_USERNAME'] and
            check_password_hash(app.config['ADMIN_PASSWORD_HASH'], form.password.data)):
            user = AdminUser(form.username.data)
            login_user(user)
            flash('登录成功！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin'))
        else:
            flash('用户名或密码错误', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出登录', 'info')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    articles = Article.query.order_by(Article.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return render_template('admin.html', articles=articles)

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if request.method == 'POST':
        per_page = request.form.get('per_page', '10')
        if int(per_page) in VALID_PAGE_SIZES:
            SiteSetting.set('per_page', per_page)
            flash(f'分页大小已更新为每页 {per_page} 条', 'success')
        else:
            flash('无效的分页大小', 'danger')
        return redirect(url_for('admin_settings'))
    current_per_page = get_per_page()
    return render_template('admin.html', 
        articles=None, 
        current_per_page=current_per_page, 
        page_sizes=VALID_PAGE_SIZES,
        show_settings=True)

@app.route('/admin/article/new', methods=['GET', 'POST'])
@login_required
def new_article():
    form = ArticleForm()
    if form.validate_on_submit():
        article = Article(
            title=form.title.data,
            content=form.content.data
        )
        db.session.add(article)
        db.session.commit()
        flash('文章发布成功！', 'success')
        return redirect(url_for('article_detail', article_id=article.id))
    return render_template('edit_article.html', form=form, title='发布新文章')

@app.route('/admin/article/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    article = Article.query.get_or_404(article_id)
    form = ArticleForm(obj=article)
    if form.validate_on_submit():
        article.title = form.title.data
        article.content = form.content.data
        db.session.commit()
        flash('文章更新成功！', 'success')
        return redirect(url_for('article_detail', article_id=article.id))
    return render_template('edit_article.html', form=form, title='编辑文章', article=article)

@app.route('/admin/article/<int:article_id>/delete', methods=['POST'])
@login_required
def delete_article(article_id):
    article = Article.query.get_or_404(article_id)
    db.session.delete(article)
    db.session.commit()
    flash('文章已删除', 'info')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
