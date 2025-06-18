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
    """
    一个API端点，用于根据查询参数返回水质历史数据。
    """
    # 1. 从请求参数中获取查询条件
    data_type = request.args.get('dataType', 'temperature') # 默认为'temperature'
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    # 2. 将字符串日期转换为 datetime 对象
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        # 结束日期需要包含当天，所以我们设置为当天的 23:59:59
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
    except (ValueError, TypeError):
        # 如果日期格式错误或为空，则默认查询最近30天的数据
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

    # 3. 根据 data_type 选择要查询的数据库列
    column_map = {
        'temperature': WaterQuality.temperature,
        'ph': WaterQuality.pH,
        'oxygen': WaterQuality.dissolved_oxygen,
        'turbidity': WaterQuality.turbidity,
        'conductivity': WaterQuality.conductivity
    }
    selected_column = column_map.get(data_type, WaterQuality.temperature)

    # 4. 从数据库查询数据 (日平均值)
    query = db.session.query(
        func.date(WaterQuality.monitor_time).label('date'),
        func.avg(selected_column).label('avg_value')
    ).filter(
        WaterQuality.monitor_time.between(start_date, end_date),
        selected_column.isnot(None)
    ).group_by('date').order_by('date')
    
    results = query.all()

    # 5. 格式化图表数据
    labels = [result.date for result in results]
    data_points = [round(result.avg_value, 2) if result.avg_value is not None else 0 for result in results]
    
    # 6. 获取表格的详细数据记录
    table_records_query = WaterQuality.query.filter(
        WaterQuality.monitor_time.between(start_date, end_date)
    ).order_by(WaterQuality.monitor_time.desc()).limit(10)
    
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
        for record in table_records_query
    ]

    # 7. 以JSON格式返回所有数据
    return jsonify({
        'labels': labels,
        'data': data_points,
        'tableData': table_data
    })