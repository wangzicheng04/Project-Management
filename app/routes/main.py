from flask import Blueprint, render_template
from flask_login import login_required, current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/user')
@login_required
def user_dashboard():
    if current_user.role != 'user':
        return "无权限访问", 403
    return render_template('dashboard.html', username=current_user.username)

@main_bp.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return "无权限访问", 403
    return render_template('intelligence.html', username=current_user.username)

@main_bp.route('/')
def home():
    return render_template('index.html')