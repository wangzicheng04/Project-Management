# 智慧海洋牧场可视化系统

## 项目简介
基于Flask的智慧海洋牧场管理系统，实现海洋环境监测、设备管理、数据可视化等功能。

## 安装指南
1. 克隆项目仓库
```bash
git clone https://github.com/your-repo/Smart-marine-ranch-visualization-system.git
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 初始化数据库
4. 
- 将导入数据放入项目目录下，运行
```bash
python init_db.py # 初始化水质历史数据和用户信息
python import_waterdata.py # 初始化全国省份流域数据
```

1. 运行开发服务器
```bash
python run.py
```

## 项目结构
```
Smart-marine-ranch-visualization-system/
├── app/
│   ├── routes/            # 路由模块
│   ├── services/          # 业务逻辑服务
│   ├── static/            # 静态资源
│   └── templates/         # 前端网页
├── instance/              # 数据库文件
├── requirements.txt       # 依赖库
└── run.py                 # 启动
```

## 鱼类识别

可在**picture_to_identify**文件夹中选取图片进行识别

## 智能问答

需要配置的API_key在对应的txt中