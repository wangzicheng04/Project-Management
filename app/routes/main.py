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
    
@main_bp.route('/admin/logs')
def manage_logs_page():
    """
    渲染系统日志页面。
    """
    # 在实际应用中，您会从数据库或日志文件中查询日志
    # 这里我们使用一些模拟数据作为示例
    mock_logs = [
        {'id': 1, 'timestamp': '2023-10-27 10:00:00', 'level': 'INFO', 'message': '用户 admin 登录成功。'},
        {'id': 2, 'timestamp': '2023-10-27 10:05:12', 'level': 'WARNING', 'message': '数据库连接延迟超过 500ms。'},
        {'id': 3, 'timestamp': '2023-10-27 10:10:25', 'level': 'ERROR', 'message': '无法处理来自传感器 #102 的数据。'},
        {'id': 4, 'timestamp': '2023-10-27 10:15:03', 'level': 'INFO', 'message': '生成了每周数据报告。'}
    ]
    username = session.get('username', '游客')
    return render_template('system_logs.html', username=username, logs=mock_logs)

@main_bp.route('/api/doubao-chat', methods=['POST'])
@login_required
def doubao_chat():
    """
    智能问答API端点，集成豆包AI并提供数据查询功能
    """
    try:
        data = request.get_json()
        question = data.get('question', '')
        api_key = data.get('api_key', '')
        
        if not question:
            return jsonify({'error': '问题不能为空'}), 400
            
        if not api_key:
            return jsonify({'error': 'API Key不能为空'}), 400
        
        # 分析问题类型并获取相关数据
        context_data = analyze_question_and_get_data(question)
        
        # 构建增强的提示词
        enhanced_prompt = build_enhanced_prompt(question, context_data)
        
        # 调用豆包API（这里需要实际的API调用实现）
        # response = call_doubao_api(enhanced_prompt, api_key)
        
        # 临时模拟响应，实际使用时替换为真实API调用
        response = generate_smart_response(question, context_data)
        
        return jsonify({'response': response})
        
    except Exception as e:
        return jsonify({'error': f'服务异常: {str(e)}'}), 500

@main_bp.route('/api/fish-recognition', methods=['POST'])
def fish_recognition():
    """鱼类识别API"""
    try:
        # 检查是否有上传的文件
        if 'image' not in request.files:
            return jsonify({
                'status': 'error',
                'message': '未找到图片文件'
            }), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': '未选择文件'
            }), 400
        
        # 检查文件类型
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if not ('.' in file.filename and 
                file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({
                'status': 'error',
                'message': '不支持的文件格式'
            }), 400
        
        # 模拟鱼类识别处理
        # 在实际应用中，这里会调用深度学习模型进行图像识别
        import random
        import time
        
        # 模拟处理时间
        time.sleep(1)
        
        # 模拟识别结果
        fish_types = [
            {'name': '鲈鱼', 'confidence': 0.92, 'avg_length': '25-35cm'},
            {'name': '武昌鱼', 'confidence': 0.88, 'avg_length': '20-30cm'},
            {'name': '狗鱼', 'confidence': 0.85, 'avg_length': '30-45cm'},
            {'name': '鲤鱼', 'confidence': 0.90, 'avg_length': '25-40cm'},
            {'name': '草鱼', 'confidence': 0.87, 'avg_length': '35-50cm'}
        ]
        
        selected_fish = random.choice(fish_types)
        predicted_length = round(random.uniform(20, 35), 1)
        health_score = round(random.uniform(80, 100), 1)
        
        result = {
            'fish_type': selected_fish['name'],
            'confidence': selected_fish['confidence'],
            'predicted_length': predicted_length,
            'health_score': health_score,
            'avg_length': selected_fish['avg_length'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'recommendations': generate_fish_recommendations(selected_fish['name'], predicted_length, health_score)
        }
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'识别过程中发生错误: {str(e)}'
        }), 500

