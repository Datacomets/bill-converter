# bill.py
# -*- coding: utf-8 -*-

import re
import io
import pandas as pd
import numpy as np
import streamlit as st

st.set_page_config(page_title="Sales System", layout="wide")

DATE_RE = re.compile(r"(\d{1,2}/\d{1,2}/\d{4})")

# =====================================================
# Utility
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


def df_to_excel_bytes(df: pd.DataFrame):
    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="result")
    return bio.getvalue()


# =====================================================
# Bill Parser (TAB 1)
# =====================================================
def is_bill_no_text(s: str) -> bool:
    return bool(re.fullmatch(r"\d{6}", as_str(s)))


def parse_bill_file(uploaded_file):
    df = pd.read_excel(uploaded_file, header=None)

    records = []
    current_bill = ""

    for _, row in df.iterrows():
        bill_no = as_str(row[0])
        item = as_str(row[1])
        qty = to_float(row[2])
        price = to_float(row[3])
        amount = to_float(row[4])

        if is_bill_no_text(bill_no):
            current_bill = bill_no
            continue

        if current_bill and item:
            records.append(
                {
                    "bill_no": current_bill,
                    "item": item,
                    "qty": qty,
                    "price": price,
                    "line_amount": amount,
                }
            )

    df_out = pd.DataFrame(records)

    if not df_out.empty:
        bill_total = (
            df_out.groupby("bill_no")["line_amount"]
            .sum()
            .reset_index(name="bill_total")
        )
        df_out = df_out.merge(bill_total, on="bill_no", how="left")

    return df_out


# =====================================================
# UI
# =====================================================
tab_bill, tab_payment = st.tabs(
    ["🧾 แปลงไฟล์บิล", "💰 รายงานการรับชำระหนี้"]
)

# =====================================================
# TAB 1 : แปลงไฟล์บิล
# =====================================================
with tab_bill:
    st.title("🧾 แปลงไฟล์บิล")

    uploaded_bill = st.file_uploader(
        "อัปโหลดไฟล์บิล (.xlsx / .xls)",
        type=["xlsx", "xls"],
        key="bill_file",
    )

    if uploaded_bill:
        df_bill = parse_bill_file(uploaded_bill)

        st.subheader("ตัวอย่างข้อมูล")
        st.dataframe(df_bill.head(200), use_container_width=True)

        if not df_bill.empty:
            csv_bytes = df_bill.to_csv(index=False).encode("utf-8-sig")
            xlsx_bytes = df_to_excel_bytes(df_bill)

            c1, c2 = st.columns(2)
            with c1:
                st.download_button(
                    "⬇️ ดาวน์โหลด CSV",
                    data=csv_bytes,
                    file_name="bill_clean.csv",
                    mime="text/csv",
                )
            with c2:
                st.download_button(
                    "⬇️ ดาวน์โหลด Excel",
                    data=xlsx_bytes,
                    file_name="bill_clean.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

# =====================================================
# TAB 2 : รายงานการรับชำระหนี้
# =====================================================
with tab_payment:
    st.title("💰 รายงานการรับชำระหนี้")

    uploaded_payment = st.file_uploader(
        "อัปโหลดไฟล์รายงานการรับชำระหนี้",
        type=["xlsx"],
        key="payment_file",
    )

    if not uploaded_payment:
        st.info("กรุณาอัปโหลดไฟล์ก่อน")
        st.stop()

    df = pd.read_excel(uploaded_payment, skiprows=4)

    # ---------- Logic รายงานการรับชำระหนี้ ----------
    mask_re = df["เลขที่ใบเสร็จ"].astype(str).str.contains("RE", na=False)

    df["new_col"] = np.where(
        mask_re,
        df["พนักงานขาย"],
        pd.NA,
    )

    df["จำนวนเงินรวมตามใบเสร็จ"] = np.where(
        mask_re,
        df["ยอดตามใบกำกับ"],
        pd.NA,
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

    # เอาเฉพาะรายการที่ตัดเงินมัดจำ
    df = df[df["ตัดเงินมัดจำ"].notna()]

    # เอาเฉพาะพนักงานขายที่มี I
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
        result_cols,
    ]

    st.subheader("ผลลัพธ์รายงานการรับชำระหนี้")
    st.write(f"จำนวนรายการทั้งหมด: **{len(df_result):,}** แถว")
    st.dataframe(df_result, use_container_width=True)

    csv_bytes = df_result.to_csv(index=False).encode("utf-8-sig")
    xlsx_bytes = df_to_excel_bytes(df_result)

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
