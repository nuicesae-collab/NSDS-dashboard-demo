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