def generate_fish_recommendations(fish_type, length, health_score):
    """根据识别结果生成养殖建议"""
    recommendations = []
    
    # 根据鱼类类型给出建议
    if fish_type == '鲈鱼':
        recommendations.append('鲈鱼适宜在水温18-25°C环境中生长')
        recommendations.append('建议投喂高蛋白饲料，促进生长')
    elif fish_type == '武昌鱼':
        recommendations.append('武昌鱼喜欢清洁的水质环境')
        recommendations.append('适当增加溶解氧含量有利于健康')
    elif fish_type == '草鱼':
        recommendations.append('草鱼需要充足的植物性饲料')
        recommendations.append('定期检查水质pH值，保持在7.0-8.5')
    
    # 根据体长给出建议
    if length < 25:
        recommendations.append('鱼体较小，建议增加营养投喂')
    elif length > 35:
        recommendations.append('鱼体发育良好，可考虑适时收获')
    
    # 根据健康评分给出建议
    if health_score < 85:
        recommendations.append('健康状况需要关注，建议检查水质和饲料')
    elif health_score > 95:
        recommendations.append('鱼类健康状况优秀，继续保持当前养殖条件')
    
    return recommendations

def analyze_question_and_get_data(question):
    """
    分析问题并获取相关数据
    """
    context_data = {}
    
    # 获取最新水质数据
    if any(keyword in question for keyword in ['水质', 'pH', '温度', '溶解氧', '浊度', '电导率']):
        latest_water_data = get_latest_water_quality_data()
        context_data['water_quality'] = latest_water_data
        
        # 获取水质趋势数据
        trend_data = get_water_quality_trend()
        context_data['water_trend'] = trend_data
    
    # 获取鱼类相关数据（模拟数据）
    if any(keyword in question for keyword in ['鱼', '鱼类', '养殖', '产量', '生长']):
        fish_data = get_fish_data_simulation()
        context_data['fish_data'] = fish_data
    
    # 获取设备状态数据（模拟数据）
    if any(keyword in question for keyword in ['设备', '传感器', '摄像头', '维护']):
        equipment_data = get_equipment_status_simulation()
        context_data['equipment'] = equipment_data
    
    # 获取环境数据
    if any(keyword in question for keyword in ['环境', '天气', '气温', '湿度']):
        environment_data = get_environment_data_simulation()
        context_data['environment'] = environment_data
    
    return context_data

def get_latest_water_quality_data():
    """
    获取最新的水质数据
    """
    try:
        latest_record = WaterQuality.query.order_by(WaterQuality.monitor_time.desc()).first()
        if latest_record:
            return {
                'monitor_time': latest_record.monitor_time.strftime('%Y-%m-%d %H:%M:%S'),
                'temperature': latest_record.temperature,
                'pH': latest_record.pH,
                'dissolved_oxygen': latest_record.dissolved_oxygen,
                'turbidity': latest_record.turbidity,
                'conductivity': latest_record.conductivity,
                'quality_level': latest_record.quality_level,
                'section_name': latest_record.section_name
            }
    except Exception as e:
        print(f"获取水质数据错误: {e}")
    return None

