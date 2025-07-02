import gradio as gr
from app.controllers.github_overtime import get_github_repos, analyze_github_overtime
import datetime


def create_github_interface():
    """创建GitHub分析界面"""
    
    # GitHub配置输入区域
    with gr.Row():
        with gr.Column(scale=1):
            github_token = gr.Textbox(
                label="🔑 GitHub Token", 
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxx", 
                type="password",
                elem_id="github_token"
            )
            github_author_email = gr.Textbox(
                label="📧 作者邮箱", 
                placeholder="user@example.com, user2@example.com",
                elem_id="github_email"
            )
        with gr.Column(scale=1):
            github_year = gr.Number(
                label="📅 年份", 
                value=datetime.datetime.now().year,
                precision=0,
                elem_id="github_year"
            )
            get_repos_btn = gr.Button(
                "📋 获取仓库列表",
                variant="secondary"
            )
    
    # GitHub工作时间设置
    with gr.Row():
        with gr.Column(scale=1):
            github_work_start_hour = gr.Number(
                label="⏰ 上班时间（小时）",
                value=9,
                precision=0,
                minimum=0,
                maximum=23,
                elem_id="github_work_start"
            )
        with gr.Column(scale=1):
            github_work_end_hour = gr.Number(
                label="🕔 下班时间（小时）",
                value=18,
                precision=0,
                minimum=1,
                maximum=23,
                elem_id="github_work_end"
            )
        with gr.Column(scale=2):
            gr.Markdown("""
            **工作时间说明：**
            - 使用24小时制（如：9表示9:00，18表示18:00）
            - 超过下班时间的提交将被识别为加班
            """, elem_classes="help-text")

    # 仓库选择区域
    with gr.Row():
        repo_selector = gr.CheckboxGroup(
            label="📂 选择要分析的仓库",
            choices=[],
            value=[],
            elem_id="github_repos"
        )

    # GitHub操作按钮
    with gr.Row():
        with gr.Column(scale=1):
            github_submit_btn = gr.Button(
                "🚀 开始分析", 
                variant="primary",
                size="lg"
            )
        with gr.Column(scale=1):
            github_clear_btn = gr.Button(
                "🗑️ 清除配置", 
                variant="secondary",
                size="lg"
            )
        with gr.Column(scale=2):
            github_status_output = gr.Textbox(
                label="📋 分析状态", 
                interactive=False,
                lines=1,
                placeholder="等待分析..."
            )

    # GitHub结果展示区域
    with gr.Row():
        with gr.Column(scale=2):
            github_chart_output = gr.Image(label="📊 GitHub加班情况图表")
        with gr.Column(scale=1):
            github_excel_output = gr.File(label="📥 下载GitHub Excel数据")

    # GitHub使用说明
    with gr.Row():
        gr.Markdown("""
        ## 💡 GitHub 使用说明
        
        **工具介绍：**
        - 🎯 智能分析GitHub代码提交记录，识别加班时间并生成可视化报告
        - 🔒 所有配置信息仅在本次会话中使用，不会被保存
        
        **使用步骤：**
        1. **输入GitHub Token**: 需要repo权限的个人访问令牌
        2. **点击获取仓库列表**: 自动获取您的所有GitHub仓库
        3. **选择分析仓库**: 从列表中选择要分析的仓库
        4. **设置作者邮箱和年份**: 指定分析的邮箱和时间范围
        5. **开始分析**: 系统将分析选中仓库的加班情况
        
        **时间规则：**
        - 工作日超过下班时间至23:00算加班
        - 周末从上班时间开始至23:00算加班
        - 可自定义工作时间范围
        """, elem_classes="compact-text")

    def fetch_github_repos(token):
        if not token or not token.strip():
            return gr.CheckboxGroup.update(choices=[]), "❌ 请先输入GitHub Token"
        
        try:
            repos = get_github_repos(token.strip())
            choices = [(f"{repo['full_name']} - {repo['description'][:50]}{'...' if len(repo['description']) > 50 else ''}", repo['full_name']) for repo in repos]
            return gr.CheckboxGroup.update(choices=choices), f"✅ 成功获取到 {len(repos)} 个仓库"
        except Exception as e:
            return gr.CheckboxGroup.update(choices=[]), f"❌ 获取仓库失败: {str(e)}"

    def on_github_submit(token, author_email, year, selected_repos, work_start_hour, work_end_hour):
        if not token or not token.strip():
            return None, None, "❌ 错误: 请输入GitHub Token"
            
        if not author_email or not author_email.strip():
            return None, None, "❌ 错误: 请输入作者邮箱"
        
        if not selected_repos:
            return None, None, "❌ 错误: 请选择要分析的仓库"
        
        if work_start_hour >= work_end_hour:
            return None, None, "❌ 错误: 上班时间必须早于下班时间"
        
        try:
            chart_path, excel_path = analyze_github_overtime(
                token.strip(),
                author_email.strip(),
                int(year),
                selected_repos,
                int(work_start_hour),
                int(work_end_hour)
            )
            
            final_status = f"🎉 GitHub分析完成！已分析 {len(selected_repos)} 个仓库。"
            return chart_path, excel_path, final_status
            
        except Exception as e:
            error_msg = f"❌ GitHub分析过程出错: {str(e)}"
            return None, None, error_msg

    def clear_github_form():
        return "", "", datetime.datetime.now().year, [], 9, 18, None, None, "🔄 配置已清除"

    # GitHub事件绑定
    get_repos_btn.click(
        fn=fetch_github_repos,
        inputs=[github_token],
        outputs=[repo_selector, github_status_output]
    )
    
    github_submit_btn.click(
        fn=on_github_submit,
        inputs=[github_token, github_author_email, github_year, repo_selector, github_work_start_hour, github_work_end_hour],
        outputs=[github_chart_output, github_excel_output, github_status_output]
    )
    
    github_clear_btn.click(
        fn=clear_github_form,
        outputs=[github_token, github_author_email, github_year, repo_selector, github_work_start_hour, github_work_end_hour, github_chart_output, github_excel_output, github_status_output]
    ) 