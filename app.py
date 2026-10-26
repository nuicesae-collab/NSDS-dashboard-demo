import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="NSDS | ระบบเฝ้าระวังโรค", page_icon="🏥", layout="wide")
ROOT = Path(__file__).parent
DATA_FILE = ROOT / "data" / "disease_monthly_data_simulated.csv"
MONTHS = ["มกราคม","กุมภาพันธ์","มีนาคม","เมษายน","พฤษภาคม","มิถุนายน","กรกฎาคม","สิงหาคม","กันยายน","ตุลาคม","พฤศจิกายน","ธันวาคม"]
SHORT_MONTHS = ["ม.ค.","ก.พ.","มี.ค.","เม.ย.","พ.ค.","มิ.ย.","ก.ค.","ส.ค.","ก.ย.","ต.ค.","พ.ย.","ธ.ค."]
OFFICIAL_SOURCES = [
    ("DOE Data Warehouse – สถานการณ์โรคติดต่อรายเดือน", "https://doe.moph.go.th/app01/?page_id=1049", "ใช้ค้นหารายงานโรคและข้อมูลรายเดือนที่เกี่ยวข้อง; ตรวจนิยามและช่วงเวลารายงานก่อนใช้"),
    ("คลังข้อมูลเปิด กรมควบคุมโรค", "https://ddcopendata.ddc.moph.go.th/", "ค้นหาชุดข้อมูลที่ดาวน์โหลดได้; ตรวจพื้นที่ ความถี่ และนิยามของแต่ละชุด"),
    ("Digital Disease Surveillance (DDS)", "https://ddsdoe.ddc.moph.go.th/dds-portal/", "แหล่งอ้างอิงระบบเฝ้าระวัง; การเข้าถึงข้อมูลอาจมีข้อจำกัด"),
    ("กรมควบคุมโรค", "https://ddc.moph.go.th/", "ค้นหารายงานสถานการณ์และคำแนะนำทางการของแต่ละโรค"),
]

st.markdown("""
<style>
.block-container {padding-top:1.4rem; padding-bottom:2rem;}
h1,h2,h3 {letter-spacing:-0.02em;}
div[data-testid="stMetric"] {background:#f6f8fb; border:1px solid #e4e9f0; padding:14px 16px; border-radius:14px;}
div[data-testid="stMetricLabel"] p {font-size:0.88rem;}
.small-note {color:#65748b;font-size:0.88rem;}
.alert-box {padding:16px 18px;border-radius:12px;border:1px solid #e2e8f0;margin:8px 0 16px 0;}
</style>
""", unsafe_allow_html=True)

st.title("🏥 National Seasonal Disease Surveillance")
st.caption("ระบบต้นแบบวิเคราะห์แนวโน้มและจำลองการแจ้งเตือนโรค")

if "alert_history" not in st.session_state:
    st.session_state.alert_history = []
if "uploaded_df" not in st.session_state:
    st.session_state.uploaded_df = None

