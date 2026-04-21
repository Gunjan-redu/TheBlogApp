import datetime
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import math
from flask_login import LoginManager, login_user, logout_user, current_user, login_required, UserMixin


app = Flask(__name__)

with open("config.json","r") as c:
    param = json.load(c)["parameters"]

if param['local_server'] :
    app.config['SQLALCHEMY_DATABASE_URI'] = param['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = param['prod_uri']
app.config['SECRET_KEY']=param['secret_key']
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class Posts(db.Model):
    post_id = db.Column('post_id',db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    sub_title = db.Column(db.String(200))
    location = db.Column(db.String(50))
    author = db.Column(db.String(30))
    date_posted = db.Column(db.Date)
    image = db.Column(db.String(300))
    content_1= db.Column(db.Text)
    content_2 = db.Column(db.Text)
    slug = db.Column(db.String(100), unique=True)

class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(150), nullable=False)
    date = db.Column(db.Date)

class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(50), nullable=False)

@app.route('/')
def home():
    post_data = Posts.query.all()
    pages = math.ceil(len(post_data)/3)

    page = request.args.get('page')

    if page is None:
        page = 1
    next = "/?page=" + str(int(page)+1)
    prev = "/?page=" + str(int(page)-1)
    page = int(page)
    if page == 2:
        next = "#"
        prev = "/?page=" + str(int(page)-1)
        page = 1
    elif page == 1:
        next    = "/?page="+str(int(page)+1)
        prev = "/?page=" + str(1)
    j = (int(page) - 1) * 3
    posts = post_data[j:j + 3]
    return render_template('index.html', param=param, posts=posts, prev = prev, next = next)

@app.route('/post')
def post():
        return render_template('post.html', param=param)

@app.route('/about')
def about():
    return render_template('about.html', param=param)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        entry = Contact(name=name, email=email, message=message, date = datetime.datetime.now())
        db.session.add(entry)
        db.session.commit()
    return render_template('contact.html', param=param)

admin_user = "abc"
admin_pass = "123"

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        password = request.form['password']
        user = Users.query.filter_by(username=user).first()
        if user  and user.password == password:
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Please check your login details and try again.")
    return render_template('login.html', param=param)

@app.route("/admin", methods = ['GET', 'POST'])
@login_required
def dashboard():
        user = current_user.name
        style = ""
        posts = Posts.query.filter_by(author = user).all()
        contacts = Contact.query.filter_by().all()
        if not current_user.username == "alex456":
            style = "display: none;"
        return render_template('admin/index.html', param=param, posts=posts, contacts=contacts)

@app.route("/post/<slug>", methods=['GET'])
def slug(slug):
    single_post = Posts.query.filter_by(slug=slug).first()
    print(single_post)
    return render_template('post.html', param=param, post=single_post)

@app.route("/editPost/<post_id>", methods=['GET', 'POST'])
def edit(post_id):
  if  request.method == 'POST':
        ntitle = request.form.get('title')
        nsubtitle = request.form.get('subtitle')
        nlocation = request.form.get('location')
        nslug = request.form.get('slug')
        author = request.form.get('author')
        date = request.form.get('date')
        image = request.form.get('image')
        content1 = request.form.get('content1')
        content2 = request.form.get('content2')
        if post_id == "0":
            post = Posts(title=ntitle, sub_title=nsubtitle, location=nlocation, slug=nslug, date_posted = date, author=author, image=image, content_1=content1, content_2=content2)
            db.session.add(post)
            db.session.commit()
        else:
            post = Posts.query.filter_by(post_id =post_id).first()
            post.title = ntitle
            post.sub_title = nsubtitle
            post.author = author
            post.image = image
            post.location = nlocation
            post.date_posted = date
            post.content_1 = content1
            post.content_2 = content2
            post.slug = nslug
            db.session.commit()
            return redirect(url_for('dashboard'))

  post = Posts.query.filter_by(post_id=post_id).first()
  return render_template("admin/editPost.html", param=param, post=post)

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        username = request.form.get('username')
        new_user = Users(name=name, email=email, password=password, username=username)

        user = Users.query.filter_by(email=email).first()
        if user :
            flash("Email already exists")
            return redirect(url_for('signup'))
        db.session.add(new_user)
        db.session.commit()
    return render_template('admin/signup.html', param=param)

@app.route('/delete/<string:post_id>', methods=['GET', 'POST'])
def delete(post_id):
    post = Posts.query.filter_by(post_id=post_id).first()
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('dashboard'))

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
if __name__=='__main__':
    with app.app_context():

        db.create_all()
    app.run(debug=True,port='8082')