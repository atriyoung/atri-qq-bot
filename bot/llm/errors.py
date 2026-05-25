"""LLM 自定义异常"""


class LLMError(Exception):
    """LLM 通用异常"""
    pass


class RateLimitError(LLMError):
    """速率限制"""
    pass


class ContentFilterError(LLMError):
    """内容被过滤"""
    pass


class APITimeoutError(LLMError):
    """API 超时"""
    pass


class APIConnectionError(LLMError):
    """API 连接失败"""
    pass
