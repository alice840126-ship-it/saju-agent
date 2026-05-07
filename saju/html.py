#!/usr/bin/env python3
"""saju.html — 사주 명식 HTML 대시보드 생성.

팔레트(Terra 액센트, 전통/따뜻함) + 오행 5색 적용.
모바일·웹뷰 호환 (CDN 없음, Chart.js 미사용, 순수 CSS).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ELEMENT_COLOR = {
    "木": "#34C759", "火": "#B8422E", "土": "#D9A441",
    "金": "#C8C8C8", "水": "#345D7E",
}
ELEMENT_KO = {"木": "목 木", "火": "화 火", "土": "토 土", "金": "금 金", "水": "수 水"}


def render_html(
    saju: Dict[str, Any],
    name: str = "익명",
    daewoon: Optional[Dict[str, Any]] = None,
    shensha: Optional[Dict[str, Any]] = None,
    yongsin: Optional[Dict[str, Any]] = None,
) -> str:
    p = saju["pillars"]
    dm = saju["day_master"]
    fe = saju["five_elements"]
    inp = saju["input"]
    birth = f"{inp['year']}.{inp['month']:02d}.{inp['day']:02d}"
    has_hour = p["hour_pillar"] is not None

    from saju.agent import STEM_ELEMENT, BRANCH_ELEMENT

    pillar_cards = []
    for label, key in [("시주", "hour"), ("일주", "day"), ("월주", "month"), ("년주", "year")]:
        pl = p[f"{key}_pillar"]
        if not pl:
            pillar_cards.append(f'<div class="pillar empty"><div class="plabel">{label}</div><div class="pchar">·</div></div>')
            continue
        stem, branch = pl[0], pl[1]
        s_el = STEM_ELEMENT[stem][0]
        b_el = BRANCH_ELEMENT[branch][0]
        pillar_cards.append(
            f'<div class="pillar"><div class="plabel">{label}</div>'
            f'<div class="pstem" style="background:{ELEMENT_COLOR[s_el]}">{stem}</div>'
            f'<div class="pbranch" style="background:{ELEMENT_COLOR[b_el]}">{branch}</div>'
            f'<div class="pname">{pl}</div></div>'
        )

    dist = fe["distribution"]
    total = sum(dist.values()) or 1
    bars = []
    for el in ("木", "火", "土", "金", "水"):
        cnt = dist[el]
        pct = cnt / total * 100
        bars.append(
            f'<div class="bar-row"><div class="bar-label">{ELEMENT_KO[el]}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct}%; background:{ELEMENT_COLOR[el]}"></div></div>'
            f'<div class="bar-count">{cnt}</div></div>'
        )

    daewoon_html = ""
    if daewoon:
        rows = []
        for d in daewoon["series"]:
            el = STEM_ELEMENT[d["stem"]][0]
            rows.append(
                f'<div class="dw-cell" style="border-color:{ELEMENT_COLOR[el]}">'
                f'<div class="dw-age">{d["start_age"]}~{d["end_age"]}</div>'
                f'<div class="dw-pillar">{d["pillar"]}</div></div>'
            )
        daewoon_html = (
            f'<section class="card"><h2>대운 흐름</h2>'
            f'<p class="meta">{daewoon["rule"]} · 대운수 {daewoon["daewoon_su"]}세</p>'
            f'<div class="dw-grid">{"".join(rows)}</div></section>'
        )

    shensha_html = ""
    if shensha:
        items = []
        for k, v in shensha.items():
            if isinstance(v, dict) and v.get("found_at"):
                items.append(f'<li><b>{k}</b> — {", ".join(v["found_at"])}</li>')
            elif isinstance(v, list):
                for it in v:
                    if "pos" in it:
                        items.append(f'<li><b>{k}</b> — {it["pos"]}({it["pillar"]})</li>')
                    else:
                        items.append(f'<li><b>{k}</b> — {it["found_at"]}</li>')
        if items:
            shensha_html = f'<section class="card"><h2>신살·귀인</h2><ul>{"".join(items)}</ul></section>'

    yongsin_html = ""
    if yongsin:
        cands = ", ".join(c["element_ko"] for c in yongsin["yongsin_candidates"]) or "—"
        gs = ", ".join(c["element_ko"] for c in yongsin["gisin_candidates"]) or "—"
        joh = ", ".join(yongsin["johoo_adjustment"]) or "—"
        yongsin_html = (
            f'<section class="card"><h2>용신·기신</h2>'
            f'<p>강약: <b>{yongsin["strength"]}</b> ({yongsin["self_ratio"]*100:.0f}%)</p>'
            f'<p>용신 후보: {cands}</p><p>조후 보정: {joh}</p><p>기신: {gs}</p></section>'
        )

    sub_time = ""
    if has_hour and inp.get('hour') is not None:
        sub_time = f" · {str(inp['hour']).zfill(2)}:{str(inp['minute']).zfill(2)}"

    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} 사주 — {birth}</title>
<style>
  body {{ margin: 0; font-family: -apple-system, "Noto Sans KR", "Inter", sans-serif;
         background: #F7F5F2; color: #1A1C1E; line-height: 1.6; }}
  .container {{ max-width: 720px; margin: 0 auto; padding: 24px 16px 64px; }}
  header {{ text-align: center; padding: 24px 0; }}
  header h1 {{ margin: 0; font-size: 28px; font-weight: 600; }}
  header .sub {{ color: #6C7278; font-size: 14px; margin-top: 4px; }}
  .badge {{ position: fixed; top: 56px; right: 16px; background: rgba(0,0,0,0.4);
            color: rgba(255,255,255,0.6); font-size: 11px; padding: 4px 10px;
            border-radius: 20px; pointer-events: none; z-index: 999; }}
  .card {{ background: white; border-radius: 16px; padding: 24px;
           box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 24px; }}
  .card h2 {{ margin: 0 0 16px 0; font-size: 18px; font-weight: 600;
              border-left: 4px solid #B8422E; padding-left: 12px; }}
  .meta {{ color: #6C7278; font-size: 13px; margin: 4px 0 16px; }}
  .pillars {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }}
  .pillar {{ text-align: center; }}
  .pillar.empty {{ opacity: 0.3; }}
  .plabel {{ font-size: 12px; color: #6C7278; margin-bottom: 6px; }}
  .pstem, .pbranch {{ font-size: 32px; font-weight: 600; color: white;
                      width: 56px; height: 56px; line-height: 56px;
                      margin: 4px auto; border-radius: 8px; font-family: serif; }}
  .pname {{ font-family: serif; font-weight: 600; margin-top: 6px; }}
  .day-master {{ background: linear-gradient(135deg, #1A1C1E, #345D7E);
                 color: white; padding: 16px; border-radius: 12px; text-align: center; }}
  .bar-row {{ display: grid; grid-template-columns: 60px 1fr 30px;
              align-items: center; gap: 8px; margin: 8px 0; }}
  .bar-label {{ font-size: 14px; }}
  .bar-track {{ height: 24px; background: #EFEDE8; border-radius: 12px; overflow: hidden; }}
  .bar-fill {{ height: 100%; transition: width 0.6s ease-out; }}
  .bar-count {{ text-align: right; font-family: "Inter", monospace; font-weight: 600; }}
  .dw-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }}
  .dw-cell {{ border: 2px solid #ccc; border-radius: 8px; padding: 12px; text-align: center; }}
  .dw-age {{ font-size: 12px; color: #6C7278; }}
  .dw-pillar {{ font-family: serif; font-size: 22px; font-weight: 600; }}
  ul {{ padding-left: 20px; }} ul li {{ margin: 4px 0; }}
  footer {{ text-align: center; color: #A8A29A; font-size: 11px; margin-top: 32px; }}
</style></head>
<body>
<div class="container">
  <header><h1>{name}의 사주 명식</h1><div class="sub">{birth}{sub_time}</div></header>
  <section class="card"><h2>사주 명식</h2>
    <div class="pillars">{"".join(pillar_cards)}</div>
    <div class="day-master" style="margin-top:24px">
      일주(나): <b style="font-family:serif; font-size:24px">{p["day_pillar"]}</b>
      — {dm["element"]} {dm["polarity"]}
    </div>
  </section>
  <section class="card"><h2>오행 분포</h2>
    {"".join(bars)}
    <p class="meta" style="margin-top:12px">최강: {fe["strongest"]} · 최약: {fe["weakest"]}</p>
  </section>
  {yongsin_html}{daewoon_html}{shensha_html}
  <footer>sajupy(MIT) 결정론 산출 + saju-agent 명리 모듈</footer>
</div></body></html>"""


