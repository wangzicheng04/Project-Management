from flask import render_template, session, redirect, url_for, Blueprint, flash, request
from flask_login import login_required, current_user
from ..models import User, db

main_bp = Blueprint('main', __name__)

@main_bp.route('/user')
@login_required
def user_dashboard():
    return render_template('dashboard.html', username=current_user.username)

@main_bp.route('/admin')
@login_required
def admin_page():
    if current_user.role != 'admin':
        return "无权限访问", 403
    return render_template('admin.html', username=current_user.username)

@main_bp.route('/')
def home():
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)

@main_bp.route('/underwater')
@login_required
def underwater():
    return render_template('underwater.html', username=current_user.username)

@main_bp.route('/intelligence')
@login_required
def intelligence():
    return render_template('intelligence.html', username=current_user.username)

@main_bp.route('/weather')
@login_required
def weather():
    return render_template('weather.html', username=current_user.username)

@main_bp.route('/datacenter')
@login_required
def datacenter():
    return render_template('datacenter.html', username=current_user.username)

@main_bp.route('/admin/users')
@login_required
def manage_users_page():
    if current_user.role != 'admin':
        flash('您没有权限访问此页面。', 'warning')
        return redirect(url_for('main.user_dashboard'))
    
    users = User.query.all()
    return render_template('manage_users.html', username=current_user.username, users=users)

@main_bp.route('/add_user', methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        flash('操作失败：权限不足。', 'danger')
        return redirect(url_for('main.manage_users_page'))

    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('用户名和密码不能为空。', 'warning')
        return redirect(url_for('main.manage_users_page'))

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash('用户名已存在，请使用其他名称。', 'warning')
        return redirect(url_for('main.manage_users_page'))

    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    
    flash(f'用户 {username} 已成功添加！', 'success')
    return redirect(url_for('main.manage_users_page'))

@main_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('操作失败：权限不足。', 'danger')
        return redirect(url_for('main.manage_users_page'))

    user_to_delete = User.query.get_or_404(user_id)

    if user_to_delete.username == 'admin':
        flash('不能删除主管理员账户！', 'danger')
        return redirect(url_for('main.manage_users_page'))

    if user_to_delete.id == current_user.id:
        flash('不能删除当前登录的账户。', 'danger')
        return redirect(url_for('main.manage_users_page'))

    db.session.delete(user_to_delete)
    db.session.commit()

    flash(f'用户 {user_to_delete.username} 已被删除。', 'success')
    return redirect(url_for('main.manage_users_page'))