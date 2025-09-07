"""
文本处理工具
中央财经大学经济学院 - 经济学大模型聊天助手
"""

import re
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


def validate_input(text: str, max_length: Optional[int] = None, min_length: Optional[int] = None) -> Optional[str]:
    """
    验证输入文本

    Args:
        text: 要验证的文本
        max_length: 最大长度限制
        min_length: 最小长度限制

    Returns:
        错误消息，如果验证通过则返回None
    """
    if not isinstance(text, str):
        return "输入必须是字符串类型"

    if not text or not text.strip():
        return "不能为空"

    text_length = len(text.strip())

    if min_length and text_length < min_length:
        return f"长度不能少于{min_length}个字符"

    if max_length and text_length > max_length:
        return f"长度不能超过{max_length}个字符"

    if contains_malicious_content(text):
        return "包含不允许的内容"

    return None


def contains_malicious_content(text: str) -> bool:
    """
    检查文本是否包含恶意内容

    Args:
        text: 要检查的文本

    Returns:
        如果包含恶意内容返回True
    """
    malicious_patterns = [
        r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'eval\s*\(',
    ]

    for pattern in malicious_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


def clean_markdown_for_word(text: str) -> str:
    """清理Markdown格式，转换为适合Word的格式"""
    if not text:
        return text


    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)

    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)

    text = re.sub(r'\*(.*?)\*', r'\1', text)

    text = re.sub(r'^\s*[-\*\+]\s*', '• ', text, flags=re.MULTILINE)

    text = re.sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1', text)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]*)`', r'\1', text)

    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)

    return text.strip()


def extract_key_phrases(text: str, max_phrases: int = 10) -> List[str]:
    """
    提取文本中的关键短语

    Args:
        text: 输入文本
        max_phrases: 最大短语数量

    Returns:
        关键短语列表
    """
    if not text:
        return []

    cleaned_text = re.sub(r'[^\w\s]', ' ', text)

    words = cleaned_text.split()

    stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很',
                  '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}

    filtered_words = [word for word in words if len(word) > 1 and word not in stop_words]

    word_freq = {}
    for word in filtered_words:
        word_freq[word] = word_freq.get(word, 0) + 1

    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

    return [word for word, freq in sorted_words[:max_phrases]]


def summarize_text(text: str, max_sentences: int = 3) -> str:
    """
    简单的文本摘要

    Args:
        text: 输入文本
        max_sentences: 最大句子数

    Returns:
        摘要文本
    """
    if not text:
        return ""

    sentences = re.split(r'[。！？]', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if len(sentences) <= max_sentences:
        return text

    return '。'.join(sentences[:max_sentences]) + '。'


def format_text_for_display(text: str, max_length: int = 100) -> str:
    """
    格式化文本用于显示（截断长文本）

    Args:
        text: 输入文本
        max_length: 最大显示长度

    Returns:
        格式化后的文本
    """
    if not text:
        return ""

    text = re.sub(r'\s+', ' ', text.strip())

    if len(text) <= max_length:
        return text

    return text[:max_length - 3] + "..."


def detect_language(text: str) -> str:
    """
    简单的语言检测

    Args:
        text: 输入文本

    Returns:
        语言代码 ('zh' 或 'en' 或 'unknown')
    """
    if not text:
        return "unknown"

    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))

    english_chars = len(re.findall(r'[a-zA-Z]', text))

    total_chars = len(text)

    if chinese_chars / total_chars > 0.3:
        return "zh"
    elif english_chars / total_chars > 0.5:
        return "en"
    else:
        return "unknown"


def normalize_whitespace(text: str) -> str:
    """
    标准化空白字符

    Args:
        text: 输入文本

    Returns:
        标准化后的文本
    """
    if not text:
        return ""

    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def escape_html(text: str) -> str:
    """
    转义HTML特殊字符

    Args:
        text: 输入文本

    Returns:
        转义后的文本
    """
    if not text:
        return ""

    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&#x27;",
        ">": "&gt;",
        "<": "&lt;",
    }

    return "".join(html_escape_table.get(c, c) for c in text)


def count_words(text: str) -> Dict[str, int]:
    """
    统计文本字数信息

    Args:
        text: 输入文本

    Returns:
        包含各种统计信息的字典
    """
    if not text:
        return {
            "total_chars": 0,
            "chars_no_spaces": 0,
            "words": 0,
            "sentences": 0,
            "paragraphs": 0
        }

    total_chars = len(text)

    chars_no_spaces = len(re.sub(r'\s', '', text))

    words = len(text.split())

    sentences = len(re.findall(r'[。！？.!?]+', text))

    paragraphs = len([p for p in text.split('\n\n') if p.strip()])

    return {
        "total_chars": total_chars,
        "chars_no_spaces": chars_no_spaces,
        "words": words,
        "sentences": sentences,
        "paragraphs": paragraphs
    }


def extract_urls(text: str) -> List[str]:
    """
    提取文本中的URL

    Args:
        text: 输入文本

    Returns:
        URL列表
    """
    if not text:
        return []

    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)

    return list(set(urls))  # 去重


def truncate_by_words(text: str, word_count: int) -> str:
    """
    按词数截断文本

    Args:
        text: 输入文本
        word_count: 保留的词数

    Returns:
        截断后的文本
    """
    if not text:
        return ""

    words = text.split()
    if len(words) <= word_count:
        return text

    return ' '.join(words[:word_count]) + '...'


def safe_filename(filename: str) -> str:
    """
    生成安全的文件名

    Args:
        filename: 原文件名

    Returns:
        安全的文件名
    """
    if not filename:
        return "untitled"

    # 移除或替换不安全的字符
    safe_chars = re.sub(r'[^\w\s-]', '', filename)
    safe_chars = re.sub(r'[-\s]+', '-', safe_chars)

    # 限制长度
    return safe_chars[:50].strip('-')


class TextProcessor:
    """文本处理器类，集成各种文本处理功能"""

    def __init__(self):
        self.logger = logging.getLogger(__name__ + '.TextProcessor')

    def process_for_model(self, text: str) -> str:
        """为模型输入准备文本"""
        try:

            text = normalize_whitespace(text)

            if contains_malicious_content(text):
                self.logger.warning("检测到潜在恶意内容，已清理")
                text = re.sub(r'<[^>]*>', '', text)

            return text

        except Exception as e:
            self.logger.error(f"文本预处理失败: {e}")
            return text

    def process_for_display(self, text: str, max_length: int = 500) -> str:
        """为显示准备文本"""
        try:
            text = escape_html(text)

            text = format_text_for_display(text, max_length)

            return text

        except Exception as e:
            self.logger.error(f"显示文本处理失败: {e}")
            return text

    def extract_metadata(self, text: str) -> Dict:
        """提取文本元数据"""
        try:
            return {
                'word_count': count_words(text),
                'language': detect_language(text),
                'key_phrases': extract_key_phrases(text),
                'urls': extract_urls(text)
            }
        except Exception as e:
            self.logger.error(f"提取文本元数据失败: {e}")
            return {}