# commit-meter

GitLab代码提交记录的加班统计分析工具 - 智能识别加班时间，生成可视化报告。

## 功能特点

- 🕒 **智能加班检测** - 自动识别工作日加班(18:00-23:00)和周末工作时间
- 📊 **可视化报告** - 生成时间线图表和详细Excel数据导出
- 🔄 **多仓库支持** - 批量分析多个GitLab项目的提交记录
- 🌐 **Web界面** - 基于Gradio的现代化用户界面
- 🐳 **容器化部署** - 支持Docker一键部署

## 快速开始

### 方法一：使用 uv (推荐)

```bash
# 安装uv (如果未安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆项目
git clone <repository-url>
cd commit-meter

# 同步依赖
uv sync

# 运行应用
uv run python main.py
```

## 直接启动

```bash
# 同步依赖并启动
uv sync
uv run python main.py

# 或使用Makefile
make run-local
```

## 开发指南

### 安装开发依赖
```bash
uv sync --extra dev
```

## Docker部署

```bash
# 构建镜像
make build

# 运行容器
make run

# 停止服务
make down
```
