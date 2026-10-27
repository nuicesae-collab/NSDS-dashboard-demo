# NSDS Dashboard — New Prototype

ต้นแบบระบบเฝ้าระวังโรคตามฤดูกาล ใช้ข้อมูลจำลองเท่านั้น

## ฟังก์ชัน
- ภาพรวมระดับประเทศและเขตสุขภาพ
- วิเคราะห์แนวโน้มรายเดือนและเปรียบเทียบปี พ.ศ.
- ทดลองระบบแจ้งเตือนจากค่าเฉลี่ย 3 เดือนก่อนหน้า

## Deploy to Streamlit Community Cloud
1. สร้าง GitHub Repository ใหม่เพื่อไม่แตะต้อง Repository ต้นฉบับ
2. อัปโหลด `app.py`, `requirements.txt`, `README.md` ไปที่ root ของ repository
3. ใน Streamlit Community Cloud เลือก repository ใหม่นี้ และตั้ง Main file path เป็น `app.py`
4. ชุดข้อมูล CSV ในโฟลเดอร์ `data/` เป็นไฟล์เสริม หากอัปโหลดไปด้วยแอปจะใช้ไฟล์นั้น หากไม่อัปโหลดแอปจะสร้างข้อมูลจำลองให้อัตโนมัติ

## Run locally
```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

**คำเตือน:** ข้อมูลเป็นข้อมูลสังเคราะห์เพื่อสาธิตเท่านั้น ไม่ใช่ข้อมูลจริงหรือข้อมูลทางการ
