from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
from werkzeug.utils import secure_filename
import json
import os
import math

with open('config.json', 'r') as f:
    params = json.load(f)["params"]

local_server = True

app = Flask(__name__)
app.secret_key = "super-secret-key"

app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']
)

mail = Mail(app)

if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)

class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    tagline = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    img_file = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(12), nullable=True)


@app.route("/", methods = ['GET'], defaults = {"page":1})
@app.route("/<int:page>", methods = ['GET'])
def home(page):
    total_posts = Posts.query.all()
    page = page
    posts = Posts.query.order_by(Posts.date.desc()).paginate(page=page, per_page = params['no_of_posts'], error_out=False)
    return render_template('index.html', params = params, posts = posts)



@app.route("/about")
def about():
    return render_template('about.html', params = params)




@app.route("/dashboard", methods = ['GET', 'POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin-user']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params = params, posts = posts)
    
    if(request.method == 'POST'):
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if(username == params['admin-user'] and userpass == params['admin-password']):
            posts = Posts.query.all()
            session['user'] = username
            return render_template('dashboard.html', params = params, posts = posts)
        
    return render_template('login.html', params = params)





@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if (request.method == 'POST'):
        name = request.form.get('name')
        phone = request.form.get('phone')
        Email = request.form.get('email')
        message = request.form.get('message')
        entry = Contacts(name = name, phone_num = phone, msg = message, email = Email, date = datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message("New mail from " + name,
                           sender = Email,
                           recipients = [params['gmail-user']],
                           body = "Message : \n" + message + "\n" + " Phone number : " + phone
                        )
    return render_template("contact.html", params = params)



@app.route("/post/<string:post_slug>", methods = ['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug = post_slug).first()
    return render_template("post.html", params = params, post = post)




@app.route("/edit/<string:sno>", methods = ['GET', 'POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin-user']):
        btn_name = params['btn-add'] if sno == '0' else params['btn-edit']
        if request.method == 'POST':
            title = request.form.get('title')
            tagline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')

            if sno == '0':
                post = Posts(title = title, 
                            tagline = tagline,
                            slug = slug, 
                            content = content, 
                            img_file = img_file,
                            date = datetime.now())
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno = sno).first()
                post.title = title
                post.tagline = tagline
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date = datetime.now()
                db.session.commit()
                return redirect('/edit/'+sno)
        post = post = Posts.query.filter_by(sno = sno).first()
        return render_template('edit.html', params = params, post = post, btn_name = btn_name, sno = sno)
    


    
@app.route("/uploader", methods = ['GET', 'POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin-user']):
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "File Uploaded Successfully"
        

@app.route("/logout")
def logout():
    if ('user' in session and session['user'] == params['admin-user']):
        session.pop('user')
    return redirect("/dashboard")



@app.route("/delete/<string:sno>", methods = ['GET', 'POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin-user']):
        post = Posts.query.filter_by(sno = sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/dashboard")



app.run(debug = True)