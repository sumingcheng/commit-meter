FROM python:3.13-slim as builder

# 安装uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# 设置工作目录
WORKDIR /commit-meter

# 复制项目配置文件
COPY pyproject.toml uv.lock ./

# 安装依赖
RUN uv sync --frozen --no-cache

# 生产阶段
FROM python:3.13-slim

# 安装uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# 复制虚拟环境
COPY --from=builder /commit-meter/.venv /commit-meter/.venv

# 复制项目代码
COPY . /commit-meter
WORKDIR /commit-meter

# 确保使用虚拟环境
ENV PATH="/commit-meter/.venv/bin:$PATH"

EXPOSE 13000

CMD ["python", "main.py"]
