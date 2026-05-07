#!/usr/bin/env python3
"""saju-agent 기본 사용 예제.

실행:
    python3 examples/basic_usage.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from saju import (
    calc, format_summary,
    calc_daewoon, format_daewoon,
    find_shensha, format_shensha,
    derive_yongsin, format_yongsin,
    save_and_share,
)


def main() -> None:
    # 1990.05.15 14:00 서울 (longitude 126.978) — 익명 표본
    result = calc(
        year=1990, month=5, day=15,
        hour=14, minute=0,
        longitude=126.978,      # 서울 동경
        time_mode="approx",     # 정확 출생시간 모를 때 'unknown' 가능
        is_lunar=False,         # 음력이면 True (is_leap_month=True for 윤달)
    )

    print(format_summary(result))
    print()
    print(format_daewoon(calc_daewoon(result, gender="M")))
    print()
    print(format_shensha(find_shensha(result)))
    print()
    print(format_yongsin(derive_yongsin(result)))

    # HTML 대시보드 저장
    out = save_and_share(
        result,
        name="익명",
        daewoon=calc_daewoon(result, gender="M"),
        shensha=find_shensha(result),
        yongsin=derive_yongsin(result),
        output_dir="/tmp",
    )
    print(f"\n📄 HTML: {out['local_path']} ({out['size_bytes']:,} bytes)")


if __name__ == "__main__":
    main()
