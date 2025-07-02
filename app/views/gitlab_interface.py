import gradio as gr
from app.controllers.overtime import analyze_and_plot, get_gitlab_projects
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
        with gr.Column(scale=1):
            get_projects_btn = gr.Button(
                "📋 获取项目列表",
                variant="secondary"
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

    with gr.Row():
        project_selector = gr.CheckboxGroup(
            label="📂 选择要分析的项目",
            choices=[],
            value=[],
            elem_id="gitlab_projects"
        )

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
        
        **使用步骤：**
        1. **输入GitLab Token**: 需要仓库读取权限的访问令牌
        2. **设置GitLab URL**: 输入GitLab实例的API地址
        3. **点击获取项目列表**: 自动获取您有权限的所有项目
        4. **选择分析项目**: 从列表中选择要分析的项目（可多选）
        5. **设置作者邮箱和年份**: 指定分析的邮箱和时间范围
        6. **开始分析**: 系统将分析选中项目的加班情况
        
        **时间规则：**
        - 工作日超过下班时间至23:00算加班
        - 周末从上班时间开始至23:00算加班
        - 可自定义工作时间范围
        """, elem_classes="compact-text")

    def fetch_gitlab_projects(token, base_url):
        if not token or not token.strip():
            return gr.CheckboxGroup.update(choices=[]), "❌ 请先输入GitLab Token"
        
        if not base_url or not base_url.strip():
            return gr.CheckboxGroup.update(choices=[]), "❌ 请先输入GitLab Base URL"
        
        try:
            projects = get_gitlab_projects(token.strip(), base_url.strip())
            choices = [(f"{proj['path_with_namespace']} - {proj['description'][:50]}{'...' if len(proj['description']) > 50 else ''}", proj['path_with_namespace']) for proj in projects]
            return gr.CheckboxGroup.update(choices=choices), f"✅ 成功获取 {len(projects)} 个项目"
        except Exception as e:
            return gr.CheckboxGroup.update(choices=[]), f"❌ 获取项目失败: {str(e)}"

    def on_gitlab_submit(access_token, base_url, author_email, year, selected_projects, work_start_hour, work_end_hour):
        if not access_token or not access_token.strip():
            return None, None, "❌ 错误: 请输入GitLab Token"
        
        if not base_url or not base_url.strip():
            return None, None, "❌ 错误: 请输入GitLab Base URL"
            
        if not author_email or not author_email.strip():
            return None, None, "❌ 错误: 请输入作者邮箱"
        
        if not selected_projects:
            return None, None, "❌ 错误: 请选择要分析的项目"
        
        if work_start_hour >= work_end_hour:
            return None, None, "❌ 错误: 上班时间必须早于下班时间"
        
        try:
            chart_path, excel_path = analyze_and_plot(
                access_token.strip(), 
                base_url.strip(), 
                author_email.strip(), 
                int(year),
                selected_projects,
                int(work_start_hour),
                int(work_end_hour)
            )
            
            return chart_path, excel_path, f"🎉 GitLab分析完成！已分析 {len(selected_projects)} 个项目。"
            
        except Exception as e:
            return None, None, f"❌ GitLab分析过程出错: {str(e)}"

    def clear_gitlab_form():
        return "", "", "", datetime.datetime.now().year, [], 9, 18, None, None, "🔄 配置已清除"

    # 事件绑定
    get_projects_btn.click(
        fn=fetch_gitlab_projects,
        inputs=[access_token, base_url],
        outputs=[project_selector, status_output]
    )
    
    submit_btn.click(
        fn=on_gitlab_submit, 
        inputs=[access_token, base_url, author_email, year, project_selector, work_start_hour, work_end_hour],
        outputs=[chart_output, excel_output, status_output]
    )
    
    clear_btn.click(
        fn=clear_gitlab_form,
        outputs=[access_token, base_url, author_email, year, project_selector, work_start_hour, work_end_hour, chart_output, excel_output, status_output]
    ) 