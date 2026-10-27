from pathlib import Path
from datetime import datetime
import math
import random
import pandas as pd
import plotly.express as px
import streamlit as st

# NSDS Dashboard — academic prototype using synthetic data only.
st.set_page_config(page_title="NSDS Dashboard", page_icon="🩺", layout="wide")

DATA = Path(__file__).parent / "data" / "disease_monthly_data_simulated.csv"
YEARS = [2567, 2568, 2569]
CURRENT_YEAR = 2569
DISEASES = [
    "โรคมือเท้าปาก",
    "โรคไข้เลือดออก",
    "โรคปอดบวม",
    "โรคไข้หวัดใหญ่",
    "โรคลมแดด",
    "โรคอุจจาระร่วงเฉียบพลัน",
]
MONTHS = [
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]
SHORT_MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
REGIONS = [f"เขตสุขภาพที่ {i}" for i in range(1, 14)]
RECIPIENT_GROUPS = [
    "ทีมเฝ้าระวังโรค / ระบาดวิทยา",
    "ทีมควบคุมการติดเชื้อ (IC)",
    "ผู้บริหารโรงพยาบาล",
    "ทีมเวชระเบียน / ข้อมูล",
]


def build_demo_data() -> pd.DataFrame:
    """Create repeatable synthetic data with 13 regions and six agreed diseases."""
    rng = random.Random(269)
    # Baseline monthly cases per region; these are illustrative parameters, not real statistics.
    disease_base = {
        "โรคมือเท้าปาก": 48,
        "โรคไข้เลือดออก": 72,
        "โรคปอดบวม": 95,
        "โรคไข้หวัดใหญ่": 112,
        "โรคลมแดด": 16,
        "โรคอุจจาระร่วงเฉียบพลัน": 88,
    }
    seasonal = {
        "โรคมือเท้าปาก": [0.82, 0.84, 0.90, 0.98, 1.06, 1.18, 1.28, 1.24, 1.08, 0.98, 0.90, 0.84],
        "โรคไข้เลือดออก": [0.62, 0.68, 0.78, 0.94, 1.08, 1.24, 1.40, 1.36, 1.20, 1.00, 0.80, 0.68],
        "โรคปอดบวม": [1.22, 1.17, 1.10, 1.02, 0.96, 0.91, 0.90, 0.91, 0.96, 1.02, 1.12, 1.20],
        "โรคไข้หวัดใหญ่": [1.28, 1.22, 1.10, 0.96, 0.86, 0.81, 0.82, 0.87, 0.98, 1.12, 1.25, 1.31],
        "โรคลมแดด": [0.22, 0.30, 0.65, 1.28, 1.48, 1.32, 0.96, 0.72, 0.50, 0.32, 0.23, 0.20],
        "โรคอุจจาระร่วงเฉียบพลัน": [0.90, 0.91, 0.98, 1.12, 1.18, 1.13, 1.06, 1.02, 1.00, 0.98, 0.94, 0.91],
    }
    year_factor = {2567: 1.00, 2568: 1.035, 2569: 1.07}
    # Stable differences between regions make regional comparisons meaningful in the demo.
    region_factor = {region: 0.72 + (idx * 0.045) for idx, region in enumerate(REGIONS)}
    rows = []
    for year in YEARS:
        last_month = 10 if year == CURRENT_YEAR else 12
        for month in range(1, last_month + 1):
            for disease in DISEASES:
                for region_index, region in enumerate(REGIONS, start=1):
                    noise = rng.uniform(0.84, 1.18)
                    cases = int(
                        disease_base[disease]
                        * seasonal[disease][month - 1]
                        * year_factor[year]
                        * region_factor[region]
                        * noise
                    )
                    test_spike = False
                    # Deliberate spikes solely to demonstrate the alert workflow.
                    if year == CURRENT_YEAR and month in (7, 8) and region_index in (4, 7) and disease in ("โรคไข้เลือดออก", "โรคมือเท้าปาก"):
                        cases = int(cases * (2.25 if month == 7 else 2.45))
                        test_spike = True
                    if year == CURRENT_YEAR and month == 9 and region_index in (2, 10) and disease == "โรคไข้หวัดใหญ่":
                        cases = int(cases * 1.95)
                        test_spike = True
                    rows.append({
                        "year_be": year,
                        "month": month,
                        "month_name_th": MONTHS[month - 1],
                        "disease": disease,
                        "health_region": region,
                        "cases": max(0, cases),
                        "data_status": "simulated",
                        "source_note": "ข้อมูลสังเคราะห์เพื่อสาธิตเท่านั้น ไม่ใช่ข้อมูลผู้ป่วยจริง",
                        "is_test_spike": test_spike,
                    })
    return pd.DataFrame(rows)


def load_data() -> pd.DataFrame:
