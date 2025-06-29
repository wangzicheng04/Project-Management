import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import json
from datetime import datetime, timedelta
from sqlalchemy import func
from ..models import WaterQuality, WeatherData, db
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import io
import base64

class DataAnalysisService:
    """数据分析服务类"""
    
    def __init__(self):
        self.scaler = StandardScaler()
    
    def get_water_quality_statistics(self, start_date=None, end_date=None, province=None):
        """获取水质数据统计信息"""
        query = WaterQuality.query
        
        if start_date:
            query = query.filter(WaterQuality.monitor_time >= start_date)
        if end_date:
            query = query.filter(WaterQuality.monitor_time <= end_date)
        if province:
            query = query.filter(WaterQuality.province == province)
        
        data = query.all()
        
        if not data:
            return None
        
        # 转换为DataFrame
        df = pd.DataFrame([{
            'temperature': d.temperature,
            'pH': d.pH,
            'dissolved_oxygen': d.dissolved_oxygen,
            'conductivity': d.conductivity,
            'turbidity': d.turbidity,
            'permanganate_index': d.permanganate_index,
            'ammonia_nitrogen': d.ammonia_nitrogen,
            'total_phosphorus': d.total_phosphorus,
            'total_nitrogen': d.total_nitrogen,
            'chlorophyll_a': d.chlorophyll_a,
            'algae_density': d.algae_density,
            'quality_level': d.quality_level,
            'monitor_time': d.monitor_time,
            'province': d.province
        } for d in data])
        
        # 基础统计
        numeric_columns = ['temperature', 'pH', 'dissolved_oxygen', 'conductivity', 
                          'turbidity', 'permanganate_index', 'ammonia_nitrogen', 
                          'total_phosphorus', 'total_nitrogen', 'chlorophyll_a', 'algae_density']
        
        statistics = {
            'total_records': len(df),
            'date_range': {
                'start': df['monitor_time'].min().isoformat() if not df.empty else None,
                'end': df['monitor_time'].max().isoformat() if not df.empty else None
            },
            'quality_distribution': df['quality_level'].value_counts().to_dict(),
            'province_distribution': df['province'].value_counts().to_dict(),
            'parameter_statistics': {}
        }
        
        # 各参数统计
        for col in numeric_columns:
            if col in df.columns and df[col].notna().any():
                statistics['parameter_statistics'][col] = {
                    'mean': float(df[col].mean()),
                    'median': float(df[col].median()),
                    'std': float(df[col].std()),
                    'min': float(df[col].min()),
                    'max': float(df[col].max()),
                    'count': int(df[col].count())
                }
        
        return statistics
    
    def generate_correlation_analysis(self, start_date=None, end_date=None):
        """生成相关性分析"""
        query = WaterQuality.query
        
        if start_date:
            query = query.filter(WaterQuality.monitor_time >= start_date)
        if end_date:
            query = query.filter(WaterQuality.monitor_time <= end_date)
        
        data = query.all()
        
        if len(data) < 10:  # 增加最小数据量要求
            return None
        
        # 转换为DataFrame
        df = pd.DataFrame([{
            'temperature': d.temperature,
            'pH': d.pH,
            'dissolved_oxygen': d.dissolved_oxygen,
            'conductivity': d.conductivity,
            'turbidity': d.turbidity,
            'permanganate_index': d.permanganate_index,
            'ammonia_nitrogen': d.ammonia_nitrogen,
            'total_phosphorus': d.total_phosphorus,
            'total_nitrogen': d.total_nitrogen,
            'chlorophyll_a': d.chlorophyll_a,
            'algae_density': d.algae_density
        } for d in data])
        
        # 删除空值过多的列和行
        df_clean = df.dropna(thresh=len(df.columns)*0.7, axis=0)  # 保留至少70%非空值的行
        df_clean = df_clean.dropna(thresh=len(df_clean)*0.5, axis=1)  # 保留至少50%非空值的列
        
        if df_clean.empty or len(df_clean.columns) < 3:
            return None
        
        # 参数中文标签映射
        label_mapping = {
            'temperature': '温度',
            'pH': 'pH值',
            'dissolved_oxygen': '溶解氧',
            'conductivity': '电导率',
            'turbidity': '浊度',
            'permanganate_index': '高锰酸盐指数',
            'ammonia_nitrogen': '氨氮',
            'total_phosphorus': '总磷',
            'total_nitrogen': '总氮',
            'chlorophyll_a': '叶绿素a',
            'algae_density': '藻密度'
        }
        
        # 重命名列为中文
        df_clean_renamed = df_clean.rename(columns=label_mapping)
        
        # 计算相关性矩阵
        correlation_matrix = df_clean_renamed.corr()
        
        # 生成美化的热力图
        fig = px.imshow(correlation_matrix, 
                       text_auto='.3f',  # 显示3位小数
                       aspect="auto",
                       title="水质参数相关性分析",
                       color_continuous_scale='RdYlBu_r',  # 更直观的配色
                       zmin=-1, zmax=1)
        
        # 美化布局
        fig.update_layout(
            title={
                'text': '水质参数相关性分析',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': '#2c3e50', 'family': 'Microsoft YaHei'}
            },
            font={'family': 'Microsoft YaHei, Arial, sans-serif', 'size': 12},
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=100, r=100, t=100, b=100),
            width=800,
            height=600
        )
        
        # 添加颜色条标题
        fig.update_coloraxes(colorbar_title="相关性系数")
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)

    def generate_trend_analysis(self, parameter, start_date=None, end_date=None, province=None):
        """生成趋势分析"""
        query = WaterQuality.query
        
        if start_date:
            query = query.filter(WaterQuality.monitor_time >= start_date)
        if end_date:
            query = query.filter(WaterQuality.monitor_time <= end_date)
        if province:
            query = query.filter(WaterQuality.province == province)
        
        data = query.order_by(WaterQuality.monitor_time).all()
        
        if not data:
            return None
        
        # 提取数据
        dates = [d.monitor_time for d in data]
        values = [getattr(d, parameter) for d in data if getattr(d, parameter) is not None]
        valid_dates = [dates[i] for i, d in enumerate(data) if getattr(d, parameter) is not None]
        
        if len(values) < 5:  # 增加最小数据点要求
            return None
        
        # 创建美化的趋势图
        fig = go.Figure()
        
        # 主数据线
        fig.add_trace(go.Scatter(
            x=valid_dates, 
            y=values, 
            mode='lines+markers',
            name=f'{parameter}实测值',
            line=dict(color='#3498db', width=2),
            marker=dict(size=6, color='#3498db')
        ))
        
        # 添加趋势线
        if len(values) > 1:
            z = np.polyfit(range(len(values)), values, 1)
            p = np.poly1d(z)
            trend_values = p(range(len(values)))
            
            fig.add_trace(go.Scatter(
                x=valid_dates, 
                y=trend_values, 
                mode='lines', 
                name='趋势线', 
                line=dict(dash='dash', color='#e74c3c', width=2)
            ))
            
            # 添加置信区间
            residuals = np.array(values) - trend_values
            std_residuals = np.std(residuals)
            upper_bound = trend_values + 1.96 * std_residuals
            lower_bound = trend_values - 1.96 * std_residuals
            
            fig.add_trace(go.Scatter(
                x=valid_dates + valid_dates[::-1],
                y=list(upper_bound) + list(lower_bound[::-1]),
                fill='toself',
                fillcolor='rgba(231, 76, 60, 0.1)',
                line=dict(color='rgba(255,255,255,0)'),
                name='95%置信区间',
                showlegend=True
            ))
        
        # 美化布局
        parameter_names = {
            'pH': 'pH值',
            'dissolved_oxygen': '溶解氧 (mg/L)',
            'temperature': '温度 (°C)',
            'turbidity': '浊度 (NTU)',
            'conductivity': '电导率 (μS/cm)'
        }
        
        fig.update_layout(
            title={
                'text': f'{parameter_names.get(parameter, parameter)}趋势分析',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#2c3e50'}
            },
            xaxis_title='监测时间',
            yaxis_title=parameter_names.get(parameter, parameter),
            font={'family': 'Arial, sans-serif'},
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=80, r=80, t=80, b=80),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode='x unified'
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)

    def perform_clustering_analysis(self, n_clusters=3):
        """执行聚类分析"""
        # 获取最近一个月的数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        data = WaterQuality.query.filter(
            WaterQuality.monitor_time >= start_date,
            WaterQuality.monitor_time <= end_date
        ).all()
        
        if len(data) < n_clusters * 3:  # 确保每个聚类至少有3个点
            return None
        
        # 准备数据
        features = ['temperature', 'pH', 'dissolved_oxygen', 'conductivity', 
                   'turbidity', 'permanganate_index', 'ammonia_nitrogen']
        
        df = pd.DataFrame([{
            feature: getattr(d, feature) for feature in features
        } for d in data])
        
        # 删除包含NaN的行
        df_clean = df.dropna()
        
        if len(df_clean) < n_clusters * 3:
            return None
        
        # 标准化数据
        X_scaled = self.scaler.fit_transform(df_clean)
        
        # K-means聚类
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)
        
        # PCA降维用于可视化
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)
        
        # 创建美化的散点图
        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
        
        fig = go.Figure()
        
        for i in range(n_clusters):
            cluster_mask = clusters == i
            fig.add_trace(go.Scatter(
                x=X_pca[cluster_mask, 0],
                y=X_pca[cluster_mask, 1],
                mode='markers',
                name=f'聚类 {i+1}',
                marker=dict(
                    size=8,
                    color=colors[i % len(colors)],
                    opacity=0.7,
                    line=dict(width=1, color='white')
                )
            ))
        
        # 添加聚类中心
        centers_pca = pca.transform(kmeans.cluster_centers_)
        fig.add_trace(go.Scatter(
            x=centers_pca[:, 0],
            y=centers_pca[:, 1],
            mode='markers',
            name='聚类中心',
            marker=dict(
                size=15,
                color='black',
                symbol='x',
                line=dict(width=2, color='white')
            )
        ))
        
        # 美化布局
        fig.update_layout(
            title={
                'text': '水质数据聚类分析（PCA降维可视化）',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#2c3e50'}
            },
            xaxis_title=f'第一主成分 (解释方差: {pca.explained_variance_ratio_[0]:.1%})',
            yaxis_title=f'第二主成分 (解释方差: {pca.explained_variance_ratio_[1]:.1%})',
            font={'family': 'Arial, sans-serif'},
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=80, r=80, t=80, b=80),
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            )
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)  # 直接返回plot JSON字符串
    
    def generate_quality_report(self, start_date=None, end_date=None):
        """生成水质报告"""
        stats = self.get_water_quality_statistics(start_date, end_date)
        
        if not stats:
            return None
        
        # 水质等级评估
        quality_levels = stats['quality_distribution']
        total_records = stats['total_records']
        
        # 计算优良率
        excellent_count = quality_levels.get('I', 0) + quality_levels.get('II', 0)
        excellent_rate = (excellent_count / total_records * 100) if total_records > 0 else 0
        
        # 参数异常检测
        param_stats = stats['parameter_statistics']
        anomalies = []
        
        # 定义正常范围（示例）
        normal_ranges = {
            'pH': (6.5, 8.5),
            'dissolved_oxygen': (5.0, 15.0),
            'temperature': (0, 35),
            'turbidity': (0, 50)
        }
        
        for param, range_val in normal_ranges.items():
            if param in param_stats:
                mean_val = param_stats[param]['mean']
                if mean_val < range_val[0] or mean_val > range_val[1]:
                    anomalies.append({
                        'parameter': param,
                        'value': mean_val,
                        'normal_range': range_val,
                        'status': 'abnormal'
                    })
        
        report = {
            'summary': {
                'total_records': total_records,
                'date_range': stats['date_range'],
                'excellent_rate': round(excellent_rate, 2),
                'quality_distribution': quality_levels
            },
            'parameter_analysis': param_stats,
            'anomalies': anomalies,
            'recommendations': self._generate_recommendations(anomalies, excellent_rate)
        }
        
        return report
    
    def _generate_recommendations(self, anomalies, excellent_rate):
        """生成建议"""
        recommendations = []
        
        if excellent_rate < 80:
            recommendations.append("水质优良率偏低，建议加强水质监测和治理措施")
        
        for anomaly in anomalies:
            param = anomaly['parameter']
            if param == 'pH':
                recommendations.append("pH值异常，建议检查酸碱平衡，必要时进行pH调节")
            elif param == 'dissolved_oxygen':
                recommendations.append("溶解氧异常，建议检查增氧设备运行状态")
            elif param == 'turbidity':
                recommendations.append("浊度异常，建议检查过滤系统和沉淀处理")
        
        if not recommendations:
            recommendations.append("水质状况良好，继续保持现有管理措施")
        
        return recommendations