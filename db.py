import pymysql
import os
from dotenv import load_dotenv
from pymysql.cursors import DictCursor
import logging

# 加载环境变量
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)

def get_mysql_config():
    """从 .env 环境变量读取数据库连接配置，配置里写什么就用什么数据库"""
    config = {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME'),
        'charset': 'utf8mb4',
        'cursorclass': DictCursor,  # 使用字典游标，返回字典格式的结果
        'init_command': "SET time_zone='+08:00'"  # 设置时区为东八区
    }

    # 校验必填项，避免缺少配置时静默连到错误的数据库
    required = ['host', 'user', 'password', 'database']
    missing = [key.upper() for key in required if not config.get(key)]
    if missing:
        raise ValueError(
            f"数据库配置不完整，请在 .env 文件中设置: {', '.join('DB_' + key for key in missing)}"
        )

    return config

def log_environment_info():
    """记录环境配置信息到日志"""
    logger.info("=" * 50)
    logger.info("应用启动环境信息")
    logger.info("=" * 50)
    logger.info("数据库配置 (实际生效值):")
    logger.info(f"  HOST: {MYSQL_CONFIG.get('host')}")
    logger.info(f"  PORT: {MYSQL_CONFIG.get('port')}")
    logger.info(f"  USER: {MYSQL_CONFIG.get('user')}")
    logger.info(f"  DB_NAME: {MYSQL_CONFIG.get('database')}")
    logger.info("=" * 50)

MYSQL_CONFIG = get_mysql_config()

def get_db_connection():
    """获取数据库连接"""
    connection = pymysql.connect(**MYSQL_CONFIG)
    # 确保时区设置正确
    with connection.cursor() as cursor:
        cursor.execute("SET time_zone='+08:00'")
    return connection