# bill.py
# -*- coding: utf-8 -*-

import io
import re
import pandas as pd
import numpy as np
import streamlit as st

# =====================================================
# Page config
# =====================================================
st.set_page_config(
    page_title="Sales & Payment System",
    layout="wide"
)

# =====================================================
# Utility functions
# =====================================================
def as_str(x):
    try:
        if pd.isna(x):
            return ""
    except Exception:
        pass
    return str(x).strip() if x is not None else ""


def to_float(v):
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    try:
        return float(str(v).replace(",", ""))
    except Exception:
        return None


def df_to_excel_bytes(df: pd.DataFrame, sheet_name="result"):
    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return bio.getvalue()


# =====================================================
# TAB UI
# =====================================================
tab_bill, tab_payment = st.tabs(
    ["🧾 แปลงไฟล์บิล", "💰 รายงานการรับชำระหนี้"]
)

# =====================================================
# TAB 1 : แปลงไฟล์บิล (โครงสร้างพื้นฐาน)
# =====================================================
with tab_bill:
    st.title("🧾 แปลงไฟล์บิล")

    st.info(
        "แท็บนี้ใช้สำหรับแปลงไฟล์บิลขาย\n"
        "โครงสร้างตัวอย่าง (สามารถต่อยอด logic เพิ่มได้ภายหลัง)"
    )

    uploaded_bill = st.file_uploader(
        "อัปโหลดไฟล์บิล (.xlsx / .xls)",
        type=["xlsx", "xls"],
        key="bill_file"
    )

    if uploaded_bill:
        df_bill = pd.read_excel(uploaded_bill)

        st.subheader("ตัวอย่างข้อมูลจากไฟล์บิล")
        st.dataframe(df_bill.head(200), use_container_width=True)

        csv_bytes = df_bill.to_csv(index=False).encode("utf-8-sig")
        xlsx_bytes = df_to_excel_bytes(df_bill, sheet_name="bill")

        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "⬇️ ดาวน์โหลด CSV",
                data=csv_bytes,
                file_name="bill_raw.csv",
                mime="text/csv",
            )
        with c2:
            st.download_button(
                "⬇️ ดาวน์โหลด Excel",
                data=xlsx_bytes,
                file_name="bill_raw.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    else:
        st.caption("ยังไม่ได้อัปโหลดไฟล์บิล")

# =====================================================
# TAB 2 : รายงานการรับชำระหนี้ (Logic หลัก)
# =====================================================
with tab_payment:
    st.title("💰 รายงานการรับชำระหนี้")

    uploaded_payment = st.file_uploader(
        "อัปโหลดไฟล์รายงานการรับชำระหนี้ (.xlsx)",
        type=["xlsx"],
        key="payment_file"
    )

    if uploaded_payment:
        # ----------------------------
        # Read file
        # ----------------------------
        df = pd.read_excel(uploaded_payment, skiprows=4)

        # ----------------------------
        # Business logic
        # ----------------------------
        mask_re = df["เลขที่ใบเสร็จ"].astype(str).str.contains("RE", na=False)

        df["new_col"] = np.where(
            mask_re,
            df["พนักงานขาย"],
            pd.NA
        )

        df["จำนวนเงินรวมตามใบเสร็จ"] = np.where(
            mask_re,
            df["ยอดตามใบกำกับ"],
            pd.NA
        )

        fill_cols = [
            "วันที่รับชำระ",
            "เลขที่ใบเสร็จ",
            "วันที่",
            "ชื่อลูกค้า",
            "new_col",
            "จำนวนเงินรวมตามใบเสร็จ",
        ]

        df[fill_cols] = df[fill_cols].ffill()

        # เฉพาะรายการที่ตัดเงินมัดจำ
        df = df[df["ตัดเงินมัดจำ"].notna()]

        # เฉพาะพนักงานขายที่มี I
        result_cols = [
            "วันที่รับชำระ",
            "เลขที่ใบเสร็จ",
            "วันที่",
            "ชื่อลูกค้า",
            "พนักงานขาย",
            "new_col",
            "ตัดเงินมัดจำ",
            "ยอดตามใบกำกับ",
            "จำนวนเงินรวมตามใบเสร็จ",
        ]

        df_result = df.loc[
            df["พนักงานขาย"].astype(str).str.contains("I", na=False),
            result_cols
        ]

        # ----------------------------
        # Display result
        # ----------------------------
        st.subheader("ผลลัพธ์รายงานการรับชำระหนี้")
        st.write(f"จำนวนรายการทั้งหมด: **{len(df_result):,}** แถว")
        st.dataframe(df_result, use_container_width=True)

        # ----------------------------
        # Download
        # ----------------------------
        csv_bytes = df_result.to_csv(index=False).encode("utf-8-sig")
        xlsx_bytes = df_to_excel_bytes(df_result, sheet_name="payment_report")

        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "⬇️ ดาวน์โหลด CSV",
                data=csv_bytes,
                file_name="payment_report.csv",
                mime="text/csv",
            )
        with c2:
            st.download_button(
                "⬇️ ดาวน์โหลด Excel",
                data=xlsx_bytes,
                file_name="payment_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    else:
        st.caption("กรุณาอัปโหลดไฟล์รายงานการรับชำระหนี้เพื่อแสดงผล")
