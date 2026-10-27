from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="NSDS Dashboard", page_icon="🩺", layout="wide")
DATA = Path(__file__).parent / "data" / "disease_monthly_data_simulated.csv"

@st.cache_data
def load():
    if DATA.exists():
        d = pd.read_csv(DATA)
    else:
        # Fallback: build synthetic data automatically if the optional CSV folder was not uploaded.
        import random, math
        random.seed(269)
        disease_meta = {
            "โรคไข้เลือดออก": (950, .45), "โรคไข้หวัดใหญ่": (1450, .25),
            "โรคโควิด-19": (850, .18), "โรคมือ เท้า ปาก": (620, .30),
            "โรคเลปโตสไปโรซิส": (210, .38), "โรคมาลาเรีย": (160, .22),
        }
        thai_months = ["มกราคม","กุมภาพันธ์","มีนาคม","เมษายน","พฤษภาคม","มิถุนายน",
                       "กรกฎาคม","สิงหาคม","กันยายน","ตุลาคม","พฤศจิกายน","ธันวาคม"]
        weights = [.07,.06,.08,.07,.07,.08,.07,.08,.08,.08,.07,.07,.07]
        records = []
        for y in [2567, 2568, 2569]:
            for m in range(1, (10 if y == 2569 else 12) + 1):
                for dis, (base, season) in disease_meta.items():
                    for r, w in enumerate(weights, 1):
                        rain = math.sin((m - 4) / 12 * 2 * math.pi)
                        n = max(0, int(base*w*(1+season*max(0,rain))*(1+(y-2567)*.045)*random.uniform(.78,1.24)))
                        spike = False
                        if y == 2569 and m in (7,8) and r in (4,7) and dis in ("โรคไข้เลือดออก","โรคเลปโตสไปโรซิส"):
                            n = int(n*(2 if m == 7 else 2.5)); spike = True
                        if y == 2569 and m == 9 and r in (2,10) and dis == "โรคไข้หวัดใหญ่":
                            n = int(n*1.9); spike = True
                        records.append({"year_be":y,"month":m,"month_name_th":thai_months[m-1],
                            "disease":dis,"health_region":f"เขตสุขภาพที่ {r}","cases":n,
                            "data_status":"simulated","source_note":"ข้อมูลจำลองเพื่อสาธิตเท่านั้น ไม่ใช่ข้อมูลผู้ป่วยจริง",
                            "is_test_spike":spike})
        d = pd.DataFrame(records)
    d["year_be"] = d["year_be"].astype(int)
    d["month"] = d["month"].astype(int)
    d["cases"] = d["cases"].astype(int)
    return d

df = load()
diseases = sorted(df.disease.unique())
regions = sorted(df.health_region.unique())
years = sorted(df.year_be.unique())
short_month = {1:"ม.ค.",2:"ก.พ.",3:"มี.ค.",4:"เม.ย.",5:"พ.ค.",6:"มิ.ย.",7:"ก.ค.",8:"ส.ค.",9:"ก.ย.",10:"ต.ค.",11:"พ.ย.",12:"ธ.ค."}

st.markdown("""<style>.block-container{padding-top:1.3rem}.stMetric{background:#f5f7fb;padding:12px;border-radius:12px}</style>""",unsafe_allow_html=True)
st.title("🩺 NSDS Dashboard")
st.caption("National Seasonal Disease Surveillance Dashboard | ระบบเฝ้าระวังโรคตามฤดูกาล")
st.warning("ข้อมูลจำลองเพื่อสาธิตเท่านั้น ไม่ใช่ข้อมูลผู้ป่วยจริง และไม่ใช้แทนการตัดสินใจทางสาธารณสุข")

with st.sidebar:
    st.header("เมนูระบบ")
    page=st.radio("ไปยังหน้า",["ภาพรวม Dashboard","วิเคราะห์แนวโน้ม","จำลองระบบแจ้งเตือน","ข้อมูลและวิธีใช้"])
    st.divider()
    level=st.radio("ระดับพื้นที่",["ระดับประเทศ","ระดับเขตสุขภาพ"])
    region=st.selectbox("เขตสุขภาพ",regions,index=3) if level=="ระดับเขตสุขภาพ" else None
    disease=st.selectbox("เลือกโรค",diseases,index=0)
    year=st.selectbox("ปี พ.ศ.",years,index=len(years)-1)

def scoped(source, dis=None, yr=None):
    x=source.copy()
    if region: x=x[x.health_region==region]
    if dis: x=x[x.disease==dis]
    if yr: x=x[x.year_be==yr]
    return x

def alerts_for(data, threshold=1.5, min_increase=50):
    result=[]
    for dis in diseases:
        s=data[data.disease==dis].groupby("month",as_index=False).cases.sum().sort_values("month")
        if len(s)<4: continue
        last=int(s.iloc[-1].cases); avg=float(s.iloc[-4:-1].cases.mean())
        ratio=last/avg if avg else 0; increase=last-avg
        if ratio>=threshold and increase>=min_increase:
            result.append({"ระดับ":"สูง" if ratio>=2 else "เฝ้าระวัง","โรค":dis,"เดือนล่าสุด":short_month[int(s.iloc[-1].month)],"จำนวนล่าสุด":last,"เฉลี่ย 3 เดือนก่อน":round(avg),"เพิ่มขึ้น":round(increase),"เทียบค่าเฉลี่ย (เท่า)":round(ratio,2)})
    return pd.DataFrame(result)

