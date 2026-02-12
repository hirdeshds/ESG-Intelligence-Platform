import streamlit as st
import pandas as pd
import plotly.express as px


st.set_page_config(
    page_title="AI-Driven ESG Monitoring System",
    layout="wide"
)

st.title("AI-Driven Multi-Agent ESG Intelligence Platform")


@st.cache_data
def load_data():
    return pd.read_csv(r"C:\Users\Mahek Bhatia\Desktop\ESG-Monitoring-System\outputs\agent4_final_output.csv")

df = load_data()

if df.empty:
    st.error("Dataset is empty!")
    st.stop()


st.subheader("Key Risk Indicators")

col1, col2, col3 = st.columns(3)

critical = df[df["alert_level"] == "Critical"].shape[0]
warning = df[df["alert_level"] == "Warning"].shape[0]
low = df[df["alert_level"] == "Low"].shape[0]

col1.metric("Critical Firms", critical)
col2.metric("Warning Firms", warning)
col3.metric("Low Risk Firms", low)

st.divider()


st.subheader("ESG Risk Score by Firm")

fig_bar = px.bar(
    df,
    x="Firm_ID",
    y="final_esg_risk_score",
    color="alert_level",
    title="Final ESG Risk Score",
    height=450
)

st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("ESG Trend Over Time")

fig_trend = px.line(
    df,
    x="Year",
    y="final_esg_risk_score",
    color="Firm_ID",
    markers=True,
    title="Risk Score Trend"
)

st.plotly_chart(fig_trend, use_container_width=True)


st.subheader("Firm-Level Analysis")

selected_firm = st.selectbox(
    "Select Firm",
    df["Firm_ID"].unique()
)

filtered_df = df[df["Firm_ID"] == selected_firm]

st.dataframe(filtered_df, use_container_width=True)


st.subheader("Alert Summary")

latest_year = df["Year"].max()
latest_data = df[df["Year"] == latest_year]

st.write(f"Latest Year: {latest_year}")

st.dataframe(
    latest_data[[
        "Firm_ID",
        "final_esg_risk_score",
        "alert_level",
        "Overall_Compliance"
    ]],
    use_container_width=True
)


st.subheader("Compliance Distribution")

compliance_counts = df["Overall_Compliance"].value_counts().reset_index()
compliance_counts.columns = ["Compliance", "Count"]

fig_pie = px.pie(
    compliance_counts,
    names="Compliance",
    values="Count",
    title="Overall Compliance Status"
)

st.plotly_chart(fig_pie, use_container_width=True)


st.success("Multi-Agent ESG Monitoring System Running Successfully")
