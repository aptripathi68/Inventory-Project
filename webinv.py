import streamlit as st
import pandas as pd
import csv
import os
import sqlite3




# File paths
STOCK_FILE = DB_FILE = "inventory.db"
MASTER_FILE = "Item_master.xlsx"

# ---------- Helper Functions ----------

def initialize_database():
    """Create inventory table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_master_id TEXT,
            item_description TEXT,
            grade_name TEXT,
            group1_name TEXT,
            group2_name TEXT,
            section_name TEXT,
            unit_weight REAL,
            quantity REAL,
            price REAL
        )
    """)

    conn.commit()
    conn.close()


def append_stock(selected_row, quantity, price):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO inventory (
            item_master_id,
            item_description,
            grade_name,
            group1_name,
            group2_name,
            section_name,
            unit_weight,
            quantity,
            price
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        selected_row["Item Master ID"],
        selected_row["Item Description"],
        selected_row["Grade Name"],
        selected_row["Group1 Name"],
        selected_row["Group2 Name"],
        selected_row["Section Name"],
        selected_row["Unit Wt. (kg/m)"],
        quantity,
        price
    ))

    conn.commit()
    conn.close()


def load_master_data():
    df = pd.read_excel(MASTER_FILE)
    df.columns = df.columns.str.strip()
    return df


def load_stock_data():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM inventory", conn)
    conn.close()

    if not df.empty:
        df["total_value"] = df["quantity"] * df["price"]

    return df


def delete_stock_row(row_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inventory WHERE id = ?", (row_id,))
    conn.commit()
    conn.close()

# Database initialization
initialize_database()

# ---------- Streamlit Interface ----------

st.title("📦 Stock Entry System")

# Initialize stock file
initialize_database()

# Load master data
master_df = load_master_data()

# ---------- 1️⃣ Select Category ----------
categories = sorted(master_df["Group2 Name"].dropna().unique())
selected_category = st.selectbox("Select Category", categories)

filtered_category = master_df[
    master_df["Group2 Name"] == selected_category
]

# ---------- 2️⃣ Select Grade ----------
grades = sorted(filtered_category["Grade Name"].dropna().unique())
selected_grade = st.selectbox("Select Grade", grades)

filtered_grade = filtered_category[
    filtered_category["Grade Name"] == selected_grade
]

# ---------- 3️⃣ Select Item ----------
selected_item_index = st.selectbox(
    "Select Item",
    filtered_grade.index,
    format_func=lambda x: filtered_grade.loc[x, "Item Description"]
)

selected_row = filtered_grade.loc[selected_item_index]

# Display item details
st.write("**Item Details:**")
st.write({
    "Item Master ID": selected_row["Item Master ID"],
    "Description": selected_row["Item Description"],
    "Grade": selected_row["Grade Name"],
    "Unit Weight (kg/m)": selected_row["Unit Wt. (kg/m)"]
})

# Quantity & Price input
quantity = st.number_input("Enter Quantity", min_value=0.0, step=0.01)
price = st.number_input("Enter Price per unit", min_value=0.0, step=0.01)

# Add stock button
if st.button("➕ Add Stock"):
    if quantity > 0 and price > 0:
        append_stock(selected_row, quantity, price)
        st.success("✅ Stock entry successful!")
    else:
        st.error("❌ Quantity and Price must be greater than 0")

# Display current stock
st.subheader("📊 Current Stock")
stock_df = load_stock_data()

if not stock_df.empty:

    # Hide internal item_master_id column (optional)
    display_df = stock_df.drop(columns=["item_master_id"], errors="ignore")

    # Make display index start from 1
    display_df.index = range(1, len(display_df) + 1)

    st.dataframe(display_df)

    st.markdown("### 🗑 Delete Stock Entry")

    # Select database ID (real ID from SQLite)
    row_to_delete = st.selectbox(
        "Select ID to Delete",
        stock_df["id"]
    )

    if st.button("Delete Selected Entry"):
        delete_stock_row(row_to_delete)
        st.success("✅ Stock entry deleted successfully!")
        st.rerun()

else:
    st.info("No stock entries available.")