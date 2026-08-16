from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import re
import logging
from api import api_bp  # 从api模块导入蓝图
import db  # 导入数据库模块

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 配置 MySQL 连接
def get_mysql_config():
    return db.get_mysql_config()

def log_environment_info():
    """记录环境配置信息到日志"""
    db.log_environment_info()

MYSQL_CONFIG = db.get_mysql_config()


def get_db_connection():
    """获取数据库连接"""
    return db.get_db_connection()


def extract_price_from_title(title):
    """从标题中提取价格"""
    # 使用正则表达式匹配价格，例如：10699元、5345元、9697元等
    price_match = re.search(r'(\d+(?:\.\d+)?)元', title)
    if price_match:
        return price_match.group(1)
    return "价格未知"


def extract_mall_from_description(description):
    """从描述中提取商城名称"""
    # 使用正则表达式匹配商城名称，例如：天猫精选、天猫国际、京东等
    mall_match = re.search(r'>([^<]+)<', description)
    if mall_match:
        return mall_match.group(1)
    return "商城未知"


def extract_image_url_from_description(description):
    """从描述中提取图片URL"""
    # 使用正则表达式匹配图片URL
    img_match = re.search(r'src="([^"]+)"', description)
    if img_match:
        return img_match.group(1)
    return None


def get_home_data():
    """查询首页展示数据（单次连接，消除 N+1），返回 (up_videos, changyong_sites, products)"""
    up_videos = {}
    changyong_sites = []
    products = []

    # 单次连接完成所有查询，避免多次建立/关闭连接
    connection = None
    try:
        connection = get_db_connection()
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return up_videos, changyong_sites, products

    try:
        # UP主及其当日视频（LEFT JOIN 一次查出，消除 N+1 查询）
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT u.upid, u.cn_name, v.cn_name AS videoname, v.url AS videourl
                FROM upuser u
                LEFT JOIN upvideo v ON v.upid = u.upid AND DATE(v.videodate) = DATE(CURDATE())
                ORDER BY u.upid, v.videodate DESC
            """)
            for row in cursor.fetchall():
                key = f"up_{row['upid']}"
                if key not in up_videos:
                    up_videos[key] = {
                        "name": row['cn_name'] if row['cn_name'] else row['upid'],
                        "videolist": []
                    }
                # LEFT JOIN 下无视频时 videoname 为 NULL
                if row['videoname']:
                    up_videos[key]["videolist"].append({
                        "videoname": row['videoname'],
                        "videourl": row['videourl']
                    })
    except Exception as db_error:
        logger.error(f"数据库错误: {db_error}")
        up_videos = {}

    try:
        # 从daohang表获取常用网站信息，包括图标URL
        with connection.cursor() as cursor:
            cursor.execute("SELECT cn_name, url, icon_url FROM daohang ORDER BY id")
            for site in cursor.fetchall():
                changyong_sites.append({
                    "name": site['cn_name'],
                    "url": site['url'],
                    "icon_url": site['icon_url'] if site['icon_url'] else None
                })
    except Exception as db_error:
        logger.error(f"数据库错误: {db_error}")
        changyong_sites = []

    try:
        # 从smzdm_products表获取最近24小时内的商品信息，按时间倒序排列，限制20条
        with connection.cursor() as cursor:
            cursor.execute("SELECT title, description, link, pub_date FROM smzdm_products WHERE pub_date >= DATE_SUB(NOW(), INTERVAL 24 HOUR) ORDER BY pub_date DESC LIMIT 20")
            for product in cursor.fetchall():
                products.append({
                    "title": product['title'],
                    "price": extract_price_from_title(product['title']),
                    "mall": extract_mall_from_description(product['description']),
                    "image_url": extract_image_url_from_description(product['description']),
                    "link": product['link'],
                    "pub_date": product['pub_date']
                })
    except Exception as db_error:
        logger.error(f"数据库错误: {db_error}")
        products = []
    finally:
        if connection:
            connection.close()

    return up_videos, changyong_sites, products


@app.route('/')
def home():
    """
    主页，显示优惠商品信息、UP主当日视频和常用网站链接
    """
    up_videos, changyong_sites, products = get_home_data()
    return render_template('index.html', up_videos=up_videos, changyong_sites=changyong_sites, products=products)


@app.route('/api/home')
def home_data():
    """
    返回首页展示数据（JSON），供前端定时局部刷新使用
    """
    up_videos, changyong_sites, products = get_home_data()
    # datetime 转字符串，保证可 JSON 序列化
    for product in products:
        if product.get('pub_date'):
            product['pub_date'] = str(product['pub_date'])
    return jsonify({
        'up_videos': up_videos,
        'changyong_sites': changyong_sites,
        'products': products
    })


@app.route('/up/<up_id>')
def get_up_details(up_id):
    """
    根据UP主ID获取其详细信息和当日视频列表
    """
    try:
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 获取UP主信息
                cursor.execute("SELECT upid, cn_name FROM upuser WHERE upid = %s", (up_id,))
                up_info = cursor.fetchone()
                
                if not up_info:
                    return jsonify({'error': 'UP user not found', 'up_id': up_id}), 404

                # 获取视频列表（只获取当天发布的视频）
                cursor.execute("SELECT cn_name as videoname, url as videourl FROM upvideo WHERE upid = %s AND DATE(videodate) = DATE(CURDATE()) ORDER BY videodate DESC", (up_id,))
                videos = cursor.fetchall()
                
                result = {
                    "name": up_info['cn_name'] if up_info['cn_name'] else up_id,
                    "videolist": videos
                }
                return jsonify(result)
        finally:
            connection.close()

    except Exception as db_error:
        # 数据库查询失败
        logger.error(f"数据库错误: {db_error}")
        return jsonify({
            'error': f'An error occurred: {str(db_error)}'
        }), 500


@app.route('/admin')
def admin():
    """
    后台管理页面
    """
    try:
        # 获取所有数据用于管理界面展示
        # 获取常用网站数据
        daohang_data = []
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, cn_name, url, icon_url FROM daohang ORDER BY id")
                daohang_data = cursor.fetchall()
        finally:
            connection.close()
        
        # 获取UP主数据
        upuser_data = []
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT upid, platform, cn_name, accountid FROM upuser")
                upuser_data = cursor.fetchall()
        finally:
            connection.close()
            
        # 获取商品关键字数据
        keywords_data = []
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, keyword, site_type, enabled FROM smzdm_keywords ORDER BY id")
                keywords_data = cursor.fetchall()
        finally:
            connection.close()
        
        return render_template('admin.html', 
                              daohang_data=daohang_data,
                              upuser_data=upuser_data,
                              keywords_data=keywords_data)
    except Exception as e:
        return f'<h1>Admin Error: {str(e)}</h1>', 500


@app.route('/admin/daohang/add', methods=['POST'])
def add_daohang():
    """添加常用网站记录"""
    try:
        cn_name = request.form.get('cn_name')
        url = request.form.get('url')
        icon_url = request.form.get('icon_url', '')
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO daohang (cn_name, url, icon_url) VALUES (%s, %s, %s)",
                    (cn_name, url, icon_url)
                )
                connection.commit()
        finally:
            connection.close()
            
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/admin/daohang/update', methods=['POST'])
def update_daohang():
    """更新常用网站记录"""
    try:
        id = request.form.get('id')
        cn_name = request.form.get('cn_name')
        url = request.form.get('url')
        icon_url = request.form.get('icon_url', '')
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE daohang SET cn_name=%s, url=%s, icon_url=%s WHERE id=%s",
                    (cn_name, url, icon_url, id)
                )
                connection.commit()
        finally:
            connection.close()
            
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/admin/daohang/delete', methods=['POST'])
def delete_daohang():
    """删除常用网站记录"""
    try:
        id = request.form.get('id')
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM daohang WHERE id=%s", (id,))
                connection.commit()
        finally:
            connection.close()
            
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/admin/upuser/add', methods=['POST'])
def add_upuser():
    """添加UP主记录"""
    try:
        upid = request.form.get('upid')
        platform = request.form.get('platform')
        cn_name = request.form.get('cn_name')
        accountid = request.form.get('accountid')
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO upuser (upid, platform, cn_name, accountid) VALUES (%s, %s, %s, %s)",
                    (upid, platform, cn_name, accountid)
                )
                connection.commit()
        finally:
            connection.close()
            
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/admin/upuser/update', methods=['POST'])
def update_upuser():
    """更新UP主记录"""
    try:
        upid = request.form.get('upid')
        platform = request.form.get('platform')
        cn_name = request.form.get('cn_name')
        accountid = request.form.get('accountid')
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE upuser SET platform=%s, cn_name=%s, accountid=%s WHERE upid=%s",
                    (platform, cn_name, accountid, upid)
                )
                connection.commit()
        finally:
            connection.close()
            
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/admin/upuser/delete', methods=['POST'])
def delete_upuser():
    """删除UP主记录"""
    try:
        upid = request.form.get('upid')
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM upuser WHERE upid=%s", (upid,))
                connection.commit()
        finally:
            connection.close()
            
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/admin/keywords/add', methods=['POST'])
def add_keyword():
    """添加商品关键字记录"""
    try:
        keyword = request.form.get('keyword')
        site_type = request.form.get('site_type', 'smzdm')
        enabled = int(request.form.get('enabled', 1))
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO smzdm_keywords (keyword, site_type, enabled) VALUES (%s, %s, %s)",
                    (keyword, site_type, enabled)
                )
                connection.commit()
        finally:
            connection.close()
            
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/admin/keywords/update', methods=['POST'])
def update_keyword():
    """更新商品关键字记录"""
    try:
        id = request.form.get('id')
        keyword = request.form.get('keyword')
        site_type = request.form.get('site_type')
        enabled = int(request.form.get('enabled'))
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE smzdm_keywords SET keyword=%s, site_type=%s, enabled=%s WHERE id=%s",
                    (keyword, site_type, enabled, id)
                )
                connection.commit()
        finally:
            connection.close()
            
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/admin/keywords/delete', methods=['POST'])
def delete_keyword():
    """删除商品关键字记录"""
    try:
        id = request.form.get('id')
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM smzdm_keywords WHERE id=%s", (id,))
                connection.commit()
        finally:
            connection.close()
            
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# 注册蓝图
app.register_blueprint(api_bp)

if __name__ == '__main__':
    # 记录环境信息
    log_environment_info()
    # 启用调试模式，这样Flask会在代码更改时自动重新加载
    app.run(debug=False, host='0.0.0.0')