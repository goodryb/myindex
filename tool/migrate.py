import sys
import os
import time

# 将项目根目录添加到系统路径，以便导入 db 模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

import db

# 迁移脚本目录与版本记录表
MIGRATIONS_DIR = os.path.join(project_root, 'migrations')
VERSION_TABLE = 'schema_migrations'
DB_RETRIES = 10
DB_RETRY_DELAY = 3


def wait_for_db():
    """等待数据库就绪，避免容器先于 MySQL 启动时连接失败"""
    for attempt in range(1, DB_RETRIES + 1):
        try:
            connection = db.get_db_connection()
            connection.close()
            print("数据库连接成功。")
            return True
        except Exception as e:
            print(f"数据库未就绪 ({attempt}/{DB_RETRIES}): {e}")
            time.sleep(DB_RETRY_DELAY)
    print("错误: 数据库连接超时，请检查数据库配置。")
    return False


def ensure_version_table(connection):
    """创建迁移版本记录表（幂等）"""
    with connection.cursor() as cursor:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {VERSION_TABLE} (
                version    VARCHAR(255) NOT NULL COMMENT '迁移版本号（文件名）',
                remark     VARCHAR(255) NULL COMMENT '迁移备注',
                applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '应用时间',
                PRIMARY KEY (version)
            ) COMMENT='数据库迁移版本记录'
        """)
    connection.commit()


def get_applied_versions(connection):
    """获取已应用的迁移版本集合"""
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT version FROM {VERSION_TABLE}")
        return {row['version'] for row in cursor.fetchall()}


def split_sql_statements(content):
    """按分号拆分 SQL，过滤注释行与空语句"""
    statements = []
    for raw in content.split(';'):
        lines = [line for line in raw.splitlines() if line.strip() and not line.strip().startswith('--')]
        stmt = '\n'.join(lines).strip()
        if stmt:
            statements.append(stmt)
    return statements


def apply_migration(connection, version, file_path):
    """执行单个迁移文件，成功后记录版本"""
    with open(file_path, 'r', encoding='utf-8') as f:
        statements = split_sql_statements(f.read())

    with connection.cursor() as cursor:
        for stmt in statements:
            try:
                cursor.execute(stmt)
            except Exception as e:
                # 对象已存在则跳过（幂等），其他错误终止当前版本
                if 'already exists' in str(e).lower():
                    print(f"  跳过已存在对象: {e}")
                else:
                    raise
        try:
            cursor.execute(f"INSERT INTO {VERSION_TABLE} (version) VALUES (%s)", (version,))
        except Exception as e:
            # 并发场景下版本号已被其他实例插入，视为已应用
            if '1062' in str(e) or 'duplicate' in str(e).lower():
                print(f"  版本 {version} 已被其他实例应用，跳过记录。")
            else:
                raise
    connection.commit()
    print(f"  ✔ 已应用迁移: {version}")


def main():
    if not os.path.isdir(MIGRATIONS_DIR):
        print(f"错误: 迁移目录不存在: {MIGRATIONS_DIR}")
        return 1

    if not wait_for_db():
        return 1

    connection = None
    try:
        connection = db.get_db_connection()
        ensure_version_table(connection)
        applied = get_applied_versions(connection)

        # 按文件名升序收集待应用迁移
        pending = []
        for name in sorted(os.listdir(MIGRATIONS_DIR)):
            if name.endswith('.sql') and name not in applied:
                pending.append(name)

        if not pending:
            print("所有迁移已应用，无需执行。")
            return 0

        print(f"发现 {len(pending)} 个待应用迁移:")
        for name in pending:
            print(f"  应用 {name} ...")
            apply_migration(connection, name, os.path.join(MIGRATIONS_DIR, name))

        print("数据库迁移全部完成。")
        return 0
    except Exception as e:
        print(f"错误: 数据库迁移失败: {e}")
        return 1
    finally:
        if connection:
            connection.close()


if __name__ == '__main__':
    sys.exit(main())