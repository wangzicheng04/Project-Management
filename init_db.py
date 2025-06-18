from app import create_app, db
from app.models import User, RanchLocation, WeatherData  # 确保所有模型都被导入

app = create_app()

with app.app_context():
    # print("删除旧数据库表...")
    # db.drop_all()
    
    if User.query.filter_by(username='admin').first():
        print('数据库已初始化，无需重复操作。')
    else: 
        db.create_all()
        print("用户数据初始化")
        
        # 检查并创建管理员账户
        if not User.query.filter_by(username='admin').first():
            print("正在创建管理员账户 'admin'...")
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            print("管理员账户创建成功。")

        # 检查并创建普通用户账户
        if not User.query.filter_by(username='user').first():
            print("正在创建普通用户账户 'user'...")
            user = User(username='user', role='user')
            user.set_password('user123')
            db.session.add(user)
            print("普通用户账户创建成功。")

        # 检查并添加示例牧场位置
        if RanchLocation.query.count() == 0:
            print("正在添加示例牧场位置...")
            locations = [
                RanchLocation(name='青岛海洋牧场', latitude=36.0671, longitude=120.3826, description='山东青岛近海海洋牧场'),
                RanchLocation(name='舟山海洋牧场', latitude=30.0444, longitude=122.1997, description='浙江舟山群岛海洋牧场'),
                RanchLocation(name='北部湾海洋牧场', latitude=21.4735, longitude=109.1192, description='广西北部湾海洋牧场')
            ]
            db.session.add_all(locations)
            print("示例牧场位置添加成功。")

        db.session.commit()
        print('数据库初始化完成！')