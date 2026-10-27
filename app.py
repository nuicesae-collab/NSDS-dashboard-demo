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
    st.caption(f"พื้นที่ที่กำลังดู: {area_label}")
    available_years = sorted(scoped["year_be"].unique().tolist())
    default_years = [year for year in YEARS if year in available_years]
    compare_years = st.multiselect("เปรียบเทียบปี พ.ศ.", available_years, default=default_years)
    trend_data = scoped[(scoped["disease"] == disease) & (scoped["year_be"].isin(compare_years))]
    if trend_data.empty:
        st.info("เลือกอย่างน้อยหนึ่งปีเพื่อแสดงแนวโน้ม")
    else:
        monthly = trend_data.groupby(["year_be", "month"], as_index=False)["cases"].sum()
        fig = px.line(monthly, x="month", y="cases", color="year_be", markers=True,
                      title=f"เปรียบเทียบ {disease}",
                      labels={"year_be": "ปี พ.ศ.", "cases": "จำนวนผู้ป่วยจำลอง (ราย)", "month": "เดือน"})
        fig.update_xaxes(tickmode="array", tickvals=list(range(1, 13)), ticktext=SHORT_MONTHS)
        fig.update_layout(margin=dict(l=10, r=10, t=55, b=10), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        pivot = monthly.pivot(index="month", columns="year_be", values="cases").reindex(range(1, 13)).reset_index()
        pivot.insert(1, "เดือน", pivot["month"].map(lambda m: SHORT_MONTHS[int(m) - 1]))
        pivot = pivot.drop(columns=["month"])
        st.subheader("ตารางเปรียบเทียบรายเดือน")
        st.dataframe(pivot, hide_index=True, use_container_width=True)
    st.info("กราฟใช้เพื่อศึกษาแนวโน้มของข้อมูลจำลอง ไม่สามารถใช้ยืนยันสาเหตุหรือทำนายการระบาดจริงได้")

# ---------------------------- ALERT SIMULATION ----------------------------
elif page == "จำลองระบบแจ้งเตือน":
    st.header("จำลองระบบแจ้งเตือน")
    st.write("ประเมินจำนวนผู้ป่วยของเดือนที่เลือกใน พ.ศ. 2569 เทียบกับค่าเฉลี่ยของเดือนเดียวกันใน พ.ศ. 2567–2568")
    available_months = sorted(scoped.loc[scoped["year_be"] == CURRENT_YEAR, "month"].unique().tolist())
    if not available_months:
        st.error("ไม่พบข้อมูลปี 2569 สำหรับพื้นที่นี้")
    else:
        latest_month = max(available_months)
        left, right = st.columns(2)
        with left:
            alert_month = st.selectbox("เดือนที่ต้องการประเมิน", available_months,
                                       index=available_months.index(latest_month),
                                       format_func=lambda m: MONTHS[int(m) - 1])
        with right:
            threshold = st.slider("เกณฑ์ ALERT (เท่าของค่าเฉลี่ยปีฐาน)", 1.1, 2.5, 1.5, 0.1)
        results = evaluate_month(scoped, int(alert_month), threshold)
        st.subheader("ผลประเมินทั้ง 6 โรค")
        st.dataframe(results, hide_index=True, use_container_width=True)
        alert_count = int((results["สถานะ"] == "ALERT").sum())
        watch_count = int((results["สถานะ"] == "WATCH").sum())
        normal_count = int((results["สถานะ"] == "NORMAL").sum())
        c1, c2, c3 = st.columns(3)
        c1.metric("ALERT", alert_count)
        c2.metric("WATCH", watch_count)
        c3.metric("NORMAL", normal_count)
        st.divider()
        st.subheader("สร้างข้อความแจ้งเตือนจำลอง")
        st.caption("ชื่อโรงพยาบาลเป็นชื่อสมมติสำหรับสาธิต และปุ่มนี้จะสร้างข้อความเท่านั้น ไม่ได้ส่ง SMS, LINE หรืออีเมลจริง")
        alert_disease = st.selectbox("โรคในข้อความแจ้งเตือน", DISEASES, index=DISEASES.index(disease), key="alert_disease")
        if selected_region:
            hospital_options = [f"โรงพยาบาลตัวอย่าง {letter} — {selected_region}" for letter in ["A", "B", "C"]]
        else:
            hospital_options = ["โรงพยาบาลตัวอย่าง A — ระดับประเทศ", "โรงพยาบาลตัวอย่าง B — ระดับประเทศ", "โรงพยาบาลตัวอย่าง C — ระดับประเทศ"]
        hospital = st.selectbox("โรงพยาบาลเป้าหมาย (ชื่อสมมติ)", hospital_options)
        recipients = st.multiselect("กลุ่มผู้รับแจ้งเตือน (จำลอง)", RECIPIENT_GROUPS, default=[RECIPIENT_GROUPS[0]])
        selected_row = results[results["โรค"] == alert_disease].iloc[0]
        st.markdown(f"**สถานะของ {alert_disease}:** `{selected_row['สถานะ']}`")
        st.caption(status_reason(str(selected_row["สถานะ"]), selected_row["เทียบฐาน (เท่า)"], threshold))
        if st.button("🔔 สร้างข้อความแจ้งเตือนจำลอง", type="primary", use_container_width=True):
            message = make_alert_message(area_label, hospital, recipients, alert_disease, int(alert_month), selected_row, threshold)
            st.session_state["last_alert_message"] = message
            st.session_state["alert_history"].insert(0, {
                "เวลา": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "พื้นที่": area_label,
                "โรงพยาบาล (สมมติ)": hospital,
                "โรค": alert_disease,
                "สถานะ": str(selected_row["สถานะ"]),
                "กลุ่มผู้รับ": ", ".join(recipients) if recipients else "ยังไม่ได้เลือก",
                "เทียบฐาน (เท่า)": selected_row["เทียบฐาน (เท่า)"],
                "ผลการส่ง": "สร้างข้อความจำลองเท่านั้น — ไม่ได้ส่งจริง",
            })
            st.success("สร้างข้อความจำลองแล้ว ยังไม่มีการส่งข้อความจริง")
        if st.session_state["last_alert_message"]:
            st.text_area("ข้อความแจ้งเตือนสำหรับคัดลอก", st.session_state["last_alert_message"], height=300)
            st.download_button("ดาวน์โหลดข้อความแจ้งเตือน (.txt)", st.session_state["last_alert_message"],
                               file_name="nsds_sample_alert.txt", mime="text/plain")
        if st.session_state["alert_history"]:
            st.subheader("ประวัติการสร้างข้อความในเซสชันนี้")
            st.dataframe(pd.DataFrame(st.session_state["alert_history"]), hide_index=True, use_container_width=True)
            st.caption("ประวัตินี้อยู่ในเซสชันที่เปิดอยู่เท่านั้น ไม่ใช่ฐานข้อมูลถาวร")
        with st.expander("เกณฑ์และข้อจำกัด"):
            st.markdown("""
- **ปีฐาน:** ค่าเฉลี่ยของเดือนเดียวกันใน พ.ศ. 2567 และ 2568
- **ALERT:** จำนวนจำลองปี 2569 ตั้งแต่เกณฑ์ที่ตั้งไว้ (ค่าเริ่มต้น 1.5 เท่า) ขึ้นไป
- **WATCH:** สูงกว่าค่าเฉลี่ยปีฐาน แต่ต่ำกว่าเกณฑ์ ALERT
- **NORMAL:** ไม่สูงกว่าค่าเฉลี่ยปีฐาน
- เกณฑ์นี้เป็นกติกาสาธิตของโปรเจกต์ ไม่ใช่เกณฑ์มาตรฐานที่รับรองโดยหน่วยงานสาธารณสุข
- ระบบยังไม่เชื่อมรายชื่อโรงพยาบาลจริงหรือช่องทางส่งข้อความจริง
""")

# ---------------------------- DATA / METHODS ----------------------------
else:
    st.header("ข้อมูลและวิธีใช้")
    st.markdown("""
**โรคในขอบเขต 6 โรค**
1. โรคมือเท้าปาก
2. โรคไข้เลือดออก
3. โรคปอดบวม
4. โรคไข้หวัดใหญ่
5. โรคลมแดด
6. โรคอุจจาระร่วงเฉียบพลัน

**วิธีใช้**
- เลือกระดับประเทศหรือเขตสุขภาพจากแถบด้านซ้าย
- เลือกโรคและปีเพื่อดูภาพรวม
- ใช้หน้า “วิเคราะห์แนวโน้ม” เพื่อเปรียบเทียบปี พ.ศ. 2567–2569
- ใช้หน้า “จำลองระบบแจ้งเตือน” เพื่อประเมินเกณฑ์ ทดลองเลือกโรงพยาบาลและกลุ่มผู้รับ แล้วสร้างข้อความตัวอย่าง

**วิธีประเมินการแจ้งเตือน**
- เปรียบเทียบจำนวนผู้ป่วยจำลองของเดือนเดียวกันใน พ.ศ. 2569 กับค่าเฉลี่ยเดือนเดียวกันของ พ.ศ. 2567–2568
- ค่าเริ่มต้น ALERT คือ 1.5 เท่าของค่าเฉลี่ยปีฐาน; WATCH คือสูงกว่าฐานแต่ต่ำกว่าเกณฑ์; NORMAL คือไม่สูงกว่าฐาน

**ข้อจำกัดที่ต้องระบุในรายงาน**
- ตัวเลขเป็นข้อมูลสังเคราะห์เพื่อสาธิต ไม่ใช่ข้อมูลผู้ป่วยจริง
- ยังไม่ได้เชื่อมแหล่งข้อมูลสาธารณสุขทางการที่ผ่านการตรวจสอบ
- เขตสุขภาพเป็นระดับพื้นที่จำลอง; ยังไม่ได้เชื่อมจังหวัดหรือโรงพยาบาลจริง
- ข้อความแจ้งเตือนเป็นการจำลองในแอป ไม่มีการส่งข้อความจริง และประวัติจะอยู่เฉพาะเซสชันปัจจุบัน
""")
    st.subheader("ตัวอย่างข้อมูลที่ระบบใช้")
    st.dataframe(df.head(30), hide_index=True, use_container_width=True)
    st.download_button("ดาวน์โหลดข้อมูลจำลองทั้งหมด (.csv)", df.to_csv(index=False).encode("utf-8-sig"),
                       file_name="disease_monthly_data_simulated.csv", mime="text/csv")
    st.info("ก่อนนำไปใช้จริง ต้องแทนข้อมูลสังเคราะห์ด้วยข้อมูลจากแหล่งทางการ พร้อมระบุ URL วันที่เข้าถึง และเงื่อนไขการใช้ข้อมูล")

st.divider()
        total_cases = int(disease_data["cases"].sum())
        latest_2026_month = int(df.loc[df["year_be"] == CURRENT_YEAR, "month"].max())
        alert_table = evaluate_month(scoped, latest_2026_month, 1.5)
        alert_count = int(alert_table["สถานะ"].isin(["ALERT", "WATCH"]).sum())
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("ผู้ป่วยสะสมจำลองของโรคที่เลือก", f"{total_cases:,} ราย")
        c2.metric(f"เดือนล่าสุด ({SHORT_MONTHS[latest_month - 1]})", f"{current_cases:,} ราย")
        c3.metric("เปลี่ยนจากเดือนก่อน", f"{change:+.1f}%", delta=f"{current_cases - previous_cases:+,} ราย")
        c4.metric("โรคที่อยู่ใน WATCH / ALERT", str(alert_count))
        st.subheader("แนวโน้มรายเดือน")
        trend = disease_data.groupby(["month", "month_name_th"], as_index=False)["cases"].sum().sort_values("month")
        fig = px.line(trend, x="month", y="cases", markers=True,
                      title=f"{disease} — พ.ศ. {selected_year}",
                      labels={"cases": "จำนวนผู้ป่วยจำลอง (ราย)", "month": "เดือน"})
        fig.update_xaxes(tickmode="array", tickvals=list(range(1, 13)), ticktext=SHORT_MONTHS)
        fig.update_layout(margin=dict(l=10, r=10, t=55, b=10), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        left, right = st.columns(2)
        with left:
            st.subheader("เปรียบเทียบโรคในพื้นที่")
            by_disease = scoped[scoped["year_be"] == selected_year].groupby("disease", as_index=False)["cases"].sum().sort_values("cases")
            fig_bar = px.bar(by_disease, x="cases", y="disease", orientation="h",
                             labels={"cases": "จำนวนผู้ป่วยจำลอง (ราย)", "disease": "โรค"})
            fig_bar.update_layout(margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_bar, use_container_width=True)
        with right:
            st.subheader(f"ผลประเมินจำลอง · {MONTHS[latest_2026_month - 1]} 2569")
            st.dataframe(alert_table, hide_index=True, use_container_width=True)

# ---------------------------- TRENDS ----------------------------
elif page == "วิเคราะห์แนวโน้ม":
    st.header("วิเคราะห์แนวโน้มโรค")
    st.caption(f"พื้นที่ที่กำลังดู: {area_label}")
    available_years = sorted(scoped["year_be"].unique().tolist())
    default_years = [year for year in YEARS if year in available_years]
    compare_years = st.multiselect("เปรียบเทียบปี พ.ศ.", available_years, default=default_years)
    trend_data = scoped[(scoped["disease"] == disease) & (scoped["year_be"].isin(compare_years))]
    if trend_data.empty:
        st.info("เลือกอย่างน้อยหนึ่งปีเพื่อแสดงแนวโน้ม")
    else:
        monthly = trend_data.groupby(["year_be", "month"], as_index=False)["cases"].sum()
        fig = px.line(monthly, x="month", y="cases", color="year_be", markers=True,
                      title=f"เปรียบเทียบ {disease}",
                      labels={"year_be": "ปี พ.ศ.", "cases": "จำนวนผู้ป่วยจำลอง (ราย)", "month": "เดือน"})
        fig.update_xaxes(tickmode="array", tickvals=list(range(1, 13)), ticktext=SHORT_MONTHS)
        fig.update_layout(margin=dict(l=10, r=10, t=55, b=10), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        pivot = monthly.pivot(index="month", columns="year_be", values="cases").reindex(range(1, 13)).reset_index()
        pivot.insert(1, "เดือน", pivot["month"].map(lambda m: SHORT_MONTHS[int(m) - 1]))
        pivot = pivot.drop(columns=["month"])
        st.subheader("ตารางเปรียบเทียบรายเดือน")
        st.dataframe(pivot, hide_index=True, use_container_width=True)
    st.info("กราฟใช้เพื่อศึกษาแนวโน้มของข้อมูลจำลอง ไม่สามารถใช้ยืนยันสาเหตุหรือทำนายการระบาดจริงได้")

# ---------------------------- ALERT SIMULATION ----------------------------
elif page == "จำลองระบบแจ้งเตือน":
    st.header("จำลองระบบแจ้งเตือน")
    st.write("ประเมินจำนวนผู้ป่วยของเดือนที่เลือกใน พ.ศ. 2569 เทียบกับค่าเฉลี่ยของเดือนเดียวกันใน พ.ศ. 2567–2568")
    available_months = sorted(scoped.loc[scoped["year_be"] == CURRENT_YEAR, "month"].unique().tolist())
    if not available_months:
        st.error("ไม่พบข้อมูลปี 2569 สำหรับพื้นที่นี้")
    else:
        latest_month = max(available_months)
        left, right = st.columns(2)
        with left:
            alert_month = st.selectbox("เดือนที่ต้องการประเมิน", available_months,
                                       index=available_months.index(latest_month),
                                       format_func=lambda m: MONTHS[int(m) - 1])
        with right:
            threshold = st.slider("เกณฑ์ ALERT (เท่าของค่าเฉลี่ยปีฐาน)", 1.1, 2.5, 1.5, 0.1)
        results = evaluate_month(scoped, int(alert_month), threshold)
        st.subheader("ผลประเมินทั้ง 6 โรค")
        st.dataframe(results, hide_index=True, use_container_width=True)
        alert_count = int((results["สถานะ"] == "ALERT").sum())
        watch_count = int((results["สถานะ"] == "WATCH").sum())
        normal_count = int((results["สถานะ"] == "NORMAL").sum())
        c1, c2, c3 = st.columns(3)
                c1.metric("ALERT", alert_count)
        c2.metric("WATCH", watch_count)
        c3.metric("NORMAL", normal_count)
        st.divider()
        st.subheader("สร้างข้อความแจ้งเตือนจำลอง")
        st.caption("ชื่อโรงพยาบาลเป็นชื่อสมมติสำหรับสาธิต และปุ่มนี้จะสร้างข้อความเท่านั้น ไม่ได้ส่ง SMS, LINE หรืออีเมลจริง")
        alert_disease = st.selectbox("โรคในข้อความแจ้งเตือน", DISEASES, index=DISEASES.index(disease), key="alert_disease")
        if selected_region:
            hospital_options = [f"โรงพยาบาลตัวอย่าง {letter} — {selected_region}" for letter in ["A", "B", "C"]]
        else:
            hospital_options = ["โรงพยาบาลตัวอย่าง A — ระดับประเทศ", "โรงพยาบาลตัวอย่าง B — ระดับประเทศ", "โรงพยาบาลตัวอย่าง C — ระดับประเทศ"]
        hospital = st.selectbox("โรงพยาบาลเป้าหมาย (ชื่อสมมติ)", hospital_options)
        recipients = st.multiselect("กลุ่มผู้รับแจ้งเตือน (จำลอง)", RECIPIENT_GROUPS, default=[RECIPIENT_GROUPS[0]])
        selected_row = results[results["โรค"] == alert_disease].iloc[0]
        st.markdown(f"**สถานะของ {alert_disease}:** `{selected_row['สถานะ']}`")
        st.caption(status_reason(str(selected_row["สถานะ"]), selected_row["เทียบฐาน (เท่า)"], threshold))
        if st.button("🔔 สร้างข้อความแจ้งเตือนจำลอง", type="primary", use_container_width=True):
            message = make_alert_message(area_label, hospital, recipients, alert_disease, int(alert_month), selected_row, threshold)
            st.session_state["last_alert_message"] = message
            st.session_state["alert_history"].insert(0, {
                "เวลา": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "พื้นที่": area_label,
                "โรงพยาบาล (สมมติ)": hospital,
                "โรค": alert_disease,
                "สถานะ": str(selected_row["สถานะ"]),
                "กลุ่มผู้รับ": ", ".join(recipients) if recipients else "ยังไม่ได้เลือก",
                "เทียบฐาน (เท่า)": selected_row["เทียบฐาน (เท่า)"],
                "ผลการส่ง": "สร้างข้อความจำลองเท่านั้น — ไม่ได้ส่งจริง",
            })
            st.success("สร้างข้อความจำลองแล้ว ยังไม่มีการส่งข้อความจริง")
        if st.session_state["last_alert_message"]:
            st.text_area("ข้อความแจ้งเตือนสำหรับคัดลอก", st.session_state["last_alert_message"], height=300)
            st.download_button("ดาวน์โหลดข้อความแจ้งเตือน (.txt)", st.session_state["last_alert_message"],
                               file_name="nsds_sample_alert.txt", mime="text/plain")
        if st.session_state["alert_history"]:
            st.subheader("ประวัติการสร้างข้อความในเซสชันนี้")
            st.dataframe(pd.DataFrame(st.session_state["alert_history"]), hide_index=True, use_container_width=True)
            st.caption("ประวัตินี้อยู่ในเซสชันที่เปิดอยู่เท่านั้น ไม่ใช่ฐานข้อมูลถาวร")
        with st.expander("เกณฑ์และข้อจำกัด"):
            st.markdown("""
- **ปีฐาน:** ค่าเฉลี่ยของเดือนเดียวกันใน พ.ศ. 2567 และ 2568
- **ALERT:** จำนวนจำลองปี 2569 ตั้งแต่เกณฑ์ที่ตั้งไว้ (ค่าเริ่มต้น 1.5 เท่า) ขึ้นไป
- **WATCH:** สูงกว่าค่าเฉลี่ยปีฐาน แต่ต่ำกว่าเกณฑ์ ALERT
- **NORMAL:** ไม่สูงกว่าค่าเฉลี่ยปีฐาน
- เกณฑ์นี้เป็นกติกาสาธิตของโปรเจกต์ ไม่ใช่เกณฑ์มาตรฐานที่รับรองโดยหน่วยงานสาธารณสุข
- ระบบยังไม่เชื่อมรายชื่อโรงพยาบาลจริงหรือช่องทางส่งข้อความจริง
""")

# ---------------------------- DATA / METHODS ----------------------------
else:
    st.header("ข้อมูลและวิธีใช้")
    st.markdown("""
**โรคในขอบเขต 6 โรค**
1. โรคมือเท้าปาก
2. โรคไข้เลือดออก
3. โรคปอดบวม
4. โรคไข้หวัดใหญ่
5. โรคลมแดด
6. โรคอุจจาระร่วงเฉียบพลัน

**วิธีใช้**
- เลือกระดับประเทศหรือเขตสุขภาพจากแถบด้านซ้าย
- เลือกโรคและปีเพื่อดูภาพรวม
- ใช้หน้า “วิเคราะห์แนวโน้ม” เพื่อเปรียบเทียบปี พ.ศ. 2567–2569
- ใช้หน้า “จำลองระบบแจ้งเตือน” เพื่อประเมินเกณฑ์ ทดลองเลือกโรงพยาบาลและกลุ่มผู้รับ แล้วสร้างข้อความตัวอย่าง

**วิธีประเมินการแจ้งเตือน**
- เปรียบเทียบจำนวนผู้ป่วยจำลองของเดือนเดียวกันใน พ.ศ. 2569 กับค่าเฉลี่ยเดือนเดียวกันของ พ.ศ. 2567–2568
- ค่าเริ่มต้น ALERT คือ 1.5 เท่าของค่าเฉลี่ยปีฐาน; WATCH คือสูงกว่าฐานแต่ต่ำกว่าเกณฑ์; NORMAL คือไม่สูงกว่าฐาน

**ข้อจำกัดที่ต้องระบุในรายงาน**
- ตัวเลขเป็นข้อมูลสังเคราะห์เพื่อสาธิต ไม่ใช่ข้อมูลผู้ป่วยจริง
- ยังไม่ได้เชื่อมแหล่งข้อมูลสาธารณสุขทางการที่ผ่านการตรวจสอบ
- เขตสุขภาพเป็นระดับพื้นที่จำลอง; ยังไม่ได้เชื่อมจังหวัดหรือโรงพยาบาลจริง
- ข้อความแจ้งเตือนเป็นการจำลองในแอป ไม่มีการส่งข้อความจริง และประวัติจะอยู่เฉพาะเซสชันปัจจุบัน
""")
    st.subheader("ตัวอย่างข้อมูลที่ระบบใช้")
    st.dataframe(df.head(30), hide_index=True, use_container_width=True)
    st.download_button("ดาวน์โหลดข้อมูลจำลองทั้งหมด (.csv)", df.to_csv(index=False).encode("utf-8-sig"),
                       file_name="disease_monthly_data_simulated.csv", mime="text/csv")
    st.info("ก่อนนำไปใช้จริง ต้องแทนข้อมูลสังเคราะห์ด้วยข้อมูลจากแหล่งทางการ พร้อมระบุ URL วันที่เข้าถึง และเงื่อนไขการใช้ข้อมูล")

st.divider()
