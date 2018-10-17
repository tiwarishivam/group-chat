from app import app
from flask import render_template,flash,redirect,url_for,session
from app.forms import LoginForm
from flask_login import current_user, login_user
from app import db
from app.models import User,chatrooms,chatrooms_and_subscribers
from flask_login import logout_user
from flask_login import login_required
from app.forms import RegistrationForm
from flask import request
from werkzeug.urls import url_parse
from datetime import datetime

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/user/<username>')
@login_required
def index(username):
    user = User.query.filter_by(username=username).first_or_404()
    connection = db.session.connection()
    subscribed=connection.execute(
        'select c.chatroom_name from chatrooms_and_subscribers c join user u on u.id=c.subscribers_id where u.username=?'
        ,(username)
    )
    return render_template('index.html', user=user, subscribed=subscribed)

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index',username=current_user.username))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index',username=current_user.username)
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

from app.forms import EditProfileForm

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edituserprofile.html', title='Edit Profile',
                           form=form)

@app.route('/create',methods=['GET','POST'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form['chatroom_name']
        error = None
        chatname=chatrooms.query.filter_by(name=name).first()
        if chatname is not None:
            error='name already taken'

        if not name:
            error = 'chat group name is required.'

        if error is not None:
            flash(error)
        else:
            connection =  db.session.connection()
            connection.execute(
                'INSERT INTO chatrooms (name,creator)'
                ' VALUES (?, ?)',
                (name,current_user.id)
            )
            connection.execute(
                'INSERT INTO chatrooms_and_subscribers (chatroom_name,subscribers_id)'
                ' VALUES (?, ?)',
                (name, current_user.id)
            )
            db.session.commit()
            flash('you can now chat in this chatroom')
            return redirect(url_for('index',username=current_user.username))

    return render_template('create.html')

@app.route('/search', methods=('GET', 'POST'))
@login_required
def search():
    if request.method == 'POST':
        groupname = request.form['chatroom_name']
        error = None
        if not groupname:
            error='enter name to search'
        connection = db.session.connection()
        '''registered_group = connection.execute(
            'SELECT id FROM chatrooms_and_subscribers '
            'WHERE chatroom_name=? AND subscribers_id=?'
            , (groupname, current_user.id)
        )
        connection.close()
        print(registered_group)
        if registered_group is not None:
            error='you are already subscribed to this group' '''
        if error is not None:
            flash(error)
        else:
            matching_names=connection.execute(
                'select name from chatrooms where name=?',(groupname,)
            )
            if matching_names is not None:
                return render_template('search.html',matching_names=matching_names)
            else:
                flash('no gruop exits with this name')
    return render_template('search.html')

@app.route('/chat/<room>')
def chat(room):
    session['name']=current_user.username
    session['room']=room
    name=current_user.username
    if name == '' or room == '':
        return redirect(url_for('index'))
    return render_template('chat.html', name=name, room=room)

@app.route('/join/<name>')
def joinroom(name):
    connection = db.session.connection()
    connection.execute(
        'INSERT INTO chatrooms_and_subscribers (chatroom_name,subscribers_id)'
        ' VALUES (?, ?)',
        (name, current_user.id)
    )
    db.session.commit()
    flash('you joined the room')
    return redirect(url_for('index',username=current_user.username))

