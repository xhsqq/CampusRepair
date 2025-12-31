from flask import Flask, render_template, request, redirect, url_for, session, flash, g
import sqlite3
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'campus_repair_secret_key'
DATABASE = 'campus_repair.sqlite3'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- 数据库工具函数 ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

# --- 登录保护装饰器 ---
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- 路由实现 ---

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = query_db("SELECT * FROM users WHERE username = ?", [username], one=True)
        if user and user['password'] == password: # 教学项目简单校验
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['name'] = user['name']
            return redirect(url_for('dashboard'))
        flash('用户名或密码错误', 'danger')
    return render_template('auth_login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        name = request.form['name']
        phone = request.form['phone']
        
        db = get_db()
        try:
            db.execute("INSERT INTO users (username, password, role, name, phone) VALUES (?, ?, ?, ?, ?)",
                       [username, password, role, name, phone])
            db.commit()
            flash('注册成功，请登录', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('用户名已存在', 'danger')
    return render_template('auth_register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    role = session['role']
    
    if role == 'student':
        stats = query_db("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status='NEW' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status='DONE' THEN 1 ELSE 0 END) as completed
            FROM repairs WHERE creator_id = ?
        """, [user_id], one=True)
    else:
        stats = query_db("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status='NEW' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status='IN_PROGRESS' THEN 1 ELSE 0 END) as processing
            FROM repairs
        """, one=True)
        
    return render_template('dashboard.html', stats=stats)

@app.route('/repairs')
@login_required
def repairs_list():
    role = session['role']
    user_id = session['user_id']
    status_filter = request.args.get('status')
    
    query = "SELECT * FROM repairs"
    params = []
    
    if role == 'student':
        query += " WHERE creator_id = ?"
        params.append(user_id)
        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)
    else:
        if status_filter:
            query += " WHERE status = ?"
            params.append(status_filter)
            
    query += " ORDER BY urgency_level DESC, created_at DESC"
    repairs = query_db(query, params)
    return render_template('repairs_list.html', repairs=repairs)

@app.route('/repairs/new', methods=['GET', 'POST'])
@login_required
def repairs_new():
    if session['role'] != 'student':
        flash('仅学生可提交报修', 'danger')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        location = request.form['location']
        category = request.form['category']
        content = request.form['content']
        urgency = request.form['urgency_level']
        contact_name = request.form.get('contact_name', session['name'])
        contact_phone = request.form.get('contact_phone', '')
        
        file = request.files.get('image')
        filename = None
        if file and file.filename:
            filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
        db = get_db()
        cursor = db.execute("""
            INSERT INTO repairs (creator_id, contact_name, contact_phone, location, category, content, urgency_level, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [session['user_id'], contact_name, contact_phone, location, category, content, urgency, filename])
        repair_id = cursor.lastrowid
        
        # 记录日志
        db.execute("INSERT INTO repair_logs (repair_id, actor_id, action, note, to_status) VALUES (?, ?, ?, ?, ?)",
                   [repair_id, session['user_id'], 'CREATE', '提交报修申请', 'NEW'])
        db.commit()
        flash('报修申请已提交', 'success')
        return redirect(url_for('repairs_list'))
        
    return render_template('repairs_new.html')

@app.route('/repairs/<int:id>')
@login_required
def repairs_detail(id):
    repair = query_db("SELECT * FROM repairs WHERE id = ?", [id], one=True)
    if not repair:
        flash('工单不存在', 'danger')
        return redirect(url_for('repairs_list'))
    
    logs = query_db("SELECT l.*, u.name as actor_name FROM repair_logs l JOIN users u ON l.actor_id = u.id WHERE l.repair_id = ? ORDER BY l.created_at DESC", [id])
    return render_template('repairs_detail.html', repair=repair, logs=logs)

@app.route('/repairs/<int:id>/action', methods=['POST'])
@login_required
def repairs_action(id):
    action = request.form.get('action')
    user_id = session['user_id']
    role = session['role']
    db = get_db()
    
    repair = query_db("SELECT * FROM repairs WHERE id = ?", [id], one=True)
    if not repair: return "Error", 404

    old_status = repair['status']
    new_status = old_status
    note = request.form.get('note', '')

    if action == 'assign' and role == 'worker':
        new_status = 'ASSIGNED'
        db.execute("UPDATE repairs SET status=?, assignee_id=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", [new_status, user_id, id])
    elif action == 'start' and role == 'worker' and repair['assignee_id'] == user_id:
        new_status = 'IN_PROGRESS'
        db.execute("UPDATE repairs SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", [new_status, id])
    elif action == 'complete' and role == 'worker' and repair['assignee_id'] == user_id:
        new_status = 'DONE'
        db.execute("UPDATE repairs SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", [new_status, id])
    elif action == 'cancel' and role == 'student' and old_status == 'NEW' and repair['creator_id'] == user_id:
        new_status = 'CANCELED'
        db.execute("UPDATE repairs SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", [new_status, id])
    else:
        # 如果角色不匹配或条件不满足，直接返回不执行任何更新
        flash('操作失败：权限不足或状态不符', 'danger')
        return redirect(url_for('repairs_detail', id=id))
    
    if new_status != old_status:
        db.execute("INSERT INTO repair_logs (repair_id, actor_id, action, note, from_status, to_status) VALUES (?, ?, ?, ?, ?, ?)",
                   [id, user_id, action.upper(), note, old_status, new_status])
        db.commit()
        flash('状态已更新', 'success')
    
    return redirect(url_for('repairs_detail', id=id))

@app.route('/me')
@login_required
def me():
    user = query_db("SELECT * FROM users WHERE id = ?", [session['user_id']], one=True)
    return render_template('me.html', user=user)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
