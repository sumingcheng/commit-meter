import gradio as gr
from app.controllers.overtime import analyze_and_plot
import datetime


def create_gitlab_interface():
    """创建GitLab分析界面"""
    
    # 配置输入区域 - 更紧凑的布局
    with gr.Row():
        with gr.Column(scale=1):
            access_token = gr.Textbox(
                label="🔑 GitLab Token", 
                placeholder="glpat-xxxxxxxxxxxxxxxxxxxx", 
                type="password",
                elem_id="gitlab_token"
            )
            author_email = gr.Textbox(
                label="📧 作者邮箱", 
                placeholder="user@example.com, user2@example.com",
                elem_id="gitlab_email"
            )
        with gr.Column(scale=1):
            base_url = gr.Textbox(
                label="🌐 GitLab Base URL", 
                placeholder="https://gitlab.example.com/api/v4",
                value="https://gitlabcode.com/api/v4",
                elem_id="gitlab_url"
            )
            year = gr.Number(
                label="📅 年份", 
                value=datetime.datetime.now().year,
                precision=0,
                elem_id="gitlab_year"
            )
    
    # 工作时间设置区域
    with gr.Row():
        with gr.Column(scale=1):
            work_start_hour = gr.Number(
                label="⏰ 上班时间（小时）",
                value=9,
                precision=0,
                minimum=0,
                maximum=23,
                elem_id="gitlab_work_start"
            )
        with gr.Column(scale=1):
            work_end_hour = gr.Number(
                label="🕔 下班时间（小时）",
                value=18,
                precision=0,
                minimum=1,
                maximum=23,
                elem_id="gitlab_work_end"
            )
        with gr.Column(scale=2):
            gr.Markdown("""
            **工作时间说明：**
            - 使用24小时制（如：9表示9:00，18表示18:00）
            - 超过下班时间的提交将被识别为加班
            """, elem_classes="help-text")

    # 操作按钮区域
    with gr.Row():
        with gr.Column(scale=1):
            submit_btn = gr.Button(
                "🚀 开始分析", 
                variant="primary",
                size="lg"
            )
        with gr.Column(scale=1):
            clear_btn = gr.Button(
                "🗑️ 清除配置", 
                variant="secondary",
                size="lg"
            )
        with gr.Column(scale=2):
            # 状态显示区域
            status_output = gr.Textbox(
                label="📋 分析状态", 
                interactive=False,
                lines=1,
                placeholder="等待分析..."
            )

    # 结果展示区域
    with gr.Row():
        with gr.Column(scale=2):
            chart_output = gr.Image(label="📊 加班情况图表")
        with gr.Column(scale=1):
            excel_output = gr.File(label="📥 下载Excel数据")

    # GitLab使用说明
    with gr.Row():
        gr.Markdown("""
        ## 💡 GitLab 使用说明
        
        **工具介绍：**
        - 🎯 智能分析GitLab代码提交记录，识别加班时间并生成可视化报告
        - 🔒 所有配置信息仅在本次会话中使用，不会被保存
        
        **配置说明：**
        - **GitLab Token**: 访问令牌，需要仓库读取权限
        - **Base URL**: API地址，如 `https://gitlab.com/api/v4`
        - **作者邮箱**: 开发者邮箱，支持多个（逗号分隔）
        - **年份**: 分析的目标年份
        
        **分析范围：**
        - 🔄 自动获取您有权限访问的所有仓库
        - 📊 分析指定邮箱在这些仓库中的提交记录
        
        **时间规则：**
        - 工作日超过下班时间至23:00算加班
        - 周末从上班时间开始至23:00算加班
        - 可自定义工作时间范围
        """, elem_classes="compact-text")

    def on_gitlab_submit(access_token, base_url, author_email, year, work_start_hour, work_end_hour):
        if not access_token or not access_token.strip():
            return None, None, "❌ 错误: 请输入GitLab Token"
        
        if not base_url or not base_url.strip():
            return None, None, "❌ 错误: 请输入GitLab Base URL"
            
        if not author_email or not author_email.strip():
            return None, None, "❌ 错误: 请输入作者邮箱"
        
        if work_start_hour >= work_end_hour:
            return None, None, "❌ 错误: 上班时间必须早于下班时间"
        
        try:
            chart_path, excel_path = analyze_and_plot(
                access_token.strip(), 
                base_url.strip(), 
                author_email.strip(), 
                int(year),
                int(work_start_hour),
                int(work_end_hour)
            )
            
            final_status = "🎉 GitLab分析完成！图表和Excel文件已生成。"
            return chart_path, excel_path, final_status
            
        except Exception as e:
            error_msg = f"❌ GitLab分析过程出错: {str(e)}"
            return None, None, error_msg

    def clear_gitlab_form():
        return "", "", "", datetime.datetime.now().year, 9, 18, None, None, "🔄 配置已清除"

    # 事件绑定
    submit_btn.click(
        fn=on_gitlab_submit, 
        inputs=[access_token, base_url, author_email, year, work_start_hour, work_end_hour],
        outputs=[chart_output, excel_output, status_output]
    )
    
    clear_btn.click(
        fn=clear_gitlab_form,
        outputs=[access_token, base_url, author_email, year, work_start_hour, work_end_hour, chart_output, excel_output, status_output]
    ) 