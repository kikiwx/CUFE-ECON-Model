"""
工具模块
中央财经大学经济学院 - 经济学大模型聊天助手
"""

from .document_utils import (
    create_word_document,
    create_markdown_document,
    clean_text_for_word,
    set_font_style,
    validate_document_data,
    get_document_statistics
)

from .text_utils import (
    validate_input,
    contains_malicious_content,
    clean_markdown_for_word,
    extract_key_phrases,
    summarize_text,
    format_text_for_display,
    detect_language,
    normalize_whitespace,
    escape_html,
    count_words,
    TextProcessor
)

__all__ = [
    'create_word_document',
    'create_markdown_document',
    'clean_text_for_word',
    'set_font_style',
    'validate_document_data',
    'get_document_statistics',

    'validate_input',
    'contains_malicious_content',
    'clean_markdown_for_word',
    'extract_key_phrases',
    'summarize_text',
    'format_text_for_display',
    'detect_language',
    'normalize_whitespace',
    'escape_html',
    'count_words',
    'TextProcessor'
]

__version__ = '1.0.0'