# commit-meter

GitLab & GitHub 代码提交记录的加班统计分析工具 - 智能识别加班时间，生成可视化报告。
![image](https://github.com/user-attachments/assets/99536159-c359-42dc-9121-4a286110cc50)

## 功能特点

- 🕒 **智能加班检测** - 自动识别工作日加班(18:00-23:00)和周末工作时间
- 📊 **可视化报告** - 生成时间线图表和详细 Excel 数据导出
- 🔄 **多平台支持** - 支持 GitLab 和 GitHub 两大代码托管平台
- 🌐 **现代化界面** - 基于 Gradio 的 Web 界面，支持双平台独立分析
- 🗂️ **仓库选择** - GitLab 自动获取权限仓库，GitHub 可选择性分析
- 🐳 **容器化部署** - 支持 Docker 一键部署

## 平台功能对比

| 功能       | GitLab                  | GitHub                         |
| ---------- | ----------------------- | ------------------------------ |
| Token 认证 | ✅ Private Token        | ✅ Personal Access Token       |
| 仓库获取   | ✅ 自动获取所有权限仓库 | ✅ 自动获取用户仓库            |
| 仓库选择   | ❌ 分析所有仓库         | ✅ 可选择性分析                |
| 独立数据库 | ✅ overtime_analysis.db | ✅ github_overtime_analysis.db |

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

## 使用说明

### GitLab 分析

1. 获取 GitLab Private Token (需要仓库读取权限)
2. 输入 GitLab 实例 URL (如: https://gitlab.com/api/v4)
3. 设置作者邮箱和分析年份
4. 工具自动获取所有可访问仓库进行分析

### GitHub 分析

1. 生成 GitHub Personal Access Token (需要 repo 权限)
2. 点击"获取仓库列表"获取所有仓库
3. 选择要分析的仓库
4. 设置作者邮箱和分析年份进行分析

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

## Docker 部署

```bash
# 构建镜像
make build

# 运行容器
make run

# 停止服务
make down
```
