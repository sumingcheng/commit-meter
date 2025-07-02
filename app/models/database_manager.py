import sqlite3
import pandas as pd
from typing import Dict, Any
from app.settings.config import Config
from app.utils.logger import logger


class DatabaseManager:
    """数据库管理类，负责所有数据库操作"""

    def __init__(self, database_path: str = None):
        self.database_path = database_path or Config.DATABASE_PATH
        self.conn = self._setup_database()

    def _setup_database(self) -> sqlite3.Connection:
        """设置数据库连接和表结构"""
        logger.info("设置数据库...")
        conn = sqlite3.connect(self.database_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Overtime (
                repository_id TEXT,
                repository_name TEXT,
                branch TEXT,
                date TEXT,
                last_commit_time TEXT,
                hours_worked REAL,
                last_commit_message TEXT,
                author_email TEXT,
                commit_hash TEXT,
                PRIMARY KEY (repository_id, branch, date, commit_hash)
            )
        """
        )
        conn.commit()
        logger.info("数据库设置完成。")
        return conn

    def check_duplicate_record(self, commit_hash: str) -> bool:
        """检查提交记录是否已存在"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM Overtime WHERE commit_hash = ?", (commit_hash,)
        )
        return cursor.fetchone()[0] > 0

    def insert_overtime_record(self, record: Dict[str, Any]) -> bool:
        """插入加班记录"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO Overtime (
                    repository_id, repository_name, branch, date, 
                    last_commit_time, hours_worked, last_commit_message, 
                    commit_hash, author_email
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["repository_id"],
                    record["repository_name"],
                    record["branch"],
                    record["date"],
                    record["last_commit_time"],
                    record["hours_worked"],
                    record["last_commit_message"],
                    record["commit_hash"],
                    record["author_email"],
                ),
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"插入记录失败: {e}")
            return False

    def get_overtime_data(self) -> pd.DataFrame:
        """获取所有加班数据"""
        return pd.read_sql_query("SELECT * FROM Overtime", self.conn)

    def get_daily_overtime_summary(self) -> pd.DataFrame:
        """获取每日加班汇总数据"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT date, SUM(hours_worked) as total_hours FROM Overtime GROUP BY date"
        )
        data = cursor.fetchall()
        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data, columns=["Date", "Hours_Worked"])

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            logger.info("关闭数据库连接...")
            self.conn.close()
