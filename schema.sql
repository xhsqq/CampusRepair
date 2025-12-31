-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL, -- 'student' 或 'worker'
    name TEXT NOT NULL,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 报修工单表
CREATE TABLE IF NOT EXISTS repairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id INTEGER NOT NULL,
    contact_name TEXT NOT NULL,
    contact_phone TEXT NOT NULL,
    location TEXT NOT NULL,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    image_path TEXT,
    status TEXT DEFAULT 'NEW', -- 'NEW', 'ASSIGNED', 'IN_PROGRESS', 'DONE', 'CANCELED'
    urgency_level INTEGER DEFAULT 1, -- 1: 低, 2: 中, 3: 高
    assignee_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES users (id),
    FOREIGN KEY (assignee_id) REFERENCES users (id)
);

-- 工单处理记录表
CREATE TABLE IF NOT EXISTS repair_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_id INTEGER NOT NULL,
    actor_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    note TEXT,
    from_status TEXT,
    to_status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repair_id) REFERENCES repairs (id),
    FOREIGN KEY (actor_id) REFERENCES users (id)
);
