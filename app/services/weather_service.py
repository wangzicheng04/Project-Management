import requests
import random
from datetime import datetime, timedelta
from ..models import db, WeatherData, RanchLocation

class WeatherService:
    """处理天气数据的服务类"""
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    @staticmethod
    def fetch_current_weather(location_id):
        """获取指定位置的当前天气数据"""
        location = RanchLocation.query.get(location_id)
        if not location:
            return None
            
        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "current": ["temperature_2m", "relative_humidity_2m", "precipitation", 
                        "wind_speed_10m", "wind_direction_10m", "pressure_msl", 
                        "cloud_cover", "visibility", "weather_code"],
            "timezone": "auto"
        }
        
        try:
            response = requests.get(WeatherService.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            # 提取当前天气数据
            current = data.get("current", {})
            
            # 创建新的天气数据记录
            weather_data = WeatherData(
                location_id=location_id,
                timestamp=datetime.utcnow(),
                temperature=current.get("temperature_2m"),
                humidity=current.get("relative_humidity_2m"),
                precipitation=current.get("precipitation"),
                wind_speed=current.get("wind_speed_10m"),
                wind_direction=current.get("wind_direction_10m"),
                pressure=current.get("pressure_msl"),
                cloud_cover=current.get("cloud_cover"),
                visibility=current.get("visibility"),
                weather_code=current.get("weather_code")
            )
            
            db.session.add(weather_data)
            db.session.commit()
            
            return weather_data
            
        except Exception as e:
            print(f"获取天气数据失败: {str(e)}")
            return None
    
    @staticmethod
    def fetch_forecast(location_id, days=7):
        """获取指定位置的天气预报"""
        location = RanchLocation.query.get(location_id)
        if not location:
            return None
            
        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", 
                     "wind_speed_10m_max", "wind_direction_10m_dominant", 
                     "pressure_msl_mean", "weather_code"],
            "timezone": "auto",
            "forecast_days": days
        }
        
        try:
            response = requests.get(WeatherService.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"获取天气预报失败: {str(e)}")
            return None
    
    @staticmethod
    def get_current_weather(location_id):
        """获取指定位置的当前天气数据（模拟数据）"""
        location = RanchLocation.query.get(location_id)
        if not location:
            return None
            
        # 检查是否已有最近的天气数据
        latest_data = WeatherData.query.filter_by(location_id=location_id).order_by(WeatherData.timestamp.desc()).first()
        
        # 如果没有数据或数据超过1小时，则生成新数据
        if not latest_data or (datetime.utcnow() - latest_data.timestamp).total_seconds() > 3600:
            # 生成模拟天气数据
            weather_data = WeatherData(
                location_id=location_id,
                timestamp=datetime.utcnow(),
                temperature=round(random.uniform(15, 30), 1),
                humidity=round(random.uniform(40, 95), 1),
                precipitation=round(random.uniform(0, 10), 1),
                wind_speed=round(random.uniform(0, 30), 1),
                wind_direction=round(random.uniform(0, 359), 1),
                pressure=round(random.uniform(995, 1015), 1),
                cloud_cover=round(random.uniform(0, 100), 1),
                visibility=round(random.uniform(5, 20), 1),
                weather_code=random.choice([0, 1, 2, 3, 45, 51, 61, 71, 80, 95])  # 随机天气代码
            )
            
            db.session.add(weather_data)
            db.session.commit()
            
            return weather_data
        
        return latest_data
    
    @staticmethod
    def get_weather_forecast(location_id, days=7):
        """获取指定位置的天气预报（模拟数据）"""
        location = RanchLocation.query.get(location_id)
        if not location:
            return None
            
        forecast = {
            "daily": {
                "time": [],
                "temperature_2m_max": [],
                "temperature_2m_min": [],
                "precipitation_sum": [],
                "wind_speed_10m_max": [],
                "wind_direction_10m_dominant": [],
                "weather_code": []
            }
        }
        
        # 生成未来几天的模拟数据
        for i in range(days):
            date = (datetime.utcnow() + timedelta(days=i)).strftime("%Y-%m-%d")
            forecast["daily"]["time"].append(date)
            forecast["daily"]["temperature_2m_max"].append(round(random.uniform(20, 35), 1))
            forecast["daily"]["temperature_2m_min"].append(round(random.uniform(10, 20), 1))
            forecast["daily"]["precipitation_sum"].append(round(random.uniform(0, 20), 1))
            forecast["daily"]["wind_speed_10m_max"].append(round(random.uniform(5, 40), 1))
            forecast["daily"]["wind_direction_10m_dominant"].append(round(random.uniform(0, 359), 1))
            forecast["daily"]["weather_code"].append(random.choice([0, 1, 2, 3, 45, 51, 61, 71, 80, 95]))
        
        return forecast
    
    @staticmethod
    def get_weather_history(location_id, days=7):
        """获取指定位置的历史天气数据"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        history_data = WeatherData.query.filter(
            WeatherData.location_id == location_id,
            WeatherData.timestamp >= start_date
        ).order_by(WeatherData.timestamp).all()
        
        # 如果没有足够的历史数据，生成模拟数据
        if len(history_data) < days:
            # 清除现有数据
            WeatherData.query.filter(
                WeatherData.location_id == location_id,
                WeatherData.timestamp >= start_date
            ).delete()
            
            # 生成历史数据
            for day in range(days):
                for hour in [6, 12, 18, 0]:
                    timestamp = datetime.utcnow() - timedelta(days=day, hours=datetime.utcnow().hour - hour)
                    
                    weather_data = WeatherData(
                        location_id=location_id,
                        timestamp=timestamp,
                        temperature=round(random.uniform(15, 30), 1),
                        humidity=round(random.uniform(40, 95), 1),
                        precipitation=round(random.uniform(0, 10), 1),
                        wind_speed=round(random.uniform(0, 30), 1),
                        wind_direction=round(random.uniform(0, 359), 1),
                        pressure=round(random.uniform(995, 1015), 1),
                        cloud_cover=round(random.uniform(0, 100), 1),
                        visibility=round(random.uniform(5, 20), 1),
                        weather_code=random.choice([0, 1, 2, 3, 45, 51, 61, 71, 80, 95])
                    )
                    db.session.add(weather_data)
            
            db.session.commit()
            
            # 重新获取数据
            history_data = WeatherData.query.filter(
                WeatherData.location_id == location_id,
                WeatherData.timestamp >= start_date
            ).order_by(WeatherData.timestamp).all()
        
        return history_data
    
    @staticmethod
    def get_weather_code_description(code):
        """获取WMO天气代码对应的描述"""
        weather_codes = {
            0: "晴朗",
            1: "大部晴朗",
            2: "部分多云",
            3: "阴天",
            45: "雾",
            48: "沉积雾",
            51: "小毛毛雨",
            53: "中毛毛雨",
            55: "大毛毛雨",
            56: "小冻雨",
            57: "大冻雨",
            61: "小雨",
            63: "中雨",
            65: "大雨",
            66: "小冻雨",
            67: "大冻雨",
            71: "小雪",
            73: "中雪",
            75: "大雪",
            77: "雪粒",
            80: "小阵雨",
            81: "中阵雨",
            82: "大阵雨",
            85: "小阵雪",
            86: "大阵雪",
            95: "雷暴",
            96: "雷暴伴有小冰雹",
            99: "雷暴伴有大冰雹"
        }
        return weather_codes.get(code, "未知")