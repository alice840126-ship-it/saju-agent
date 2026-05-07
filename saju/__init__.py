"""saju — 사주(四柱) 명리학 결정론 계산 + LLM 풀이 패키지.

공개 API:
    from saju import calc, format_summary
    from saju import calc_daewoon, find_shensha, derive_yongsin
    from saju import analyze_compatibility
    from saju import render_html, save_and_share
"""
from saju.agent import calc, format_summary
from saju.daewoon import calc_daewoon, format_daewoon
from saju.shensha import find_shensha, format_shensha
from saju.yongsin import derive_yongsin, format_yongsin
from saju.compatibility import analyze_compatibility, format_compatibility
from saju.html import render_html, save_and_share

__version__ = "0.1.0"
__all__ = [
    "calc", "format_summary",
    "calc_daewoon", "format_daewoon",
    "find_shensha", "format_shensha",
    "derive_yongsin", "format_yongsin",
    "analyze_compatibility", "format_compatibility",
    "render_html", "save_and_share",
]
