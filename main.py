from app.views.interface import create_interface
from app.utils.logger import logger


def main():
    """主程序入口"""
    try:
        interface = create_interface()
        interface.launch(
            server_name="0.0.0.0",  # 监听所有网络接口
            server_port=33669,  # 指定端口
            share=False,  # 不使用公共链接
            show_error=True,  # 显示详细错误信息
        )
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        raise


if __name__ == "__main__":
    main()
