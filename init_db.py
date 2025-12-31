import sqlite3
import os

def init_db():
    db_path = 'campus_repair.sqlite3'
    schema_path = 'schema.sql'
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    with open(schema_path, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    
    # 插入演示数据（可选）
    cursor = conn.cursor()
    
    # 检查是否已有用户，避免重复插入
    cursor.execute("SELECT count(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # 插入一个学生账号和维修人员账号
        # 密码简单演示用明文（实际项目建议哈希）
        users = [
            ('student01', '123456', 'student', '张同学', '13800138001'),
            ('worker01', '123456', 'worker', '王师傅', '13900139002')
        ]
        cursor.executemany(
            "INSERT INTO users (username, password, role, name, phone) VALUES (?, ?, ?, ?, ?)",
            users
        )
        print("已创建演示账号: student01/123456 (学生), worker01/123456 (维修人员)")

    conn.commit()
    conn.close()
    print(f"数据库 {db_path} 初始化完成！")

if __name__ == '__main__':
    init_db()
