from flask import render_template, session, redirect, url_for, Blueprint, flash, request, jsonify
from flask_login import login_required, current_user
from ..models import User, db, WaterQuality
from datetime import datetime, timedelta
from sqlalchemy import func

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

@main_bp.route('/api/water_quality_history')
def water_quality_history_api():
    data_type = request.args.get('dataType', 'temperature')
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    # 支持分页
    page = int(request.args.get('page', 10))
    page_size = int(request.args.get('page_size', 10))
    offset = (page - 1) * page_size

    # 时间解析
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
    except (ValueError, TypeError):
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

    # 列映射
    column_map = {
        'temperature': WaterQuality.temperature,
        'ph': WaterQuality.pH,
        'oxygen': WaterQuality.dissolved_oxygen,
        'turbidity': WaterQuality.turbidity,
        'conductivity': WaterQuality.conductivity
    }
    selected_column = column_map.get(data_type, WaterQuality.temperature)

    # 图表：按日聚合
    query = db.session.query(
        func.date(WaterQuality.monitor_time).label('date'),
        func.avg(selected_column).label('avg_value')
    ).filter(
        WaterQuality.monitor_time.between(start_date, end_date),
        selected_column.isnot(None)
    ).group_by('date').order_by('date')

    results = query.all()

    # 表格总数（用于分页）
    total = db.session.query(func.count()).filter(
        WaterQuality.monitor_time.between(start_date, end_date)
    ).scalar()

    # 分页数据
    table_query = WaterQuality.query.filter(
        WaterQuality.monitor_time.between(start_date, end_date)
    ).order_by(WaterQuality.monitor_time.desc()).offset(offset).limit(page_size)

    table_data = [
        {
            'time': record.monitor_time.strftime('%Y-%m-%d %H:%M'),
            'temperature': record.temperature,
            'ph': record.pH,
            'oxygen': record.dissolved_oxygen,
            'turbidity': record.turbidity,
            'conductivity': record.conductivity,
            'status': record.station_status
        }
        for record in table_query
    ]

    return jsonify({
        'labels': [r.date for r in results],
        'data': [round(r.avg_value, 2) if r.avg_value else 0 for r in results],
        'tableData': table_data,
        'total': total,
        'page': page,
        'page_size': page_size
    })