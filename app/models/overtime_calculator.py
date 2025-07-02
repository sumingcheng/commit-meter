import datetime
import pytz
from typing import List, Dict, Any
from app.utils.logger import logger


class OvertimeCalculator:
    """加班计算器，负责加班时间的计算逻辑"""

    def __init__(
        self, local_tz: pytz.timezone, work_start_hour: int = 9, work_end_hour: int = 18
    ):
        self.local_tz = local_tz
        self.work_start_hour = work_start_hour
        self.work_end_hour = work_end_hour
        self.overtime_end_hour = 23  # 加班统计截止时间

    def parse_commit_time(self, commit_created_at: str) -> datetime.datetime:
        """解析提交时间并转换为本地时区"""
        try:
            commit_time_utc = datetime.datetime.strptime(
                commit_created_at, "%Y-%m-%dT%H:%M:%S.%f%z"
            )
        except ValueError:
            commit_time_utc = datetime.datetime.strptime(
                commit_created_at, "%Y-%m-%dT%H:%M:%S%z"
            )
        return commit_time_utc.astimezone(self.local_tz)

    def is_overtime_commit(self, commit_time: datetime.datetime) -> bool:
        """判断提交是否属于加班时间"""
        weekday = commit_time.weekday()
        hour = commit_time.hour

        # 周末全天算加班
        if weekday >= 5:
            return True

        # 工作日超过下班时间且未超过统计截止时间算加班
        return self.work_end_hour <= hour < self.overtime_end_hour

    def categorize_commits_by_date(
        self, commits: List[Dict[str, Any]], author_emails: List[str]
    ) -> Dict[datetime.date, Dict[str, Any]]:
        """按日期分类提交记录，并标记是否为加班"""
        overtime_records = {}

        for commit in commits:
            if commit["author_email"] not in author_emails:
                continue

            commit_time_local = self.parse_commit_time(commit["created_at"])

            if not self.is_overtime_commit(commit_time_local):
                continue

            date_key = commit_time_local.date()
            weekday = commit_time_local.weekday()

            # 确定加班开始时间
            if weekday >= 5:  # 周末
                start_time = datetime.datetime.combine(
                    date_key,
                    datetime.time(self.work_start_hour, 0),
                    tzinfo=self.local_tz,
                )
                is_weekend = True
            else:  # 工作日
                start_time = datetime.datetime.combine(
                    date_key,
                    datetime.time(self.work_end_hour, 0),
                    tzinfo=self.local_tz,
                )
                is_weekend = False

            overtime_records.setdefault(
                date_key,
                {
                    "commits": [],
                    "start_time": start_time,
                    "is_weekend": is_weekend,
                },
            )["commits"].append(commit)

        return overtime_records

    def calculate_overtime_hours(
        self,
        commits_on_date: List[Dict[str, Any]],
        start_time: datetime.datetime,
        is_weekend: bool,
    ) -> float:
        """计算指定日期的加班小时数"""
        if not commits_on_date:
            return 0.0

        # 按时间排序提交
        commits_on_date.sort(key=lambda x: self.parse_commit_time(x["created_at"]))

        # 获取最后提交时间
        last_commit_time = self.parse_commit_time(commits_on_date[-1]["created_at"])
        date_key = last_commit_time.date()

        # 确保最后提交时间不超过当天23:59:59
        end_time = datetime.datetime.combine(
            date_key,
            datetime.time(self.overtime_end_hour, 59, 59),
            tzinfo=self.local_tz,
        )
        last_commit_time = min(last_commit_time, end_time)

        # 计算加班时长
        if is_weekend:
            # 周末从设定的上班时间开始计算
            hours_worked = (last_commit_time - start_time).total_seconds() / 3600
        else:
            # 工作日从下班时间开始计算
            overtime_duration = (last_commit_time - start_time).total_seconds() / 3600
            if overtime_duration < 1:
                logger.info(f"工作日加班时间不足1小时，跳过记录: {date_key}")
                return 0.0
            hours_worked = overtime_duration

        return round(max(hours_worked, 0), 2)

    def create_overtime_record(
        self,
        project_id: str,
        repository_name: str,
        branch: str,
        date: datetime.date,
        commits_on_date: List[Dict[str, Any]],
        hours_worked: float,
        author_email: str,
        commit_hash_field: str = "id"  # 添加参数指定hash字段名
    ) -> Dict[str, Any]:
        """创建加班记录字典"""
        last_commit = commits_on_date[-1]
        last_commit_time = self.parse_commit_time(last_commit["created_at"])
        
        return {
            "repository_id": project_id,
            "repository_name": repository_name,
            "branch": branch,
            "date": date.isoformat(),
            "last_commit_time": last_commit_time.strftime("%H:%M:%S"),
            "hours_worked": hours_worked,
            "last_commit_message": last_commit.get("title", ""),
            "commit_hash": last_commit.get(commit_hash_field, ""),
            "author_email": author_email,
        }
