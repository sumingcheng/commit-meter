import gradio as gr
from app.controller.overtime_controller import analyze_and_plot
import datetime

def create_interface():
    with gr.Blocks() as gradio:
        gr.Markdown("# 加班分析工具")

        with gr.Row():
            access_token = gr.Textbox(label="GitLab Token", placeholder="请输入访问令牌", elem_id="token")
            base_url = gr.Textbox(label="Git Base URL", placeholder="请输入 GitLab 的基础 URL", elem_id="url")
            author_email = gr.Textbox(label="邮箱", placeholder="请输入作者邮箱", elem_id="email")
            year = gr.Number(label="年份", value=datetime.datetime.now().year, elem_id="year")

        with gr.Row():
            submit_btn = gr.Button("分析加班数据")

        chart_output = gr.Image(label="加班情况图")
        excel_output = gr.File(label="下载数据 Excel")

        def on_submit(access_token, base_url, author_email, year):
            chart_path, excel_path = analyze_and_plot(access_token, base_url, author_email, year)
            return chart_path, excel_path

        submit_btn.click(on_submit, inputs=[access_token, base_url, author_email, year],
                         outputs=[chart_output, excel_output])

    return gradio
