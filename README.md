# saju-agent

사주(四柱) 8글자 결정론 계산 + 명리학 모듈(대운·신살·용신·궁합) + HTML 대시보드 + LLM 풀이 프롬프트.

> **Disclaimer.** 이 패키지는 명리학을 학문·문화·재미의 영역에서 다루기 위한 도구다.
> 의료·법률·재무·인생사의 결정 근거로 사용하지 말 것. 결정론 계산 부분은 검증되었지만,
> 풀이는 본질적으로 해석 영역이며 보장되지 않는다.

---

## 무엇이 들어 있나

```
saju-agent/
├── saju/                       # ← Python 패키지 (결정론 계산)
│   ├── agent.py                #   8글자·음양오행·십신·12운성
│   ├── daewoon.py              #   대운 (10년 단위 흐름)
│   ├── shensha.py              #   신살·귀인 (천을귀인·도화·역마·양인 등)
│   ├── yongsin.py              #   용신·기신 (단순화 억부+조후)
│   ├── compatibility.py        #   궁합 분석 (천간합·지지합·일간상생)
│   └── html.py                 #   모바일 호환 HTML 대시보드 생성
├── prompts/사주.md             # ← LLM(Claude 등)용 풀이 프롬프트 (요약/중간/풀 13단계)
└── examples/basic_usage.py     # ← 최소 사용 예제
```

**계산 엔진**은 [sajupy](https://pypi.org/project/sajupy/) 0.2.0(MIT) 위에 얹은
clean-room 명리학 모듈이다. 8글자(연·월·일·시 천간지지)는 sajupy가 결정론적으로
산출하고, 그 위의 십신·12운성·대운·신살·용신·궁합은 공개 명리학 공식으로
직접 구현했다.

**풀이 엔진**은 Claude/ChatGPT 같은 LLM이다. `prompts/사주.md`는 '대만신'
페르소나 프롬프트로, 결정론 출력값을 입력받아 자연어 풀이를 생성한다.
**풀이 길이 3단** — 요약(한 페이지) / 중간(5~7개 핵심) / 풀(13단계 인터랙티브)
중 사용자가 선택. (Claude Code에서는 `~/.claude/commands/사주.md`로 슬래시 커맨드화.)

---

## 빠른 시작

```bash
git clone https://github.com/alice840126-ship-it/saju-agent.git
cd saju-agent
pip install -r requirements.txt
python3 examples/basic_usage.py
```

코드 사용:

```python
from saju import calc, calc_daewoon, find_shensha, derive_yongsin, save_and_share

result = calc(
    year=1990, month=5, day=15,
    hour=14, minute=0,
    longitude=126.978,      # 서울 동경 (중국 기준 자오선 보정용)
    time_mode="approx",     # 정확 출생시간 모를 때 'unknown'
    is_lunar=False,         # 음력이면 True
)

print(result["pillars"]["day_pillar"])  # 庚辰 (일주)
print(result["day_master"])             # {'stem': '庚', 'element': '金', ...}

# 대운 (성별 필요)
dw = calc_daewoon(result, gender="M")

# 신살·용신
sh = find_shensha(result)
ys = derive_yongsin(result)

# HTML 대시보드 저장
out = save_and_share(result, name="홍길동",
                     daewoon=dw, shensha=sh, yongsin=ys,
                     output_dir="/tmp")
```

---

## LLM 풀이와 함께 쓰기

`prompts/사주.md`를 Claude 또는 ChatGPT에 시스템 프롬프트로 넣고, 결정론 결과를
입력으로 전달하면 자연어 풀이가 나온다. **길이는 3단 중 선택:**

- **요약 / 짧게** — 한 페이지 압축. 약 2,000자. 인터랙티브 없이 한 번에 출력.
- **중간** — 5~7개 핵심 항목. 약 8,000자. "다음" 5~7번.
- **풀 / 13단계** — 13단계 인터랙티브 풀이. 약 50,000자. 총평 → 핵심성정 →
  진로·재물 → 인간관계 → 혼인·자녀 → 건강 → 대운 흐름 → 권고.

Claude Code 사용자는 이 레포를 클론한 뒤 `prompts/사주.md`를
`~/.claude/commands/사주.md`로 복사하면 `/사주` 슬래시 커맨드로 바로 쓸 수 있다.

---

## 검증

각 모듈에 selftest가 들어 있다.

```bash
python3 -m saju.agent selftest          # 9/9
python3 -m saju.daewoon selftest        # 6/6
python3 -m saju.shensha selftest        # 5/5
python3 -m saju.yongsin selftest        # 4/4
python3 -m saju.compatibility selftest  # 4/4
python3 -m saju.html selftest           # 3/3
# 합계 31/31
```

8글자 계산은 sajupy가 보장한다. 십신·12운성·대운·신살은 공개 명리학 공식 그대로다.
용신은 **단순화 억부+조후 모델**이며 풀이 시 LLM 보강이 필요하다 (통근/투출/합충 미반영).

샘플 명식과 외부 만세력 비교: <https://manse.fortuneteller.kr/>

---

## License

MIT — `LICENSE` 참조.

계산 엔진 의존성:
- [sajupy](https://pypi.org/project/sajupy/) (MIT) — 8글자 결정론 산출
