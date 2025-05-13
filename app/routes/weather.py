from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from ..models import db, RanchLocation, WeatherData
from ..services.weather_service import WeatherService

weather_bp = Blueprint('weather', __name__)

@weather_bp.route('/weather')
@login_required
def weather_dashboard():
    """天气数据展示页面"""
    locations = RanchLocation.query.all()
    return render_template('weather.html', locations=locations)

@weather_bp.route('/api/weather/current/<int:location_id>')
@login_required
def get_current_weather(location_id):
    """获取最新天气数据"""
    weather_data = WeatherService.get_current_weather(location_id)
    
    if weather_data:
        location = RanchLocation.query.get(location_id)
        return jsonify({
            'id': weather_data.id,
            'location_name': location.name,
            'timestamp': weather_data.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'temperature': weather_data.temperature,
            'humidity': weather_data.humidity,
            'precipitation': weather_data.precipitation,
            'wind_speed': weather_data.wind_speed,
            'wind_direction': weather_data.wind_direction,
            'pressure': weather_data.pressure,
            'cloud_cover': weather_data.cloud_cover,
            'visibility': weather_data.visibility,
            'weather_code': weather_data.weather_code,
            'weather_description': WeatherService.get_weather_code_description(weather_data.weather_code)
        })
    else:
        return jsonify({'error': '无法获取天气数据'}), 404

@weather_bp.route('/api/weather/forecast/<int:location_id>')
@login_required
def get_weather_forecast(location_id):
    """获取天气预报"""
    days = request.args.get('days', 7, type=int)
    forecast_data = WeatherService.get_weather_forecast(location_id, days)
    
    if forecast_data:
        # 添加天气描述
        weather_descriptions = []
        for code in forecast_data['daily']['weather_code']:
            weather_descriptions.append(WeatherService.get_weather_code_description(code))
        
        forecast_data['daily']['weather_description'] = weather_descriptions
        
        return jsonify(forecast_data)
    else:
        return jsonify({'error': '无法获取天气预报'}), 404

@weather_bp.route('/api/weather/history/<int:location_id>')
@login_required
def get_weather_history(location_id):
    """获取历史天气数据"""
    days = request.args.get('days', 7, type=int)
    history_data = WeatherService.get_weather_history(location_id, days)
    
    result = []
    for data in history_data:
        result.append({
            'timestamp': data.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'temperature': data.temperature,
            'humidity': data.humidity,
            'precipitation': data.precipitation,
            'wind_speed': data.wind_speed,
            'pressure': data.pressure,
            'weather_code': data.weather_code,
            'weather_description': WeatherService.get_weather_code_description(data.weather_code)
        })
    
    return jsonify(result)

@weather_bp.route('/locations')
@login_required
def list_locations():
    """列出所有牧场位置"""
    locations = RanchLocation.query.all()
    return render_template('locations.html', locations=locations)

@weather_bp.route('/locations/add', methods=['GET', 'POST'])
@login_required
def add_location():
    """添加新的牧场位置"""
    if current_user.role != 'admin':
        flash('只有管理员可以添加位置')
        return redirect(url_for('weather.list_locations'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        description = request.form.get('description')
        
        if not name or not latitude or not longitude:
            flash('请填写所有必填字段')
        else:
            try:
                latitude = float(latitude)
                longitude = float(longitude)
                
                new_location = RanchLocation(
                    name=name,
                    latitude=latitude,
                    longitude=longitude,
                    description=description
                )
                
                db.session.add(new_location)
                db.session.commit()
                flash('位置添加成功')
                return redirect(url_for('weather.list_locations'))
            except ValueError:
                flash('经纬度必须是有效的数字')
    
    return render_template('add_location.html')