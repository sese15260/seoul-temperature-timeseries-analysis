# 서울 월평균 기온 시계열 분석

Open-Meteo Historical Weather API의 **ERA5 재분석** 일평균 2m 기온을 월평균으로 집계하여 2010~2024년 서울의 추세, 계절성, 이상 편차를 분석합니다. 관측소 실측 기온과는 다릅니다.

## 파일

- `analysis.py`: 자료 검증, 월별 집계, 분석 및 PNG 3개 생성
- `data/seoul_era5_daily_2010_2024.json`: 다운로드한 원본 API 응답(5,479일)
- `data/seoul_monthly_2010_2024.csv`: 스크립트로 생성한 월별 자료(180개월)
- `data/metrics.json`: 리포트 수치의 재현용 출력
- `images/`: 리포트에 포함된 그래프
- `REPORT.md`: 질문, 방법, 관찰과 해석, 결론

## 실행

Python 3.10 이상에서 프로젝트 루트에서 실행합니다.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python analysis.py
```

실행 후 `data/seoul_monthly_2010_2024.csv`, `data/metrics.json`, `images/01_annual_trend.png`부터 `03_anomaly_ma12.png`까지 다시 생성됩니다. 스크립트는 날짜 누락/중복과 결측값을 검사합니다.

## 자료 재수집

원본 JSON이 포함되어 있으므로 분석 재실행에는 인터넷이 필요 없습니다. 새로 받을 때는 다음 고정 URL의 응답을 `data/seoul_era5_daily_2010_2024.json`으로 저장합니다.

```text
https://archive-api.open-meteo.com/v1/archive?latitude=37.5665&longitude=126.9780&start_date=2010-01-01&end_date=2024-12-31&daily=temperature_2m_mean&timezone=Asia%2FSeoul&models=era5
```

요청 좌표는 서울 중심부(37.5665, 126.9780)이며 응답 격자는 37.5, 127.0입니다. API 데이터는 [Open-Meteo](https://open-meteo.com/en/docs/historical-weather-api) 제공이며 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)에 따라 출처, 라이선스 링크와 변경 사항을 표시합니다. 여기서는 일별 ERA5 격자 기온을 월평균·편차·그래프로 가공했습니다. Open-Meteo의 무료 API 이용 범위는 비상업 용도입니다. 재사용 시 [서비스 이용 조건](https://open-meteo.com/en/terms)을 확인하세요.
