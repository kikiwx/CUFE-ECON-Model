"""
模型模块
中央财经大学经济学院 - 经济学大模型聊天助手
"""

from .chatbot import QwenChatBot
from .report_generator import ReportGenerator

__all__ = ['QwenChatBot', 'ReportGenerator']
__version__ = '1.0.0'