import pandas as pd
import matplotlib.pyplot as plt
from app.models.database_manager import DatabaseManager
from app.utils.logger import logger


class ReportGenerator:
    """报告生成器，负责生成图表和导出Excel"""

    def __init__(self, database_manager: DatabaseManager):
        self.db_manager = database_manager

    def create_overtime_chart(self, output_path: str = "overtime_chart.png") -> str:
        """生成加班情况图表"""
        logger.info("生成加班图表...")

        df = self.db_manager.get_daily_overtime_summary()
        if df.empty:
            logger.warning("无数据生成图表")
            return None

        # 数据处理
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)

        # 创建图表
        plt.figure(figsize=(12, 6))
        plt.plot(
            df.index,
            df["Hours_Worked"],
            marker="o",
            linestyle="-",
            linewidth=2,
            markersize=4,
        )
        plt.title("加班情况一览", fontsize=16, fontweight="bold")
        plt.xlabel("日期", fontsize=12)
        plt.ylabel("加班小时数", fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        # 保存图表
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        logger.info(f"图表已保存: {output_path}")
        return output_path

    def export_to_excel(self, output_path: str = "overtime_data.xlsx") -> str:
        """导出数据为Excel文件"""
        logger.info("导出Excel...")

        # 获取所有数据
        df = self.db_manager.get_overtime_data()

        # 创建Excel文件，包含多个工作表
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            # 详细数据表
            df.to_excel(writer, sheet_name="详细记录", index=False)

            # 汇总统计表
            if not df.empty:
                summary_df = self._create_summary_stats(df)
                summary_df.to_excel(writer, sheet_name="统计汇总", index=False)

        logger.info(f"已导出: {output_path}")
        return output_path

    def _create_summary_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建统计汇总数据"""
        try:
            # 按日期汇总
            daily_summary = (
                df.groupby("date")
                .agg(
                    {
                        "hours_worked": "sum",
                        "repository_name": "nunique",
                        "branch": "nunique",
                    }
                )
                .reset_index()
            )

            # 重命名列
            daily_summary.columns = ["日期", "总加班小时", "涉及仓库数", "涉及分支数"]

            # 添加统计信息
            total_hours = df["hours_worked"].sum()
            total_days = len(df["date"].unique())
            avg_hours = total_hours / total_days if total_days > 0 else 0

            # 添加汇总行
            summary_row = pd.DataFrame(
                {
                    "日期": ["总计"],
                    "总加班小时": [total_hours],
                    "涉及仓库数": [df["repository_name"].nunique()],
                    "涉及分支数": [df["branch"].nunique()],
                }
            )

            avg_row = pd.DataFrame(
                {
                    "日期": ["日均"],
                    "总加班小时": [round(avg_hours, 2)],
                    "涉及仓库数": [""],
                    "涉及分支数": [""],
                }
            )

            # 合并所有数据
            result = pd.concat([daily_summary, summary_row, avg_row], ignore_index=True)
            return result

        except Exception as e:
            logger.error(f"创建统计汇总出错: {e}")
            return pd.DataFrame()