def get_water_quality_trend():
    """
    获取水质趋势数据（最近7天）
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        trend_data = db.session.query(
            func.date(WaterQuality.monitor_time).label('date'),
            func.avg(WaterQuality.temperature).label('avg_temp'),
            func.avg(WaterQuality.pH).label('avg_ph'),
            func.avg(WaterQuality.dissolved_oxygen).label('avg_oxygen')
        ).filter(
            WaterQuality.monitor_time.between(start_date, end_date)
        ).group_by('date').order_by('date').all()
        
        return [{
            'date': str(record.date),
            'temperature': round(record.avg_temp, 2) if record.avg_temp else None,
            'pH': round(record.avg_ph, 2) if record.avg_ph else None,
            'dissolved_oxygen': round(record.avg_oxygen, 2) if record.avg_oxygen else None
        } for record in trend_data]
    except Exception as e:
        print(f"获取水质趋势数据错误: {e}")
    return []

def get_fish_data_simulation():
    """
    模拟鱼类数据
    """
    return {
        'total_fish_count': 15420,
        'species': [
            {'name': '鲈鱼', 'count': 6800, 'avg_weight': 1.2, 'growth_rate': 0.15},
            {'name': '武昌鱼', 'count': 4320, 'avg_weight': 0.8, 'growth_rate': 0.12},
            {'name': '狗鱼', 'count': 4300, 'avg_weight': 1.5, 'growth_rate': 0.18}
        ],
        'feeding_schedule': '每日3次，上午8点、下午2点、晚上6点',
        'health_status': '良好',
        'estimated_harvest_date': '2024-08-15'
    }

def get_equipment_status_simulation():
    """
    模拟设备状态数据
    """
    return {
        'total_devices': 24,
        'online_devices': 22,
        'offline_devices': 2,
        'devices': [
            {'id': 'UW001', 'type': '水下摄像头', 'status': '正常', 'last_maintenance': '2024-01-15'},
            {'id': 'UW002', 'type': '水下摄像头', 'status': '信号不稳定', 'last_maintenance': '2024-01-10'},
            {'id': 'WQ001', 'type': '水质传感器', 'status': '正常', 'last_maintenance': '2024-01-20'},
            {'id': 'WQ002', 'type': '水质传感器', 'status': '需要校准', 'last_maintenance': '2024-01-05'}
        ]
    }

def get_environment_data_simulation():
    """
    模拟环境数据
    """
    return {
        'air_temperature': 22.5,
        'humidity': 68,
        'wind_speed': 12.3,
        'weather_condition': '多云',
        'water_surface_temperature': 18.2,
        'visibility': 8.5
    }

def build_enhanced_prompt(question, context_data):
    """
    构建增强的提示词
    """
    prompt = f"""你是一个海洋牧场智能助手，请基于以下实时数据回答用户问题：

用户问题：{question}

当前数据：
"""
    
    if 'water_quality' in context_data and context_data['water_quality']:
        water_data = context_data['water_quality']
        prompt += f"""
水质数据（{water_data['monitor_time']}）：
- 温度：{water_data['temperature']}°C
- pH值：{water_data['pH']}
- 溶解氧：{water_data['dissolved_oxygen']}mg/L
- 浊度：{water_data['turbidity']}NTU
- 电导率：{water_data['conductivity']}μS/cm
- 水质等级：{water_data['quality_level']}
- 监测点：{water_data['section_name']}
"""
    
    if 'fish_data' in context_data:
        fish_data = context_data['fish_data']
        prompt += f"""
鱼类养殖数据：
- 总鱼数：{fish_data['total_fish_count']}尾
- 鱼类品种：{', '.join([f"{s['name']}({s['count']}尾)" for s in fish_data['species']])}
- 健康状况：{fish_data['health_status']}
- 预计收获时间：{fish_data['estimated_harvest_date']}
"""
    
    if 'equipment' in context_data:
        equipment_data = context_data['equipment']
        prompt += f"""
设备状态：
- 设备总数：{equipment_data['total_devices']}台
- 在线设备：{equipment_data['online_devices']}台
- 离线设备：{equipment_data['offline_devices']}台
"""
    
    prompt += """

请基于以上数据，用专业但易懂的语言回答用户问题。如果数据显示有异常情况，请提供相应的建议。
"""
    
    return prompt

def generate_smart_response(question, context_data):
    """
    基于数据生成智能响应（模拟实现）
    """
    if 'water_quality' in context_data and context_data['water_quality']:
        water_data = context_data['water_quality']
        
        if '水质' in question or 'pH' in question or '温度' in question:
            response = f"""根据最新监测数据（{water_data['monitor_time']}），当前水质状况如下：

📊 **关键指标**：

• 水温：{water_data['temperature']}°C

• pH值：{water_data['pH']}

• 溶解氧：{water_data['dissolved_oxygen']}mg/L

• 浊度：{water_data['turbidity']}NTU

• 水质等级：{water_data['quality_level']}

💡 **分析建议**：

