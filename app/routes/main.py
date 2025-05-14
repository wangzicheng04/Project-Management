from flask import Blueprint, render_template
from flask_login import login_required, current_user

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