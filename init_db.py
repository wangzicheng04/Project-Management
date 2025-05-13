from app import create_app, db
from app.models import User, RanchLocation
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # 创建所有数据库表
    db.create_all()
    
    # 检查是否已存在管理员账户
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        # 创建管理员账户
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        
        # 创建普通用户账户
        user = User(
            username='user',
            password=generate_password_hash('user123'),
            role='user'
        )
        db.session.add(user)
        
        # 添加一些示例牧场位置
        locations = [
            RanchLocation(
                name='青岛海洋牧场',
                latitude=36.0671,
                longitude=120.3826,
                description='山东青岛近海海洋牧场'
            ),
            RanchLocation(
                name='舟山海洋牧场',
                latitude=30.0444,
                longitude=122.1997,
                description='浙江舟山群岛海洋牧场'
            ),
            RanchLocation(
                name='北部湾海洋牧场',
                latitude=21.4735,
                longitude=109.1192,
                description='广西北部湾海洋牧场'
            )
        ]
        
        for location in locations:
            db.session.add(location)
        
        db.session.commit()
        print('数据库初始化完成！')
    else:
        print('数据库已初始化，无需重复操作。')