"""
            
            # 基于实际数据给出建议
            if water_data['pH'] and (water_data['pH'] < 6.5 or water_data['pH'] > 8.5):
                response += "• ⚠️ pH值偏离正常范围，建议检查水质调节系统\n\n"
            else:
                response += "• ✅ pH值正常，水质酸碱度适宜\n\n"
                
            if water_data['dissolved_oxygen'] and water_data['dissolved_oxygen'] < 5.0:
                response += "• ⚠️ 溶解氧偏低，建议增加增氧设备运行时间\n\n"
            else:
                response += "• ✅ 溶解氧充足，有利于鱼类生长\n\n"
                
            if water_data['temperature'] and (water_data['temperature'] < 15 or water_data['temperature'] > 25):
                response += "• ⚠️ 水温需要关注，可能影响鱼类活动\n\n"
            else:
                response += "• ✅ 水温适宜，符合养殖要求\n\n"
                
            return response
    
    if 'fish_data' in context_data:
        fish_data = context_data['fish_data']
        
        if any(keyword in question for keyword in ['鱼', '鱼类', '养殖', '产量']):
            return f"""🐟 **当前养殖状况**：

📈 **数量统计**：

• 总鱼数：{fish_data['total_fish_count']:,}尾

• 鲈鱼：{fish_data['species'][0]['count']:,}尾（平均{fish_data['species'][0]['avg_weight']}kg）

• 武昌鱼：{fish_data['species'][1]['count']:,}尾（平均{fish_data['species'][1]['avg_weight']}kg）

• 狗鱼：{fish_data['species'][2]['count']:,}尾（平均{fish_data['species'][2]['avg_weight']}kg）

🎯 **生长情况**：

• 整体健康状况：{fish_data['health_status']}

• 预计收获时间：{fish_data['estimated_harvest_date']}

• 投喂计划：{fish_data['feeding_schedule']}

💡 **管理建议**：

• 继续保持现有投喂频次

• 定期监测鱼类活动状态

• 根据生长情况适时调整饲料配比

"""
    
    if 'equipment' in context_data:
        equipment_data = context_data['equipment']
        
        if any(keyword in question for keyword in ['设备', '维护', '传感器']):
            return f"""🔧 **设备运行状态**：

📊 **总体概况**：

• 设备总数：{equipment_data['total_devices']}台

• 在线设备：{equipment_data['online_devices']}台

• 离线设备：{equipment_data['offline_devices']}台

• 运行率：{(equipment_data['online_devices']/equipment_data['total_devices']*100):.1f}%

⚠️ **需要关注的设备**：

• UW002水下摄像头：信号不稳定，建议检查连接线路

• WQ002水质传感器：需要校准，建议安排技术人员处理

🔧 **维护建议**：

• 定期检查设备连接状态

• 按计划进行设备校准和保养

• 及时更换老化的传感器元件

"""
    
    # 默认响应
    return """感谢您的咨询！作为海洋牧场智能助手，我可以为您提供：

🌊 **水质监测**：实时水质参数分析和建议

🐟 **养殖管理**：鱼类生长状况和饲养指导

🔧 **设备维护**：设备状态监控和维护提醒

📈 **数据分析**：历史趋势分析和预测建议

请告诉我您想了解哪个方面的具体信息，我会基于实时数据为您提供专业的分析和建议。

