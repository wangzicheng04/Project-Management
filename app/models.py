from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'user' 或 'admin'

# 添加海洋牧场位置模型
class RanchLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)  # 纬度
    longitude = db.Column(db.Float, nullable=False)  # 经度
    description = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<RanchLocation {self.name}>'

# 添加天气数据模型
class WeatherData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('ranch_location.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    temperature = db.Column(db.Float, nullable=True)  # 温度，单位：摄氏度
    humidity = db.Column(db.Float, nullable=True)  # 湿度，百分比
    precipitation = db.Column(db.Float, nullable=True)  # 降水量，单位：mm
    wind_speed = db.Column(db.Float, nullable=True)  # 风速，单位：km/h
    wind_direction = db.Column(db.Float, nullable=True)  # 风向，单位：度
    pressure = db.Column(db.Float, nullable=True)  # 气压，单位：hPa
    cloud_cover = db.Column(db.Float, nullable=True)  # 云量，百分比
    visibility = db.Column(db.Float, nullable=True)  # 能见度，单位：km
    weather_code = db.Column(db.Integer, nullable=True)  # WMO天气代码
    
    def __repr__(self):
        return f'<WeatherData {self.timestamp}>'
