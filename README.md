<p align="center"><a href="https://hsc-class02.github.io/csh_sam/"><img alt="대시보드 바로가기" src="https://img.shields.io/badge/%F0%9F%94%97%20%EB%8C%80%EC%8B%9C%EB%B3%B4%EB%93%9C-%EB%B0%94%EB%A1%9C%EA%B0%80%EA%B8%B0-2458d3?style=for-the-badge"></a></p>

# 삼성전자 재무 데이터 분석

OpenDART에서 삼성전자(005930, corp_code `00126380`)의 재무제표를 수집하고 재무지표·차트·기간별 테이블을 GitHub Pages 대시보드로 제공합니다.

## 대시보드
**[🔗 대시보드 바로가기](https://hsc-class02.github.io/csh_sam/)**

## 기능
- 2015년 이후 사업보고서·반기보고서·분기보고서 수집
- 연결재무제표 우선 조회, 필요한 경우 별도재무제표 활용
- 매출액, 영업이익, 순이익, 자산, 부채, 자본, 영업현금흐름 및 유형자산 취득 추적
- Annual, Half-year, Quarterly 테이블과 재무분석 차트
- 매월 1일 자동 수집 및 GitHub Pages 자동 배포

## 최초 설정
1. Settings → Secrets and variables → Actions에서 Repository secret `DART_API_KEY`를 생성하고 OpenDART 인증키를 저장합니다. `OPENDART_API_KEY`도 지원합니다.
2. Settings → Pages → Build and deployment에서 Source를 **GitHub Actions**로 설정합니다.
3. Actions → **Update and deploy Samsung Electronics dashboard** → Run workflow를 실행합니다.

## 데이터 주의
- 출처: 금융감독원 OpenDART. 금액은 원 단위로 수집하고 대시보드에서 조 원으로 표시합니다.
- 보고서별 계정명 차이로 자동 매칭되지 않은 값은 0으로 대체하지 않고 — 로 표시합니다.
- 반기·분기 보고서의 당기 금액은 누계/분기 표시 차이가 있을 수 있으므로 공시 원문을 확인하세요.
- 본 대시보드는 정보 제공 목적이며 투자 권유가 아닙니다.

## 국내 Peer Firms
| 기업 | 종목코드 | 주요 비교 영역 | 비교 시 유의점 |
|---|---:|---|---|
| SK하이닉스 | 000660 | 메모리 반도체, HBM | 메모리 집중도가 높음 |
| LG전자 | 066570 | 가전, 전장, 전자제품 | 사업 포트폴리오가 다름 |
| 삼성전기 | 009150 | 전자부품, 패키지 기판 | 부품 중심 기업 |
| DB하이텍 | 000990 | 파운드리, 아날로그 반도체 | 특화 파운드리 중심 |

## 파일 구성
- `dashboard/data.json`: 대시보드 데이터
- `data/processed/latest.json`: 처리된 데이터 보관본
- `scripts/update.py`: OpenDART 수집 및 분석
- `.github/workflows/update-and-deploy.yml`: 월간 자동화 및 배포