"""

@main_bp.route('/data_analysis')
@login_required
def data_analysis():
    return render_template('data_analysis.html', username=current_user.username)

# ==================== 新增管理员功能路由 ====================

# 权限管理
@main_bp.route('/admin/permissions')
@login_required
def permission_management_page():
    if current_user.role != 'admin':
        flash('您没有权限访问此页面。', 'warning')
        return redirect(url_for('main.user_dashboard'))
    
    users = User.query.all()
    # 模拟审计日志数据
    audit_logs = [
        {'timestamp': '2023-12-01 10:30:00', 'operator': 'admin', 'target_user': 'user1', 'action': '提升为管理员', 'ip_address': '192.168.1.100'},
        {'timestamp': '2023-12-01 09:15:00', 'operator': 'admin', 'target_user': 'user2', 'action': '降级为普通用户', 'ip_address': '192.168.1.100'},
    ]
    return render_template('permission_management.html', username=current_user.username, users=users, audit_logs=audit_logs)

@main_bp.route('/admin/permissions/update_role/<int:user_id>', methods=['POST'])
@login_required
def update_user_role(user_id):
    if current_user.role != 'admin':
        flash('操作失败：权限不足。', 'danger')
        return redirect(url_for('main.permission_management_page'))
    
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    
    if user.username == 'admin':
        flash('不能修改主管理员角色！', 'danger')
        return redirect(url_for('main.permission_management_page'))
    
    if new_role in ['user', 'admin']:
        user.role = new_role
        db.session.commit()
        flash(f'用户 {user.username} 角色已更新为 {new_role}。', 'success')
    else:
        flash('无效的角色类型。', 'danger')
    
    return redirect(url_for('main.permission_management_page'))

@main_bp.route('/admin/permissions/update_module', methods=['POST'])
@login_required
def update_module_permissions():
    if current_user.role != 'admin':
        flash('操作失败：权限不足。', 'danger')
        return redirect(url_for('main.permission_management_page'))
    
    # 这里应该实现模块权限的更新逻辑
    flash('模块权限设置已更新。', 'success')
    return redirect(url_for('main.permission_management_page'))

# 系统设置
@main_bp.route('/admin/settings')
@login_required
def system_settings_page():
    if current_user.role != 'admin':
        flash('您没有权限访问此页面。', 'warning')
        return redirect(url_for('main.user_dashboard'))
    
    # 模拟系统配置数据
    config = {
        'system_name': '海洋管理系统',
        'data_retention_days': 365,
        'session_timeout': 30,
        'max_login_attempts': 5,
        'data_collection_interval': 300,
        'alert_threshold_temp_min': 15.0,
        'alert_threshold_temp_max': 30.0,
        'alert_threshold_ph_min': 6.5,
        'alert_threshold_ph_max': 8.5,
        'enable_alerts': True
    }
    
    # 模拟系统信息
    system_info = {
        'version': 'v1.2.0',
        'uptime': '15天 8小时 32分钟',
        'cpu_usage': 45,
        'memory_usage': 62,
        'disk_usage': 78,
        'db_size': '256 MB'
    }
    
    return render_template('system_settings.html', username=current_user.username, config=config, system_info=system_info)

@main_bp.route('/admin/settings/update_config', methods=['POST'])
@login_required
def update_system_config():
    if current_user.role != 'admin':
        flash('操作失败：权限不足。', 'danger')
        return redirect(url_for('main.system_settings_page'))
    
    # 这里应该实现系统配置的更新逻辑
    flash('系统配置已更新。', 'success')
    return redirect(url_for('main.system_settings_page'))

@main_bp.route('/admin/settings/update_monitoring', methods=['POST'])
@login_required
def update_monitoring_config():
    if current_user.role != 'admin':
        flash('操作失败：权限不足。', 'danger')
        return redirect(url_for('main.system_settings_page'))
    
    # 这里应该实现监控配置的更新逻辑
    flash('监控配置已更新。', 'success')
    return redirect(url_for('main.system_settings_page'))

@main_bp.route('/admin/settings/clear_cache', methods=['POST'])
@login_required
def clear_cache():
    if current_user.role != 'admin':
        flash('操作失败：权限不足。', 'danger')
        return redirect(url_for('main.system_settings_page'))
    
    flash('系统缓存已清理。', 'success')
    return redirect(url_for('main.system_settings_page'))

@main_bp.route('/admin/settings/optimize_db', methods=['POST'])
@login_required
def optimize_database():
    if current_user.role != 'admin':
        flash('操作失败：权限不足。', 'danger')
        return redirect(url_for('main.system_settings_page'))
    
    flash('数据库优化完成。', 'success')
    return redirect(url_for('main.system_settings_page'))

@main_bp.route('/admin/settings/restart_services', methods=['POST'])
@login_required
def restart_services():
    if current_user.role != 'admin':
        flash('操作失败：权限不足。', 'danger')
        return redirect(url_for('main.system_settings_page'))
    
    flash('系统服务重启完成。', 'success')
    return redirect(url_for('main.system_settings_page'))

# 数据导入
@main_bp.route('/admin/data_import')
@login_required
def data_import_page():
    if current_user.role != 'admin':
        flash('您没有权限访问此页面。', 'warning')
        return redirect(url_for('main.user_dashboard'))
    
    # 模拟导入历史数据
    import_history = [
        {'filename': 'water_quality_20231201.csv', 'timestamp': '2023-12-01 14:30:00', 'status': 'success'},
        {'filename': 'weather_data_20231130.xlsx', 'timestamp': '2023-11-30 16:45:00', 'status': 'success'},
        {'filename': 'equipment_logs_20231129.json', 'timestamp': '2023-11-29 09:15:00', 'status': 'failed'},
    ]
    
    return render_template('data_import.html', username=current_user.username, import_history=import_history)

@main_bp.route('/admin/data_import/upload', methods=['POST'])
@login_required
def upload_data():
    if current_user.role != 'admin':
        flash('操作失败：权限不足。', 'danger')
        return redirect(url_for('main.data_import_page'))
    
    if 'data_file' not in request.files:
        flash('请选择要上传的文件。', 'warning')
        return redirect(url_for('main.data_import_page'))
    
    file = request.files['data_file']
    if file.filename == '':
        flash('请选择要上传的文件。', 'warning')
        return redirect(url_for('main.data_import_page'))
    
    # 这里应该实现文件上传和数据导入逻辑
    flash(f'文件 {file.filename} 上传成功，数据导入完成。', 'success')
    return redirect(url_for('main.data_import_page'))

# 系统备份
@main_bp.route('/admin/backup')
@login_required
def system_backup_page():
    if current_user.role != 'admin':
        flash('您没有权限访问此页面。', 'warning')
        return redirect(url_for('main.user_dashboard'))
    
    # 模拟备份设置
    settings = {
        'auto_backup': 'weekly',
        'backup_time': '02:00',
        'retention_days': 30,
        'storage_path': '/backups'
    }
    
    # 模拟备份历史
    backups = [
        {'id': 1, 'name': '系统完整备份_20231201', 'created_at': '2023-12-01 02:00:00', 'size': '1.2 GB', 'status': 'completed', 'type': 'auto'},
        {'id': 2, 'name': '手动备份_20231130', 'created_at': '2023-11-30 15:30:00', 'size': '1.1 GB', 'status': 'completed', 'type': 'manual'},
        {'id': 3, 'name': '系统完整备份_20231123', 'created_at': '2023-11-23 02:00:00', 'size': '1.0 GB', 'status': 'completed', 'type': 'auto'},
    ]
    
    return render_template('system_backup.html', username=current_user.username, settings=settings, backups=backups)

@main_bp.route('/admin/backup/create', methods=['POST'])
@login_required
def create_backup():
    if current_user.role != 'admin':
        flash('操作失败：权限不足。', 'danger')
        return redirect(url_for('main.system_backup_page'))
    
    # 这里应该实现备份创建逻辑
    flash('系统备份创建成功。', 'success')
    return redirect(url_for('main.system_backup_page'))

@main_bp.route('/admin/backup/restore/<int:backup_id>')
@login_required
def restore_backup(backup_id):
    if current_user.role != 'admin':
        flash('操作失败：权限不足。', 'danger')
        return redirect(url_for('main.system_backup_page'))
    
    # 这里应该实现备份恢复逻辑
    flash('系统备份恢复成功。', 'success')
    return redirect(url_for('main.system_backup_page'))

@main_bp.route('/admin/backup/download/<int:backup_id>')
@login_required
def download_backup(backup_id):
    if current_user.role != 'admin':
        return "无权限", 403
    
    # 这里应该实现备份下载逻辑
    return "备份下载功能待实现", 200

@main_bp.route('/admin/backup/delete/<int:backup_id>', methods=['POST'])
@login_required
def delete_backup(backup_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 这里应该实现备份删除逻辑
    return jsonify({'success': True, 'message': '备份删除成功'})

@main_bp.route('/admin/backup/update_settings', methods=['POST'])
@login_required
def update_backup_settings():
    if current_user.role != 'admin':
        flash('操作失败：权限不足。', 'danger')
        return redirect(url_for('main.system_backup_page'))
    
    # 这里应该实现备份设置更新逻辑
    flash('备份设置已更新。', 'success')
    return redirect(url_for('main.system_backup_page'))

# 通知管理
@main_bp.route('/admin/notifications')
@login_required
def notification_management_page():
    if current_user.role != 'admin':
        flash('您没有权限访问此页面。', 'warning')
        return redirect(url_for('main.user_dashboard'))
    
    users = User.query.all()
    
    # 模拟通知模板
    templates = [
        {'id': 1, 'name': '系统维护通知', 'description': '用于系统维护时的通知模板'},
        {'id': 2, 'name': '水质警报通知', 'description': '用于水质异常时的警报通知'},
        {'id': 3, 'name': '设备故障通知', 'description': '用于设备故障时的通知模板'},
    ]
    
    # 模拟通知历史
    notifications = [
        {'id': 1, 'title': '系统维护通知', 'content': '系统将于今晚进行维护...', 'type': 'maintenance', 'priority': 'normal', 'sent_at': '2023-12-01 10:00:00', 'status': 'sent', 'recipient_count': 15},
        {'id': 2, 'title': '水质异常警报', 'content': '检测到水质参数异常...', 'type': 'alert', 'priority': 'high', 'sent_at': '2023-11-30 14:30:00', 'status': 'sent', 'recipient_count': 8},
        {'id': 3, 'title': '设备故障通知', 'content': '传感器设备出现故障...', 'type': 'alert', 'priority': 'urgent', 'sent_at': '2023-11-29 09:15:00', 'status': 'sending', 'recipient_count': 5},
    ]
    
    return render_template('notification_management.html', username=current_user.username, users=users, templates=templates, notifications=notifications)

@main_bp.route('/admin/notifications/send', methods=['POST'])
@login_required
def send_notification():
    if current_user.role != 'admin':
        flash('操作失败：权限不足。', 'danger')
        return redirect(url_for('main.notification_management_page'))
    
    # 这里应该实现通知发送逻辑
    flash('通知发送成功。', 'success')
    return redirect(url_for('main.notification_management_page'))

@main_bp.route('/admin/notifications/template', methods=['POST'])
@login_required
def save_notification_template():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 这里应该实现模板保存逻辑
    return jsonify({'success': True, 'message': '模板保存成功'})

@main_bp.route('/admin/notifications/template/<int:template_id>')
@login_required
def get_notification_template(template_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 这里应该实现模板获取逻辑
    template = {
        'type': 'maintenance',
        'priority': 'normal',
        'title': '系统维护通知',
        'content': '系统将于今晚进行维护，请提前做好准备。'
    }
    return jsonify(template)

@main_bp.route('/admin/notifications/template/<int:template_id>', methods=['DELETE'])
@login_required
def delete_notification_template(template_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 这里应该实现模板删除逻辑
    return jsonify({'success': True, 'message': '模板删除成功'})

@main_bp.route('/admin/notifications/resend/<int:notification_id>', methods=['POST'])
@login_required
def resend_notification(notification_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 这里应该实现通知重新发送逻辑
    return jsonify({'success': True, 'message': '通知重新发送成功'})

@main_bp.route('/admin/notifications/delete/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 这里应该实现通知删除逻辑
    return jsonify({'success': True, 'message': '通知删除成功'})

# 接口管理
@main_bp.route('/admin/api')
@login_required
def api_management_page():
    if current_user.role != 'admin':
        flash('您没有权限访问此页面。', 'warning')
        return redirect(url_for('main.user_dashboard'))
    
    # 模拟API密钥
    api_keys = [
        {'id': 1, 'name': 'Web应用密钥', 'key': 'sk_test_1234567890abcdef', 'created_at': '2023-11-01 10:00:00', 'last_used': '2023-12-01 15:30:00', 'status': 'active', 'usage_count': 1250},
        {'id': 2, 'name': '移动端密钥', 'key': 'sk_test_abcdef1234567890', 'created_at': '2023-11-15 14:20:00', 'last_used': '2023-11-30 09:45:00', 'status': 'active', 'usage_count': 890},
        {'id': 3, 'name': '测试密钥', 'key': 'sk_test_9876543210fedcba', 'created_at': '2023-11-20 16:10:00', 'last_used': None, 'status': 'inactive', 'usage_count': 0},
    ]
    
    # 模拟API配置
    config = {
        'rate_limit': 100,
        'max_requests': 10,
        'timeout': 30,
        'enable_cors': True,
        'enable_logging': True
    }
    
    # 模拟API端点
    endpoints = [
        {'path': '/api/water_quality_history', 'method': 'GET', 'description': '获取水质历史数据', 'call_count': 1250, 'avg_response_time': 150},
        {'path': '/api/doubao-chat', 'method': 'POST', 'description': '智能问答接口', 'call_count': 890, 'avg_response_time': 2000},
        {'path': '/api/fish-recognition', 'method': 'POST', 'description': '鱼类识别接口', 'call_count': 456, 'avg_response_time': 3500},
        {'path': '/api/weather_data', 'method': 'GET', 'description': '获取天气数据', 'call_count': 234, 'avg_response_time': 120},
    ]
    
    # 模拟访问日志
    access_logs = [
        {'timestamp': '2023-12-01 15:30:00', 'ip_address': '192.168.1.100', 'api_key': 'sk_test_1234567890abcdef', 'method': 'GET', 'path': '/api/water_quality_history', 'status_code': 200, 'response_time': 150, 'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
        {'timestamp': '2023-12-01 15:29:30', 'ip_address': '192.168.1.101', 'api_key': 'sk_test_abcdef1234567890', 'method': 'POST', 'path': '/api/doubao-chat', 'status_code': 200, 'response_time': 2100, 'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'},
        {'timestamp': '2023-12-01 15:28:45', 'ip_address': '192.168.1.102', 'api_key': 'sk_test_1234567890abcdef', 'method': 'POST', 'path': '/api/fish-recognition', 'status_code': 400, 'response_time': 500, 'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
    ]
    
    return render_template('api_management.html', username=current_user.username, api_keys=api_keys, config=config, endpoints=endpoints, access_logs=access_logs)

@main_bp.route('/admin/api/generate-key', methods=['POST'])
@login_required
def generate_api_key():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 这里应该实现API密钥生成逻辑
    return jsonify({'success': True, 'message': 'API密钥生成成功'})

@main_bp.route('/admin/api/regenerate-key/<int:key_id>', methods=['POST'])
@login_required
def regenerate_api_key(key_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 这里应该实现API密钥重新生成逻辑
    return jsonify({'success': True, 'message': 'API密钥重新生成成功'})

@main_bp.route('/admin/api/delete-key/<int:key_id>', methods=['DELETE'])
@login_required
def delete_api_key(key_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 这里应该实现API密钥删除逻辑
    return jsonify({'success': True, 'message': 'API密钥删除成功'})

@main_bp.route('/admin/api/update-config', methods=['POST'])
@login_required
def update_api_config():
    if current_user.role != 'admin':
        flash('操作失败：权限不足。', 'danger')
        return redirect(url_for('main.api_management_page'))
    
    # 这里应该实现API配置更新逻辑
    flash('API配置已更新。', 'success')
    return redirect(url_for('main.api_management_page'))

@main_bp.route('/admin/api/export-logs')
@login_required
def export_api_logs():
    if current_user.role != 'admin':
        return "无权限", 403
    
    # 这里应该实现日志导出逻辑
    return "日志导出功能待实现", 200

## 修改B3