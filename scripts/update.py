from __future__ import annotations
import json, os, time
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dashboard" / "data.json"
CORP_CODE = "00126380"  # Samsung Electronics Co., Ltd.
API_KEY = os.getenv("DART_API_KEY") or os.getenv("OPENDART_API_KEY")
BASE = "https://opendart.fss.or.kr/api"
REPORTS = [
    ("annual", "11011", "사업보고서"),
    ("half_year", "11012", "반기보고서"),
    ("quarterly", "11013", "1분기보고서"),
    ("quarterly", "11014", "3분기보고서"),
]
ALIASES = {
    "revenue": ["매출액", "수익(매출액)", "영업수익"],
    "operating_income": ["영업이익", "영업이익(손실)"],
    "net_income": ["당기순이익", "당기순이익(손실)", "분기순이익", "분기순이익(손실)"],
    "assets": ["자산총계"],
    "liabilities": ["부채총계"],
    "equity": ["자본총계"],
    "operating_cash_flow": ["영업활동현금흐름"],
    "capex": ["유형자산의 취득", "유형자산 취득"],
}
def api(path, params, retries=3):
    if not API_KEY:
        raise RuntimeError("DART_API_KEY 또는 OPENDART_API_KEY secret을 설정하세요.")
    p = dict(params, crtfc_key=API_KEY)
    last = None
    for n in range(retries):
        try:
            r = requests.get(f"{BASE}/{path}", params=p, timeout=25)
            r.raise_for_status()
            data = r.json()
            if data.get("status") not in ("000", "013"):
                if data.get("status") == "013":
                    return []
                raise RuntimeError(f"DART {data.get('status')}: {data.get('message')}")
            return data.get("list", [])
        except Exception as e:
            last = e
            if n < retries - 1: time.sleep(1.5 * (n + 1))
    raise last
def number(value):
    if value is None: return None
    s = str(value).replace(",", "").strip()
    if not s or s in ("-", "–"): return None
    try: return int(float(s))
    except ValueError: return None
def pick(rows, aliases, fs_div="CFS"):
    # Prefer consolidated statements; use separate statements only if CFS is unavailable.
    for div in ([fs_div, "OFS"] if fs_div == "CFS" else [fs_div]):
        candidates = [r for r in rows if r.get("fs_div") == div]
        for alias in aliases:
            exact = [r for r in candidates if r.get("account_nm", "").strip() == alias]
            if exact:
                for r in exact:
                    val = number(r.get("thstrm_amount"))
                    if val is not None: return val, div, r.get("account_nm")
    return None, None, None
def fetch_period(job):
    year, category, code, name = job
    rows = api("fnlttSinglAcntAll.json", {
        "corp_code": CORP_CODE, "bsns_year": str(year), "reprt_code": code, "fs_div": "CFS"
    })
    if not rows: return category, None
    values, bases, account_names = {}, {}, {}
    for key, aliases in ALIASES.items():
        val, div, account = pick(rows, aliases)
        values[key] = val
        if div: bases[key] = div
        if account: account_names[key] = account
    # Drop truly empty responses rather than publishing a fabricated zero row.
    if not any(v is not None for v in values.values()): return category, None
    return category, {
        "year": year, "report_code": code, "report_name": name,
        "period_name": f"{year}년 {name}", "financial_basis": "연결 우선" if all(v == "CFS" for v in bases.values()) else "연결/별도 확인",
        "values": values, "source_divisions": bases, "source_accounts": account_names
    }
def main():
    if not API_KEY:
        raise RuntimeError("DART_API_KEY 또는 OPENDART_API_KEY repository secret이 필요합니다. README의 최초 설정을 완료한 뒤 재실행하세요.")
    now = datetime.now(timezone.utc)
    current_year = now.year
    jobs = []
    for year in range(2015, current_year + 1):
        for category, code, name in REPORTS:
            # A report is only expected after its reporting period closes.
            if year == current_year:
                month = now.month
                if code == "11011" or (code == "11012" and month < 8) or (code == "11013" and month < 5) or (code == "11014" and month < 11):
                    continue
            jobs.append((year, category, code, name))
    annual, half, quarterly, warnings = [], [], [], []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(fetch_period, job): job for job in jobs}
        for f in as_completed(futures):
            job = futures[f]
            try:
                category, row = f.result()
                if not row:
                    continue
                (annual if category == "annual" else half if category == "half_year" else quarterly).append(row)
                print(f"[OK] {row['period_name']}")
            except Exception as e:
                msg = f"{job[0]} {job[3]}: {e}"
                warnings.append(msg)
                print(f"[WARN] {msg}")
    annual.sort(key=lambda x: x["year"])
    half.sort(key=lambda x: x["year"])
    quarterly.sort(key=lambda x: (x["year"], x["report_code"]))
    if not annual and not half and not quarterly:
        raise RuntimeError("재무자료를 수집하지 못했습니다. API key, GitHub secret 및 OpenDART 응답을 확인하세요.")
    payload = {
        "company": {"name": "삼성전자", "name_en": "Samsung Electronics Co., Ltd.", "stock_code": "005930", "corp_code": CORP_CODE},
        "updated_at": now.isoformat(),
        "currency": "KRW", "unit": "원",
        "methodology": "OpenDART 단일회사 전체 재무제표 API. 연결재무제표(CFS)를 우선하고 필요한 경우 별도재무제표(OFS)를 사용합니다. 원자료 금액은 원 단위이며 대시보드에서 조 단위로 표시합니다.",
        "periods": {"annual": annual, "half_year": half, "quarterly": quarterly},
        "collection": {"annual_count": len(annual), "half_year_count": len(half), "quarterly_count": len(quarterly), "warnings": warnings}
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "processed" / "latest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {OUT}; annual={len(annual)}, half-year={len(half)}, quarterly={len(quarterly)}, warnings={len(warnings)}")
if __name__ == "__main__":
    main()
