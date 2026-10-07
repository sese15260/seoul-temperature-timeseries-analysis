"""Analyze Seoul ERA5 daily mean temperature (2010-2024)."""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplconfig"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


SOURCE = ROOT / "data" / "seoul_era5_daily_2010_2024.json"
OUT = ROOT / "images"


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    daily = pd.DataFrame(payload["daily"]).rename(columns={"time": "date", "temperature_2m_mean": "temp_c"})
    daily["date"] = pd.to_datetime(daily["date"], errors="raise")
    daily["temp_c"] = pd.to_numeric(daily["temp_c"], errors="coerce")
    daily = daily.sort_values("date").set_index("date")
    expected = pd.date_range("2010-01-01", "2024-12-31", freq="D")
    assert daily.index.is_unique and daily.index.equals(expected), "Missing/duplicate dates"
    missing = int(daily["temp_c"].isna().sum())
    assert missing == 0, f"Missing temperatures: {missing}"
    # A broad physical plausibility screen catches broken units/sentinel values.
    assert daily["temp_c"].between(-40, 45).all(), "Implausible daily temperature"
    # Retain all plausible extremes: they may be real weather.
    monthly = daily["temp_c"].resample("MS").mean().to_frame("temp_c")
    assert len(monthly) == 180
    monthly["month"] = monthly.index.month
    monthly["year"] = monthly.index.year
    monthly["climatology_c"] = monthly.groupby("month")["temp_c"].transform("mean")
    monthly["anomaly_c"] = monthly["temp_c"] - monthly["climatology_c"]
    monthly["ma12_c"] = monthly["temp_c"].rolling(12).mean()
    monthly["anomaly_ma12_c"] = monthly["anomaly_c"].rolling(12).mean()
    return daily, monthly, payload


def save_plots(daily: pd.DataFrame, monthly: pd.DataFrame) -> None:
    OUT.mkdir(exist_ok=True)
    plt.rcParams.update({"figure.dpi": 140, "savefig.dpi": 140, "font.size": 10})
    # 1. Overall trend: annual averages avoid hiding long-term changes in seasons.
    annual = daily["temp_c"].resample("YS").mean()
    fig, ax = plt.subplots(figsize=(11, 4.4))
    ax.plot(annual.index.year, annual, marker="o", color="#176b87", label="Annual mean")
    coeff = np.polyfit(annual.index.year.to_numpy(), annual.to_numpy(), 1)
    ax.plot(annual.index.year, np.polyval(coeff, annual.index.year), "--", color="#d1603d", label="Linear fit")
    ax.set(title="Seoul ERA5: annual mean temperature, 2010-2024", xlabel="Year", ylabel="Temperature (°C)")
    ax.grid(alpha=.25); ax.legend(); fig.tight_layout()
    fig.savefig(OUT / "01_annual_trend.png"); plt.close(fig)

    # 2. Mean seasonal cycle, with min/max month-average across the 15 years.
    by_month = monthly.groupby("month")["temp_c"]
    fig, ax = plt.subplots(figsize=(10, 4.4))
    x = np.arange(1, 13)
    ax.fill_between(x, by_month.min(), by_month.max(), color="#aacde1", alpha=.55, label="Range of monthly means")
    ax.plot(x, by_month.mean(), marker="o", color="#176b87", label="2010-2024 mean")
    ax.set(title="Seoul ERA5: seasonal temperature cycle", xlabel="Month", ylabel="Temperature (°C)", xticks=x)
    ax.grid(alpha=.25); ax.legend(); fig.tight_layout()
    fig.savefig(OUT / "02_seasonality.png"); plt.close(fig)

    # 3. Deseasonalized monthly anomalies and 12-month rolling average.
    fig, ax = plt.subplots(figsize=(11, 4.4))
    ax.bar(monthly.index, monthly["anomaly_c"], width=23, color=np.where(monthly["anomaly_c"] >= 0, "#d1603d", "#3686b4"), alpha=.65)
    ax.plot(monthly.index, monthly["anomaly_ma12_c"], color="#222222", linewidth=2, label="12-month moving average")
    ax.axhline(0, color="#444444", linewidth=.8)
    ax.set(title="Seoul ERA5: monthly anomalies vs 2010-2024 month baseline", xlabel="Year", ylabel="Anomaly (°C)")
    ax.grid(axis="y", alpha=.25); ax.legend(); fig.tight_layout()
    fig.savefig(OUT / "03_anomaly_ma12.png"); plt.close(fig)


def main() -> None:
    daily, monthly, payload = load_data()
    save_plots(daily, monthly)
    annual = daily["temp_c"].resample("YS").mean()
    slope = float(np.polyfit(annual.index.year.to_numpy(), annual.to_numpy(), 1)[0])
    first5 = float(annual.iloc[:5].mean())
    last5 = float(annual.iloc[-5:].mean())
    monthly.to_csv(ROOT / "data" / "seoul_monthly_2010_2024.csv", float_format="%.4f", index_label="date")
    metrics = {
        "daily_points": len(daily), "monthly_points": len(monthly),
        "missing_daily": int(daily["temp_c"].isna().sum()),
        "first_year_mean": round(float(annual.iloc[0]), 2), "last_year_mean": round(float(annual.iloc[-1]), 2),
        "first5_mean": round(first5, 2), "last5_mean": round(last5, 2),
        "last5_minus_first5": round(last5 - first5, 2),
        "linear_slope_c_per_decade": round(slope * 10, 2),
        "warmest_year": int(annual.idxmax().year), "warmest_year_c": round(float(annual.max()), 2),
        "coldest_year": int(annual.idxmin().year), "coldest_year_c": round(float(annual.min()), 2),
        "coldest_climatology_month": int(monthly.groupby("month")["temp_c"].mean().idxmin()),
        "coldest_climatology_c": round(float(monthly.groupby("month")["temp_c"].mean().min()), 2),
        "warmest_climatology_month": int(monthly.groupby("month")["temp_c"].mean().idxmax()),
        "warmest_climatology_c": round(float(monthly.groupby("month")["temp_c"].mean().max()), 2),
        "max_anomaly_month": monthly["anomaly_c"].idxmax().strftime("%Y-%m"),
        "max_anomaly_c": round(float(monthly["anomaly_c"].max()), 2),
        "min_anomaly_month": monthly["anomaly_c"].idxmin().strftime("%Y-%m"),
        "min_anomaly_c": round(float(monthly["anomaly_c"].min()), 2),
        "api_grid_latitude": payload["latitude"], "api_grid_longitude": payload["longitude"],
    }
    (ROOT / "data" / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
