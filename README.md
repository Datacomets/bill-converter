# Bill Converter (Streamlit)

แอปแปลงไฟล์บิลจาก Excel (.xlsx/.xls) → ตารางสะอาดสำหรับวิเคราะห์

## Features
- Upload หลายไฟล์พร้อมกัน
- เลือก sheet ต่อไฟล์ได้
- ดึง machine_name + date_from/date_to จากหัวไฟล์อัตโนมัติ
- สร้าง unique_bill_id = machine_name-bill_no
- สร้างแถว TOTAL ต่อท้ายทุกบิล
- discount = abs(ยอดรวมสินค้า) เฉพาะแถวที่ยอดติดลบ (แถว TOTAL จะว่าง)
- Export CSV / Excel
- เปลี่ยนชื่อคอลัมน์: line_amount → ยอดรวมสินค้า, bill_total → ยอดรวมบิล

## Setup
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run
```bash
python -m streamlit run bill.py
```