def normalize_df(raw):
    df = raw.copy()
    # Accept common English column names or a few Thai names.
    aliases = {
        "โรค":"disease", "ปี":"year_be", "ปี พ.ศ.":"year_be", "เดือน":"month",
        "จำนวนผู้ป่วย":"cases", "ผู้ป่วย":"cases", "สถานะข้อมูล":"data_status",
        "แหล่งอ้างอิง":"source_url"
    }
    df = df.rename(columns={c: aliases.get(c, c) for c in df.columns})
    required = ["disease","year_be","month","cases"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError("ไฟล์ต้องมีคอลัมน์ disease, year_be, month, cases (หรือชื่อภาษาไทยที่เทียบเท่า)")
    df["year_be"] = pd.to_numeric(df["year_be"], errors="coerce")
    df["month"] = pd.to_numeric(df["month"], errors="coerce")
    df["cases"] = pd.to_numeric(df["cases"], errors="coerce")
    df = df.dropna(subset=["disease","year_be","month","cases"]).copy()
    df["year_be"] = df["year_be"].astype(int)
    df["month"] = df["month"].astype(int)
    df = df[df["month"].between(1,12) & (df["cases"] >= 0)]
    if "month_name_th" not in df:
        df["month_name_th"] = df["month"].map(lambda m: MONTHS[m-1])
    if "data_status" not in df:
        df["data_status"] = "unverified"
    if "source_url" not in df:
        df["source_url"] = ""
    if "source_note" not in df:
        df["source_note"] = ""
    return df

try:
    default_df = normalize_df(pd.read_csv(DATA_FILE))
except Exception:
    default_df = pd.DataFrame(columns=["disease","year_be","month","month_name_th","cases","data_status","source_url","source_note"])

with st.sidebar:
    st.header("เมนูระบบ")
    page = st.radio("ไปยังหน้า", ["Dashboard","วิเคราะห์แนวโน้ม","ศูนย์แจ้งเตือน","จัดการข้อมูล","วิธีวิเคราะห์และอ้างอิง"])
    st.divider()
    st.markdown("**สถานะชุดข้อมูล**")
    if st.session_state.uploaded_df is not None:
        st.success("ใช้ข้อมูลที่นำเข้าในเซสชันนี้")
    else:
        st.warning("ใช้ข้อมูลจำลอง")
    st.caption("ข้อมูลจำลองใช้สาธิตเท่านั้น ไม่ใช่ข้อมูลผู้ป่วยจริง")

df = st.session_state.uploaded_df if st.session_state.uploaded_df is not None else default_df
df = normalize_df(df) if len(df) else df

st.error("โหมดต้นแบบ: ข้อมูลเริ่มต้นเป็นข้อมูลสังเคราะห์ทั้งหมด ไม่ใช่สถิติผู้ป่วยจริง และไม่มีการส่งแจ้งเตือนไปยังโรงพยาบาลจริง")

# Baseline / alert helper
def make_assessment(data, disease, month, year=2569, threshold=1.5):
    base = data[(data["disease"]==disease)&(data["year_be"].isin([2567,2568]))&(data["month"]==month)]
    cur = data[(data["disease"]==disease)&(data["year_be"]==year)&(data["month"]==month)]
    if len(base) < 2 or cur.empty:
        return None
    baseline = float(base["cases"].mean())
    cases = float(cur.iloc[0]["cases"])
    ratio = cases / baseline if baseline > 0 else np.nan
    status = "ALERT" if ratio >= threshold else ("WATCH" if ratio > 1 else "NORMAL")
    return {"baseline":baseline,"cases":cases,"ratio":ratio,"status":status}

if page == "Dashboard":
    st.subheader("ภาพรวมสถานการณ์")
    if df.empty:
        st.warning("ยังไม่มีข้อมูลให้แสดง กรุณานำเข้า CSV ในเมนูจัดการข้อมูล")
        st.stop()
    disease_list = sorted(df["disease"].dropna().unique().tolist())
    c1,c2,c3 = st.columns(3)
    c1.metric("จำนวนโรคในชุดข้อมูล", len(disease_list))
    c2.metric("จำนวนแถวข้อมูล", f"{len(df):,}")
    c3.metric("ประเภทข้อมูล", "ข้อมูลจำลอง" if (df["data_status"]=="simulated").all() else "โปรดตรวจสอบสถานะ")
    selected_disease = st.selectbox("เลือกโรค", disease_list, key="dash_disease")
    selected_year = st.selectbox("เลือกปี พ.ศ.", sorted(df["year_be"].unique().tolist()), index=len(sorted(df["year_be"].unique().tolist()))-1, key="dash_year")
    chartdf = df[(df["disease"]==selected_disease)&(df["year_be"].isin([2567,2568,2569]))].copy()
    chartdf["year_label"] = chartdf["year_be"].astype(str)
    chart = alt.Chart(chartdf).mark_line(point=True).encode(
        x=alt.X("month:O", title="เดือน", sort=list(range(1,13)), axis=alt.Axis(labelExpr=f"['','ม.ค.','ก.พ.','มี.ค.','เม.ย.','พ.ค.','มิ.ย.','ก.ค.','ส.ค.','ก.ย.','ต.ค.','พ.ย.','ธ.ค.'][datum.value]")),
        y=alt.Y("cases:Q", title="จำนวนผู้ป่วยในชุดข้อมูล"),
        color=alt.Color("year_label:N", title="ปี พ.ศ."),
        tooltip=["disease","year_be","month_name_th","cases","data_status","source_url"]
    ).properties(height=350)
    st.altair_chart(chart, use_container_width=True)
    st.caption("กราฟแสดงค่าจากชุดข้อมูลที่เลือก; หากเป็นข้อมูลจำลอง ห้ามตีความเป็นแนวโน้มการระบาดจริง.")
    st.subheader("สถานะทดสอบปี 2569")
    month = st.selectbox("เดือนที่ประเมิน", list(range(1,13)), format_func=lambda m: MONTHS[m-1], key="dash_month")
    threshold = st.slider("เกณฑ์ทดลองเทียบค่าเฉลี่ยปีฐาน (เท่า)", 1.1, 3.0, 1.5, 0.1, key="dash_threshold")
    result = make_assessment(df, selected_disease, month, 2569, threshold)
    if result:
        a,b,c,d = st.columns(4)
        a.metric("จำนวนผู้ป่วยในชุดข้อมูล", f"{result['cases']:,.0f}")
        b.metric("ค่าเฉลี่ยฐาน 2567–2568", f"{result['baseline']:,.0f}")
        c.metric("เทียบค่าฐาน", f"{result['ratio']:.2f}×")
        d.metric("สถานะทดลอง", result["status"])
        st.info("เกณฑ์และผลนี้เป็นการสาธิตซอฟต์แวร์ ไม่ใช่เกณฑ์ทางการแพทย์หรือการระบาดวิทยาที่รับรองแล้ว")
        if st.button("เพิ่มผลนี้ลงประวัติการแจ้งเตือน", key="add_dash_alert"):
            st.session_state.alert_history.append({
                "เวลา":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"โรค":selected_disease,
                "เดือน":MONTHS[month-1],"ปี":2569,"จำนวนในชุดข้อมูล":result["cases"],
                "ค่าเฉลี่ยฐาน":result["baseline"],"อัตราส่วน":result["ratio"],"สถานะ":result["status"],
                "ประเภทข้อมูล":"จำลอง/นำเข้า"
            })
            st.success("บันทึกลงประวัติในเซสชันนี้แล้ว")
    else:
        st.warning("ไม่มีข้อมูลครบทั้งสองปีฐานและปี 2569 สำหรับโรค/เดือนนี้ จึงยังประเมินไม่ได้")
    st.subheader("ข้อมูลล่าสุดในชุดข้อมูล")
    st.dataframe(df.sort_values(["year_be","month"],ascending=[False,False]).head(12),use_container_width=True,hide_index=True)

elif page == "วิเคราะห์แนวโน้ม":
    st.subheader("วิเคราะห์แนวโน้มรายโรค")
    if df.empty:
        st.warning("ยังไม่มีข้อมูล กรุณานำเข้า CSV ก่อน")
        st.stop()
    disease = st.selectbox("เลือกโรค", sorted(df["disease"].unique()), key="trend_disease")
    trend = df[df["disease"]==disease].copy()
    pivot = trend.pivot_table(index="month",columns="year_be",values="cases",aggfunc="mean").reset_index()
    pivot["month_name_th"] = pivot["month"].map(lambda m: MONTHS[int(m)-1])
    st.markdown("**เปรียบเทียบเดือนเดียวกันระหว่างปี**")
    st.dataframe(pivot, use_container_width=True, hide_index=True)
    years = sorted(trend["year_be"].unique())
    if 2567 in years and 2568 in years:
        comp = trend[trend["year_be"].isin([2567,2568])].pivot_table(index="month",columns="year_be",values="cases",aggfunc="mean")
        if 2567 in comp.columns and 2568 in comp.columns:
            comp["เปลี่ยนแปลง 2568 เทียบ 2567 (%)"] = np.where(comp[2567]!=0,(comp[2568]-comp[2567])/comp[2567]*100,np.nan)
            st.markdown("**การเปลี่ยนแปลงรายเดือน 2568 เทียบ 2567**")
            st.dataframe(comp.reset_index().assign(เดือน=lambda x:x["month"].map(lambda m:MONTHS[int(m)-1])).drop(columns=["month"]),use_container_width=True,hide_index=True)
    st.warning("ข้อมูลฐานเพียง 2 ปีใช้สำรวจรูปแบบเบื้องต้นได้ แต่ไม่เพียงพอยืนยันฤดูกาลหรือสร้างเกณฑ์ทางสถิติที่มั่นคง ต้องตรวจสอบข้อมูลจริงและแหล่งที่มา")
    st.markdown("**แนวทางพัฒนาต่อ:** หากมีข้อมูลย้อนหลังรายสัปดาห์/รายเดือนหลายปี ให้พิจารณา baseline ตามฤดูกาลและขีดจำกัดทางสถิติที่เหมาะกับชนิดข้อมูล โดยผู้เชี่ยวชาญต้องตรวจทานก่อนใช้จริง")

elif page == "ศูนย์แจ้งเตือน":
    st.subheader("ศูนย์แจ้งเตือน")
    st.caption("หน้านี้สร้างข้อความและบันทึกประวัติในแอปเท่านั้น ยังไม่ส่งข้อความไปยังโรงพยาบาล")
    if df.empty:
        st.warning("ไม่มีข้อมูลสำหรับประเมิน")
        st.stop()
    with st.form("alert_form"):
        disease = st.selectbox("โรค", sorted(df["disease"].unique()), key="alert_disease")
        month = st.selectbox("เดือน", list(range(1,13)), format_func=lambda m:MONTHS[m-1], key="alert_month")
        threshold = st.number_input("เกณฑ์ทดลอง (เท่าของค่าเฉลี่ยฐาน)", min_value=1.0, max_value=5.0, value=1.5, step=0.1)
        hospital = st.text_input("หน่วยงานผู้รับ (ตัวอย่าง)", "โรงพยาบาลตัวอย่าง")
        receiver = st.selectbox("กลุ่มผู้รับ (ตัวอย่าง)", ["ทีมเฝ้าระวังโรค / ระบาดวิทยา","ทีมควบคุมการติดเชื้อ (IC)","ผู้บริหารโรงพยาบาล"])
        submit = st.form_submit_button("ประเมินและสร้างข้อความแจ้งเตือน")
    if submit:
        result = make_assessment(df,disease,month,2569,float(threshold))
        if not result:
            st.warning("ข้อมูลไม่ครบสำหรับการประเมินเดือนนี้ ต้องมีข้อมูลปี 2567, 2568 และ 2569 ของโรคเดียวกัน")
        else:
            msg = (f"[ข้อความจำลองเพื่อทดสอบระบบ — ไม่ใช่การแจ้งเตือนจริง]\\n"
                   f"หน่วยงานผู้รับ (ตัวอย่าง): {hospital}\\nกลุ่มผู้รับ (ตัวอย่าง): {receiver}\\n"
                   f"โรค: {disease}\\nช่วงเวลา: {MONTHS[month-1]} พ.ศ. 2569\\n"
                   f"จำนวนในชุดข้อมูล: {result['cases']:,.0f}\\nค่าเฉลี่ยฐาน 2567–2568: {result['baseline']:,.0f}\\n"
                   f"อัตราส่วนเทียบฐาน: {result['ratio']:.2f} เท่า\\nเกณฑ์ทดลอง: {threshold:.1f} เท่า\\n"
                   f"ผลประเมิน: {result['status']}\\nประเภทข้อมูล: {df['data_status'].iloc[0] if len(df) else 'ไม่ทราบ'}\\n"
                   "หมายเหตุ: ตรวจสอบข้อมูลและเกณฑ์กับหน่วยงานสาธารณสุขก่อนใช้งานจริง; ไม่มีการส่งข้อความออกจากแอปนี้")
            st.text_area("ข้อความแจ้งเตือนตัวอย่าง",msg,height=260)
            st.download_button("ดาวน์โหลดข้อความ .txt",msg,file_name="nsds_alert_demo.txt",mime="text/plain")
            st.session_state.alert_history.append({"เวลา":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"โรค":disease,"เดือน":MONTHS[month-1],"ปี":2569,
                "จำนวนในชุดข้อมูล":result["cases"],"ค่าเฉลี่ยฐาน":result["baseline"],"อัตราส่วน":result["ratio"],"สถานะ":result["status"],"หน่วยงานผู้รับ":hospital,"ช่องทาง":"ยังไม่ส่ง (สาธิต)"})
            st.success("สร้างข้อความและบันทึกประวัติในเซสชันนี้แล้ว (ยังไม่ได้ส่งจริง)")
    st.markdown("#### ประวัติการแจ้งเตือนในเซสชันนี้")
    if st.session_state.alert_history:
        hist = pd.DataFrame(st.session_state.alert_history)
        st.dataframe(hist,use_container_width=True,hide_index=True)
        st.download_button("ดาวน์โหลดประวัติ CSV",hist.to_csv(index=False).encode("utf-8-sig"),file_name="nsds_alert_history.csv",mime="text/csv")
        if st.button("ล้างประวัติในเซสชันนี้"):
            st.session_state.alert_history=[]
            st.rerun()
    else:
        st.info("ยังไม่มีประวัติการแจ้งเตือนในเซสชันนี้")

elif page == "จัดการข้อมูล":
    st.subheader("จัดการข้อมูล")
    st.markdown("นำเข้า CSV เพื่อทดลองใช้ข้อมูลชุดอื่น โดยต้องแยกข้อมูลจริงและข้อมูลจำลองให้ชัดเจน")
    st.info("คอลัมน์ขั้นต่ำ: disease, year_be, month, cases. คอลัมน์เสริม: data_status, source_url, source_note. ปีใช้ พ.ศ. และเดือนเป็นตัวเลข 1–12")
    uploaded = st.file_uploader("อัปโหลดไฟล์ CSV", type=["csv"])
    if uploaded is not None:
        try:
            raw = pd.read_csv(uploaded)
            normalized = normalize_df(raw)
            st.success(f"อ่านไฟล์ได้ {len(normalized)} แถว")
            st.dataframe(normalized.head(20),use_container_width=True,hide_index=True)
            missing_source = normalized["source_url"].fillna("").astype(str).str.strip().eq("").sum()
            st.metric("แถวที่ไม่มี URL แหล่งอ้างอิง", int(missing_source))
            if st.button("ใช้ไฟล์นี้ใน Dashboard (เฉพาะเซสชันนี้)"):
                st.session_state.uploaded_df = normalized
                st.success("นำเข้าข้อมูลแล้ว หน้าอื่นจะใช้ข้อมูลชุดนี้จนกว่าจะรีเซ็ตเซสชัน")
                st.rerun()
        except Exception as e:
            st.error(f"อ่าน CSV ไม่สำเร็จ: {e}")
    st.markdown("#### ดาวน์โหลดแม่แบบ CSV")
    template = pd.DataFrame([{"disease":"ชื่อโรค","year_be":2567,"month":1,"month_name_th":"มกราคม","cases":0,
                              "data_status":"verified/unverified/simulated","source_url":"https://...","source_note":"ชื่อรายงาน/วันที่ตัดยอด/นิยาม"}])
    st.download_button("ดาวน์โหลดแม่แบบ CSV",template.to_csv(index=False).encode("utf-8-sig"),file_name="nsds_data_template.csv",mime="text/csv")
    if st.session_state.uploaded_df is not None and st.button("กลับไปใช้ข้อมูลตั้งต้นของเดโม"):
        st.session_state.uploaded_df = None
        st.rerun()
    st.caption("ข้อมูลที่นำเข้าเก็บในหน่วยความจำของเซสชันเท่านั้น ไม่ได้บันทึกลงฐานข้อมูลถาวร")

elif page == "วิธีวิเคราะห์และอ้างอิง":
    st.subheader("วิธีวิเคราะห์และแหล่งอ้างอิง")
    st.markdown("""
**วิธีทดลองในแอป**
1. คำนวณค่าเฉลี่ยของเดือนเดียวกันจากปี พ.ศ. 2567 และ 2568
2. เปรียบเทียบจำนวนในชุดข้อมูลปี 2569 กับค่าเฉลี่ยฐาน
3. แสดง NORMAL เมื่อไม่สูงกว่าฐาน, WATCH เมื่อสูงกว่าฐานแต่ยังไม่ถึงเกณฑ์, และ ALERT เมื่ออัตราส่วนถึงเกณฑ์ทดลองที่ผู้ใช้ตั้ง

สูตรทดลอง: `อัตราส่วน = จำนวนปี 2569 ÷ ค่าเฉลี่ยของเดือนเดียวกันในปี 2567–2568`

**ข้อจำกัด**
- ข้อมูลตั้งต้นในชุดนี้เป็นข้อมูลสังเคราะห์ ไม่ใช่สถิติผู้ป่วยจริง
- ฐานข้อมูลเพียง 2 ปีไม่เพียงพอสำหรับยืนยันฤดูกาลหรือประเมินความผันผวนอย่างมั่นคง
- ค่าเกณฑ์เริ่มต้น 1.5 เท่าเป็นค่าทดลอง ไม่ใช่เกณฑ์ทางการ
- ผลประเมินไม่ใช่การยืนยันการระบาด และไม่ควรใช้ตัดสินใจทางการแพทย์
- แอปไม่ส่งแจ้งเตือนจริง; ต้องกำหนดผู้รับ ช่องทาง สิทธิ์ และการอนุมัติจากหน่วยงานก่อน
""")
    st.markdown("#### แหล่งข้อมูลทางการสำหรับค้นข้อมูลจริง")
    for name,url,note in OFFICIAL_SOURCES:
        st.markdown(f"**[{name}]({url})**  \n{note}")
    st.markdown("#### ข้อควรตรวจสอบก่อนใช้ข้อมูลจริง")
    st.markdown("- นิยามผู้ป่วยและโรคต้องสอดคล้องกันทุกปี\n- แยกจำนวนผู้ป่วยรายเดือนออกจากยอดสะสม ณ วันที่รายงาน\n- แยกจำนวนผู้ป่วยออกจากจำนวนผู้เสียชีวิตและข้อมูลห้องปฏิบัติการ\n- บันทึกวันที่เผยแพร่ วันที่ตัดยอด พื้นที่ครอบคลุม และ URL\n- ให้ผู้เชี่ยวชาญด้านระบาดวิทยาตรวจสอบเกณฑ์ก่อนส่งเตือนจริง")
