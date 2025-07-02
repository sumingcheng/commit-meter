import gradio as gr
from app.views.gitlab_interface import create_gitlab_interface
from app.views.github_interface import create_github_interface


def create_interface():
    """创建主界面，包含GitLab和GitHub两个分析Tab"""
    with gr.Blocks(
        title="Commit Meter - 加班分析工具", theme=gr.themes.Soft()
    ) as gradio:
        # 头部区域 - 标题
        gr.Markdown("# 🕒 Commit Meter - 加班分析工具")

        # 创建两个Tab
        with gr.Tabs():
            # GitLab Tab
            with gr.TabItem("GitLab 分析"):
                create_gitlab_interface()

            # GitHub Tab
            with gr.TabItem("GitHub 分析"):
                create_github_interface()

    return gradio
