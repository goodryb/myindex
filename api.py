from flask import Blueprint, request, jsonify
from datetime import datetime
import db  # 导入数据库模块

# 创建一个蓝图对象，url_prefix 会自动为该蓝图下的所有路由添加 /api 前缀
api_bp = Blueprint('api', __name__, url_prefix='/api')

# --- 统一错误处理 ---
@api_bp.errorhandler(Exception)
def handle_api_exception(e):
    """
    统一处理 API 蓝图中的所有异常，确保返回 JSON 格式
    """
    from werkzeug.exceptions import HTTPException
    import logging
    
    # 记录详细日志
    logging.error(f"API Error occurred: {str(e)}", exc_info=True)
    
    # 如果是标准的 HTTP 异常 (如 404, 405, 400 等)
    if isinstance(e, HTTPException):
        return jsonify({
            'success': False,
            'error': e.name,
            'message': e.description
        }), e.code
    
    # 对于非标准的异常（如数据库报错、代码逻辑错误），返回 500
    return jsonify({
        'success': False,
        'error': 'Internal Server Error',
        'details': str(e)
    }), 500

# --- API 路由定义 ---
# 事件心跳上报API
@api_bp.route('/event_heartbeat', methods=['GET'])
def event_heartbeat():
    """
    事件心跳上报接口
    GET /api/event_heartbeat?event_name=<事件名称>&timestamp=<可选时间戳>
    """
    event_name = request.args.get('event_name')
    
    if not event_name:
        return jsonify({
            'success': False,
            'error': 'Missing event_name parameter'
        }), 400
    
    # 验证event_name长度
    if len(event_name) > 100:
        return jsonify({
            'success': False,
            'error': 'event_name exceeds maximum length of 100 characters'
        }), 400
    
    # 获取时间戳参数，如果未提供则使用当前时间
    timestamp_str = request.args.get('timestamp')
    if timestamp_str:
        try:
            # 尝试解析时间戳
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid timestamp format. Use ISO 8601 format.'
            }), 400
    else:
        timestamp = datetime.now()
    
    connection = None
    try:
        connection = db.get_db_connection()
        with connection.cursor() as cursor:
            # 使用INSERT ... ON DUPLICATE KEY UPDATE来更新或插入记录
            sql = """
            INSERT INTO event_heartbeat (event_name, latest_heartbeat) 
            VALUES (%s, %s) 
            ON DUPLICATE KEY UPDATE latest_heartbeat = %s
            """
            cursor.execute(sql, (event_name, timestamp, timestamp))
            connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Event heartbeat updated successfully',
                'event_name': event_name,
                'timestamp': timestamp.isoformat()
            })
            
    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({
            'success': False,
            'error': f'Database error: {str(e)}'
        }), 500
    finally:
        if connection:
            connection.close()