def save_and_share(
    saju: Dict[str, Any], name: str = "익명",
    daewoon=None, shensha=None, yongsin=None,
    output_dir: str = "/tmp",
) -> Dict[str, Any]:
    html = render_html(saju, name=name, daewoon=daewoon, shensha=shensha, yongsin=yongsin)
    inp = saju["input"]
    birth = f"{inp['year']:04d}{inp['month']:02d}{inp['day']:02d}"
    fname = f"saju_{name}_{birth}.html"
    fpath = Path(output_dir) / fname
    fpath.write_text(html, encoding="utf-8")
    return {"local_path": str(fpath), "size_bytes": len(html)}


def _selftest() -> int:
    from saju.agent import calc
    from saju.daewoon import calc_daewoon
    from saju.shensha import find_shensha
    from saju.yongsin import derive_yongsin
    passed, total = 0, 0

    total += 1
    r = calc(year=1990, month=5, day=15, hour=14, minute=0,
             longitude=126.978, time_mode="approx")
    html = render_html(r, name="익명")
    assert "<!doctype html>" in html
    assert all(p in html for p in (r["pillars"]["year_pillar"],
                                    r["pillars"]["month_pillar"],
                                    r["pillars"]["day_pillar"]))
    print(f"  ✓ 기본 명식 ({len(html):,} bytes)")
    passed += 1

    total += 1
    dw = calc_daewoon(r, gender="M")
    sh = find_shensha(r)
    ys = derive_yongsin(r)
    html2 = render_html(r, name="익명", daewoon=dw, shensha=sh, yongsin=ys)
    assert "대운 흐름" in html2 and "용신·기신" in html2
    print(f"  ✓ 풀 패키지 ({len(html2):,} bytes)")
    passed += 1

    total += 1
    out = save_and_share(r, name="익명", output_dir="/tmp")
    assert Path(out["local_path"]).exists()
    print(f"  ✓ 저장: {out['local_path']}")
    passed += 1

    print(f"✅ selftest passed: {passed}/{total}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        sys.exit(_selftest())
    elif len(sys.argv) > 1 and sys.argv[1] == "demo":
        from saju.agent import calc
        from saju.daewoon import calc_daewoon
        from saju.shensha import find_shensha
        from saju.yongsin import derive_yongsin
        r = calc(year=1990, month=5, day=15, hour=14, minute=0,
                 longitude=126.978, time_mode="approx")
        out = save_and_share(
            r, name="익명",
            daewoon=calc_daewoon(r, "M"),
            shensha=find_shensha(r),
            yongsin=derive_yongsin(r),
        )
        print(out)
    else:
        print(__doc__)
