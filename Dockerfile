# 使用官方 Python 运行时作为基础镜像
FROM python:3.11.14-slim

# 设置工作目录
WORKDIR /app

# 配置pip使用清华大学镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 复制 requirements.txt 并安装依赖
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件，但排除sql目录
COPY . .

# 暴露端口
EXPOSE 5000

# 设置环境变量
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# 运行应用：先执行数据库迁移（幂等），再启动应用
CMD ["sh", "-c", "python tool/migrate.py && flask run --host=0.0.0.0"]