if page=="ภาพรวม Dashboard":
    x=scoped(df,yr=year)
    d=x[x.disease==disease]
    latest=int(d.month.max()); current=int(d[d.month==latest].cases.sum())
    prev=int(d[d.month==latest-1].cases.sum()) if latest>1 else 0
    change=(current-prev)/prev*100 if prev else 0
    total=int(d.cases.sum())
    a=alerts_for(x)
    c1,c2,c3,c4=st.columns(4)
    c1.metric("ผู้ป่วยสะสมของโรคที่เลือก",f"{total:,}")
    c2.metric(f"เดือนล่าสุด ({short_month[latest]})",f"{current:,}")
    c3.metric("เปลี่ยนจากเดือนก่อน",f"{change:+.1f}%",delta=f"{current-prev:+,} ราย")
    c4.metric("โรคเข้าเกณฑ์แจ้งเตือนจำลอง",str(len(a)))
    st.subheader("แนวโน้มรายเดือน")
    trend=d.groupby(["month","month_name_th"],as_index=False).cases.sum().sort_values("month")
    trend["เดือน"]=trend.month.map(short_month)
    fig=px.line(trend,x="เดือน",y="cases",markers=True,title=f"{disease} — พ.ศ. {year}",labels={"cases":"จำนวนผู้ป่วยจำลอง","เดือน":"เดือน"})
    fig.update_layout(margin=dict(l=10,r=10,t=50,b=10),hovermode="x unified")
    st.plotly_chart(fig,use_container_width=True)
    left,right=st.columns(2)
    with left:
        st.subheader("เปรียบเทียบโรค")
        by=x.groupby("disease",as_index=False).cases.sum().sort_values("cases")
        st.plotly_chart(px.bar(by,x="cases",y="disease",orientation="h",labels={"cases":"จำนวนผู้ป่วยจำลอง","disease":"โรค"}),use_container_width=True)
    with right:
        st.subheader("ผลแจ้งเตือนจำลอง")
        st.dataframe(a,hide_index=True,use_container_width=True) if not a.empty else st.success("ไม่พบโรคที่เข้าเกณฑ์ตามค่าตั้งต้น")
elif page=="วิเคราะห์แนวโน้ม":
    st.header("วิเคราะห์แนวโน้มโรค")
    x=scoped(df,dis=disease)
    compare=st.multiselect("เปรียบเทียบปี พ.ศ.",years,default=years)
    t=x[x.year_be.isin(compare)].groupby(["year_be","month"],as_index=False).cases.sum()
    t["เดือน"]=t.month.map(short_month)
    fig=px.line(t,x="เดือน",y="cases",color="year_be",markers=True,labels={"year_be":"ปี พ.ศ.","cases":"จำนวนผู้ป่วยจำลอง","เดือน":"เดือน"},title=f"เปรียบเทียบ {disease}")
    fig.update_layout(margin=dict(l=10,r=10,t=50,b=10),hovermode="x unified")
    st.plotly_chart(fig,use_container_width=True)
    st.subheader("ตารางรายเดือน")
    pivot=t.pivot(index="month",columns="year_be",values="cases").reset_index()
    pivot.insert(1,"เดือน",pivot.month.map(short_month)); pivot=pivot.drop(columns="month")
    st.dataframe(pivot,hide_index=True,use_container_width=True)
    st.info("ใช้ดูรูปแบบและความเปลี่ยนแปลงตามเวลา ไม่ควรสรุปสาเหตุจากกราฟเพียงอย่างเดียว")
elif page=="จำลองระบบแจ้งเตือน":
    st.header("จำลองระบบแจ้งเตือน")
    st.write("ระบบเปรียบเทียบเดือนล่าสุดกับค่าเฉลี่ย 3 เดือนก่อนหน้า")
    c1,c2=st.columns(2)
    threshold=c1.slider("เกณฑ์เทียบค่าเฉลี่ย (เท่า)",1.1,3.0,1.5,.1)
    minimum=c2.number_input("จำนวนเพิ่มขึ้นขั้นต่ำ (ราย)",0,5000,50,10)
    alert_year=st.selectbox("ปีที่ใช้จำลอง",years,index=len(years)-1,key="alert_year")
    result=alerts_for(scoped(df,yr=alert_year),threshold,minimum)
    if result.empty: st.success("ไม่พบโรคที่เข้าเกณฑ์ตามเงื่อนไขนี้")
    else:
        st.error(f"พบ {len(result)} โรคเข้าเกณฑ์แจ้งเตือนจำลอง")
        st.dataframe(result,hide_index=True,use_container_width=True)
    with st.expander("หลักการทำงาน"):
        st.markdown("1. รวมจำนวนผู้ป่วยจำลองตามพื้นที่และโรค\n2. เปรียบเทียบเดือนล่าสุดกับค่าเฉลี่ย 3 เดือนก่อนหน้า\n3. แจ้งเตือนเมื่ออัตราส่วนและจำนวนที่เพิ่มขึ้นถึงเกณฑ์\n4. ระดับเตือนเป็นกติกาสาธิต ไม่ใช่ระดับความเสี่ยงทางการแพทย์")
elif page=="ข้อมูลและวิธีใช้":
    st.header("ข้อมูลและวิธีใช้")
    st.markdown("""- เลือกระดับประเทศหรือเขตสุขภาพจากแถบด้านซ้าย\n- เลือกโรคและปี พ.ศ.\n- ใช้ “วิเคราะห์แนวโน้ม” เพื่อเปรียบเทียบปี\n- ใช้ “จำลองระบบแจ้งเตือน” เพื่อทดลองปรับเกณฑ์\n\n**ข้อจำกัด:** ข้อมูลทั้งหมดสังเคราะห์ขึ้นเพื่อสาธิต ไม่ใช่ข้อมูลทางการ และไม่ควรใช้ประกอบการตัดสินใจจริง""")
    st.dataframe(df.head(12),hide_index=True,use_container_width=True)

st.divider()
st.caption("NSDS Dashboard prototype · Synthetic data only · Streamlit")
