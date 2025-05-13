from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)

            # 根据角色跳转
            if user.role == 'admin':
                return redirect(url_for('main.admin_dashboard'))  # 管理员页面
            else:
                return redirect(url_for('main.user_dashboard'))  # 普通用户页面
        flash('用户名或密码错误')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'user')  # 管理员注册时手动赋权
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
        else:
            new_user = User(username=username, password=generate_password_hash(password), role=role)
            db.session.add(new_user)
            db.session.commit()
            flash('注册成功，请登录')
            return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('main.home'))
