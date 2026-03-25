import streamlit as st
import pandas as pd
import pymysql

st.set_page_config(page_title="RAB Purchase Approval", layout="wide")

# ---------------------------
# HEADER
# ---------------------------
st.markdown("""
<h1 style='text-align: center; color: #2E86C1;'>
📦 RAB Purchase Approval System
</h1>
""", unsafe_allow_html=True)

st.markdown("---")

# ---------------------------
# DATABASE CONNECTION
# ---------------------------
conn = pymysql.connect(
    host="10.0.0.5",
    user="deliverytest",
    password="yPz!jC?]Vfv7ke9E",
    database="deliverytest",
    port=3306
)

# ---------------------------
# LOAD DATA
# ---------------------------
query = "SELECT * FROM sku_data"
df = pd.read_sql(query, conn)

if "status" not in df.columns:
    df["status"] = "Pending"

if "comments" not in df.columns:
    df["comments"] = ""

# ---------------------------
# BUYER FILTER
# ---------------------------
buyer = st.selectbox("👤 Select Buyer", df["buyer"].unique())
filtered_df = df[df["buyer"] == buyer].copy()

filtered_df["approve"] = filtered_df["approve"].astype(bool)

# ---------------------------
# OPTIONAL FILTERS
# ---------------------------
col1, col2 = st.columns(2)

with col1:
    show_low_stock = st.checkbox("⚠️ Low stock (<50)")

with col2:
    show_pending = st.checkbox("📌 Pending only")

if show_low_stock:
    filtered_df = filtered_df[filtered_df["current_stock"] < 50]

if show_pending:
    filtered_df = filtered_df[filtered_df["status"] == "Pending"]

# ---------------------------
# STYLING
# ---------------------------
def highlight_low_stock(row):
    if row["current_stock"] < 50:
        return ["background-color: #ffe6e6"] * len(row)
    return [""] * len(row)

def highlight_approved(row):
    if row["approve"]:
        return ["background-color: #e6ffe6"] * len(row)
    return [""] * len(row)

def color_status(val):
    if val == "Approved":
        return "color: green; font-weight: bold"
    return "color: orange; font-weight: bold"

# ---------------------------
# DISPLAY TABLE
# ---------------------------
st.subheader(f"📋 SKU List for {buyer}")

st.dataframe(
    filtered_df.style
    .apply(highlight_low_stock, axis=1)
    .apply(highlight_approved, axis=1)
    .applymap(color_status, subset=["status"]),
    use_container_width=True
)

st.markdown("---")

# ---------------------------
# EDITABLE TABLE
# ---------------------------
st.subheader("✏️ Review & Approve")

edited_df = st.data_editor(
    filtered_df,
    use_container_width=True,
    column_config={
        "id": st.column_config.NumberColumn("ID", disabled=True),
        "buyer": st.column_config.TextColumn("Buyer", disabled=True),
        "sku": st.column_config.TextColumn("SKU", disabled=True),
        "description": st.column_config.TextColumn("Description", disabled=True),
        "suggested_qty": st.column_config.NumberColumn("Suggested Qty", disabled=True),
        "current_stock": st.column_config.NumberColumn("Stock", disabled=True),
        "approve": st.column_config.CheckboxColumn("Approve"),
        "final_qty": st.column_config.NumberColumn("Final Qty"),
        "comments": st.column_config.TextColumn("Comments"),
        "status": st.column_config.TextColumn("Status", disabled=True),
    }
)

# Auto update status
edited_df["status"] = edited_df["approve"].apply(
    lambda x: "Approved" if x else "Pending"
)

# ---------------------------
# BUSINESS LOGIC (IMPORTANT)
# ---------------------------
edited_df["shortage"] = edited_df["suggested_qty"] - edited_df["current_stock"]

st.markdown("---")

# ---------------------------
# SUMMARY
# ---------------------------
st.subheader("📊 Summary")

col1, col2, col3 = st.columns(3)

total_skus = len(edited_df)
approved_skus = edited_df["approve"].sum()
approved_qty = edited_df[edited_df["approve"]]["final_qty"].sum()

col1.metric("📦 Total SKUs", total_skus)
col2.metric("✅ Approved", int(approved_skus))
col3.metric("📊 Approved Qty", int(approved_qty) if approved_qty else 0)

st.markdown("---")

# ---------------------------
# RECOMMENDATION SECTION
# ---------------------------
st.subheader("🚨 Recommended SKUs to Purchase")

recommend_df = edited_df[edited_df["shortage"] > 0]

if not recommend_df.empty:
    recommend_df = recommend_df.sort_values(by="shortage", ascending=False)

    st.dataframe(
        recommend_df[["sku", "current_stock", "suggested_qty", "shortage"]],
        use_container_width=True
    )
else:
    st.success("✅ All SKUs have sufficient stock!")

st.markdown("---")

# ---------------------------
# SMART VISUALIZATION
# ---------------------------
st.subheader("📊 Smart Visualization")

numeric_columns = ["suggested_qty", "current_stock", "final_qty", "shortage"]

x_axis = st.selectbox("Select X-axis", ["sku"])
y_axis = st.selectbox("Select Y-axis", numeric_columns)

chart_type = st.selectbox(
    "Select Chart Type",
    ["Bar Chart", "Line Chart"]
)

sort_option = st.selectbox(
    "Sort By",
    ["None", "Highest First", "Lowest First"]
)

chart_df = edited_df.copy()

if sort_option == "Highest First":
    chart_df = chart_df.sort_values(by=y_axis, ascending=False)
elif sort_option == "Lowest First":
    chart_df = chart_df.sort_values(by=y_axis, ascending=True)

chart_df = chart_df.set_index(x_axis)

if chart_type == "Bar Chart":
    st.bar_chart(chart_df[y_axis])

elif chart_type == "Line Chart":
    st.line_chart(chart_df[y_axis])

st.markdown("---")

# ---------------------------
# SUBMIT BUTTON
# ---------------------------
if st.button("🚀 Submit Approval"):

    with st.spinner("Submitting..."):
        cursor = conn.cursor()

        approved_rows = edited_df[edited_df["approve"] == True]

        for _, row in approved_rows.iterrows():
            update_query = """
            UPDATE sku_data
            SET approve=%s, final_qty=%s, status=%s, comments=%s
            WHERE id=%s
            """
            cursor.execute(update_query, (
                int(row["approve"]),
                int(row["final_qty"]),
                row["status"],
                row["comments"],
                int(row["id"])
            ))

        conn.commit()

    st.success("✅ Approval submitted successfully!")

conn.close()

st.markdown("---")
st.caption("RAB IDW Demo | Purchase Approval Workflow")