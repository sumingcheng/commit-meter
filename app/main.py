from app.view.overtime_view import create_interface
from app.journal.logger_setup import logger

if __name__ == "__main__":
    try:
        interface = create_interface()
        interface.launch()
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        raise
