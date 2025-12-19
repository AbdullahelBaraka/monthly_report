import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from io import BytesIO

st.set_page_config(page_title="Surgical Analytics", layout="wide")

# 1. Blue Theme CSS (Bright to Dark)
st.markdown("""
<style>
/* Main Title - Dark Blue */
.main-title {text-align: center; color: #1e3a8a; font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;}
.subtitle {text-align: center; color: #60a5fa; font-size: 1.1rem; margin-bottom: 2rem;}

/* Metric Cards - Gradient Blue */
.stMetric {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); 
    padding: 1rem; 
    border-radius: 10px; 
    border: 1px solid #bfdbfe;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.stMetric label {color: #1e40af !important;}
.stMetric [data-testid="stMetricValue"] {color: #172554 !important;}

/* Section Headers - Blue Gradient */
.section-header {
    background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); 
    color: white; 
    padding: 1rem; 
    border-radius: 8px; 
    font-size: 1.5rem; 
    font-weight: 600; 
    margin: 2rem 0 1rem 0;
}

/* Buttons - Blue */
.stButton>button {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); 
    color: white; 
    border: none; 
    padding: 0.75rem 2rem; 
    font-size: 1.1rem; 
    font-weight: 600; 
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

def clean_columns(df):
    df.columns = df.columns.str.replace(r"\s+", " ", regex=True).str.strip()
    return df

def safe_sum(df, col):
    return df[col].sum() if col in df.columns else 0

def classify_degree(x):
    x = str(x).lower()
    if "consult" in x: return "Consultant"
    if "special" in x: return "Specialist"
    if "resident" in x: return "Resident"
    return "Other"

def generate_pdf(dept_df, department, detailed_tables, perf_table, op_source_table, op_value_table, fin_table):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    # PDF Styles - Blue Theme
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#1e3a8a'), spaceAfter=30, alignment=TA_CENTER)
    header_style = ParagraphStyle('Header', parent=styles['Heading2'], fontSize=16, textColor=colors.HexColor('#2563eb'), spaceAfter=12, spaceBefore=20)
    
    elements.append(Paragraph(f"Surgical Department Report - {department}", title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Staff Breakdown
    elements.append(Paragraph("Staff Breakdown by Degree", header_style))
    for degree, table_df in detailed_tables.items():
        total = len(table_df)
        contracted = (table_df["Contract Type"] == "Contracted").sum() if "Contract Type" in table_df.columns else 0
        general = (table_df["Contract Type"] == "General").sum() if "Contract Type" in table_df.columns else 0
        elements.append(Paragraph(f"{degree}s - Total: {total} | Contracted: {contracted} | General: {general}", styles['Heading3']))
        
        data = [table_df.columns.tolist()] + table_df.values.tolist()
        t = Table(data, colWidths=[4*inch, 2*inch] if "Contract Type" in table_df.columns else [6*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')), # Dark Blue Header
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.aliceblue]), 
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.2*inch))
    
    elements.append(PageBreak())
    
    # Performance Table
    elements.append(Paragraph("Overall Performance", header_style))
    data = [perf_table.columns.tolist()] + perf_table.values.tolist()
    t = Table(data, colWidths=[1.5*inch, 1*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.aliceblue]),
    ]))
    elements.append(t)
    elements.append(PageBreak())
    
    # Operations
    elements.append(Paragraph("Operations Overview", header_style))
    for title, table in [("Operation Source", op_source_table), ("Operation Value", op_value_table)]:
        elements.append(Paragraph(title, styles['Heading3']))
        data = [table.columns.tolist()] + table.values.tolist()
        t = Table(data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.aliceblue]),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.2*inch))
    
    elements.append(PageBreak())
    
    # Financial
    elements.append(Paragraph("Financial Performance", header_style))
    data = [fin_table.columns.tolist()] + fin_table.values.tolist()
    t = Table(data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.aliceblue]),
    ]))
    elements.append(t)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# Main App
st.markdown('<h1 class="main-title">🏥 Surgical Department Analytics</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Comprehensive Performance & Financial Analysis Dashboard</p>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 📁 Data Upload")
    uploaded_file = st.file_uploader("Upload Department CSV", type=["csv"])
    if uploaded_file:
        st.success("✅ File uploaded!")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = clean_columns(df)
    
    if "department" not in df.columns:
        st.error("❌ CSV must contain 'department' column")
        st.stop()
    
    with st.sidebar:
        department = st.selectbox("🏥 Select Department", sorted(df["department"].dropna().unique()))
        st.metric("Total Departments", len(df["department"].unique()))
        st.metric("Total Staff", len(df))
    
    dept_df = df[df["department"] == department].copy()
    dept_df["Degree Group"] = dept_df["degree"].apply(classify_degree) if "degree" in dept_df.columns else "Other"
    
    # Manpower Overview (Modified: 3 cards only)
    st.markdown('<div class="section-header">👥 Manpower Overview</div>', unsafe_allow_html=True)
    total_staff = len(dept_df)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Staff", total_staff)
    
    if "Contract type" in dept_df.columns:
        contract_counts = dept_df["Contract type"].value_counts()
        cont_val = contract_counts.get("Contracted", 0)
        cont_pct = (cont_val/total_staff*100) if total_staff else 0
        col2.metric("Contracted", f"{cont_val} ({cont_pct:.1f}%)")
        
        gen_val = contract_counts.get("General", 0)
        gen_pct = (gen_val/total_staff*100) if total_staff else 0
        col3.metric("General", f"{gen_val} ({gen_pct:.1f}%)")
    else:
        col2.metric("Contracted", "N/A")
        col3.metric("General", "N/A")
    
    # Staff Breakdown (Modified: 3 cards per degree)
    st.markdown('<div class="section-header">📋 Staff Breakdown by Degree</div>', unsafe_allow_html=True)
    detailed_tables = {}
    
    for degree in ["Consultant", "Specialist", "Resident"]:
        deg_df = dept_df[dept_df["Degree Group"] == degree]
        if not deg_df.empty:
            total_deg = len(deg_df)
            st.markdown(f"#### 👨‍⚕️ {degree}s")
            
            # 3 Cards per Degree
            c1, c2, c3 = st.columns(3)
            c1.metric("Total", total_deg)
            
            if "Contract type" in deg_df.columns:
                contracted = (deg_df["Contract type"] == "Contracted").sum()
                general = (deg_df["Contract type"] == "General").sum()
                c2.metric("Contracted", contracted)
                c3.metric("General", general)
                table_df = deg_df[["staff name", "Contract type"]].copy()
                table_df.columns = ["Staff Name", "Contract Type"]
            else:
                c2.metric("Contracted", "N/A")
                c3.metric("General", "N/A")
                table_df = deg_df[["staff name"]].copy()
                table_df.columns = ["Staff Name"]
            
            st.dataframe(table_df, use_container_width=True, hide_index=True)
            detailed_tables[degree] = table_df
            st.markdown("---")
    
    # Performance Metrics
    st.markdown('<div class="section-header">📊 Performance Metrics</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Hours", f"{safe_sum(dept_df, 'total hours'):,.0f}")
    col2.metric("Opened Clinics", f"{safe_sum(dept_df, 'opened clinic'):,.0f}")
    col3.metric("Total Visits", f"{safe_sum(dept_df, 'Total visits'):,.0f}")
    col4.metric("Total Operations", f"{safe_sum(dept_df, 'Operation total number'):,.0f}")
    
    # Operations Overview
    st.markdown('<div class="section-header">🛠️ Operations Overview</div>', unsafe_allow_html=True)
    elective = safe_sum(dept_df, "opr_elective")
    emergency = safe_sum(dept_df, "opr_emergency")
    high = safe_sum(dept_df, "opr_high")
    moderate = safe_sum(dept_df, "opr_moderate")
    low = safe_sum(dept_df, "opr_low")
    
    # Blue Palette for Charts
    blue_colors_source = ['#1e3a8a', '#60a5fa'] # Dark Blue, Light Blue
    blue_colors_value = ['#172554', '#2563eb', '#93c5fd'] # Darkest, Mid, Lightest

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure(data=[go.Pie(labels=['Elective', 'Emergency'], values=[elective, emergency], hole=0.4, marker_colors=blue_colors_source)])
        fig.update_layout(title="Operation Source", height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = go.Figure(data=[go.Pie(labels=['High', 'Moderate', 'Low'], values=[high, moderate, low], hole=0.4, marker_colors=blue_colors_value)])
        fig.update_layout(title="Operation Value", height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    # Financial Performance
    st.markdown('<div class="section-header">💰 Financial Performance</div>', unsafe_allow_html=True)
    total_salary = safe_sum(dept_df, "total slary")
    total_income = safe_sum(dept_df, "total income")
    total_net = safe_sum(dept_df, "Net")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Salary", f"${total_salary:,.0f}")
    col2.metric("Total Income", f"${total_income:,.0f}")
    col3.metric("Net Income", f"${total_net:,.0f} ({(total_net/total_income*100 if total_income else 0):.1f}%)")
    
    # Staff Analytics
    st.markdown('<div class="section-header">👤 Staff Performance Analytics</div>', unsafe_allow_html=True)
    
    degree_order = ["Consultant", "Specialist", "Resident", "Other"]
    dept_df["Degree Group"] = pd.Categorical(dept_df["Degree Group"], categories=degree_order, ordered=True)
    staff_sorted_df = dept_df.sort_values(by="Degree Group")
    
    # Blue color scale for bars
    blue_scale_map = {"Consultant": "#1e3a8a", "Specialist": "#3b82f6", "Resident": "#93c5fd", "Other": "#e0f2fe"}

    # Dynamic Height Calculation (25px per staff member + buffer) to show ALL staff
    dynamic_height = max(400, 200 + (len(staff_sorted_df) * 25))

    tab1, tab2, tab3 = st.tabs(["🏥 Clinics", "⚕️ Operations", "💵 Financial"])
    
    with tab1:
        fig = px.bar(staff_sorted_df.sort_values("opened clinic", ascending=True), 
                     y="staff name", x="opened clinic", 
                     color="Degree Group", title="Clinics by Staff (All)", orientation='h',
                     color_discrete_map=blue_scale_map)
        fig.update_layout(height=dynamic_height)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = px.bar(staff_sorted_df.sort_values("Operation total number", ascending=True), 
                     y="staff name", x="Operation total number", 
                     color="Degree Group", title="Operations by Staff (All)", orientation='h',
                     color_discrete_map=blue_scale_map)
        fig.update_layout(height=dynamic_height)
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(x=["Elective", "Emergency"], y=[elective, emergency], title="Operations by Type", 
                         color=["Elective", "Emergency"], color_discrete_map={"Elective": "#1e3a8a", "Emergency": "#60a5fa"})
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(x=["High", "Moderate", "Low"], y=[high, moderate, low], title="Operations by Value",
                         color=["High", "Moderate", "Low"], color_discrete_map={"High": "#172554", "Moderate": "#2563eb", "Low": "#93c5fd"})
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        fig = px.bar(staff_sorted_df.sort_values("Net", ascending=True), 
                     y="staff name", x="Net",
                     color="Degree Group", title="Net Income by Staff (All)", orientation='h',
                     color_discrete_map=blue_scale_map)
        fig.update_layout(height=dynamic_height)
        st.plotly_chart(fig, use_container_width=True)
    
    # Data Tables
    st.markdown('<div class="section-header">📋 Detailed Tables</div>', unsafe_allow_html=True)
    
    perf_table = staff_sorted_df[["staff name", "degree", "total hours", "opened clinic", "Total visits", "Operation total number"]].copy()
    perf_table.columns = ["Staff Name", "Degree", "Total Hours", "Opened Clinics", "Total Visits", "Total Operations"]
    perf_table["Avg. Clinics"] = (perf_table["Opened Clinics"] / 10).round(2)
    perf_table["Avg. Operations"] = (perf_table["Total Operations"] / 10).round(2)
    
    st.markdown("### Overall Performance")
    st.dataframe(perf_table, use_container_width=True, hide_index=True)
    
    op_source_table = staff_sorted_df[["staff name", "degree", "opr_elective", "opr_emergency", "Operation total number"]].copy()
    op_source_table.columns = ["Staff Name", "Degree", "Elective", "Emergency", "Total Operations"]
    
    op_value_table = staff_sorted_df[["staff name", "degree", "opr_high", "opr_moderate", "opr_low", "Operation total number"]].copy()
    op_value_table.columns = ["Staff Name", "Degree", "High", "Moderate", "Low", "Total Operations"]
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Operation Source")
        st.dataframe(op_source_table, use_container_width=True, hide_index=True)
    with col2:
        st.markdown("### Operation Value")
        st.dataframe(op_value_table, use_container_width=True, hide_index=True)
    
    fin_table = staff_sorted_df[["staff name", "degree", "total slary", "total income", "Net"]].copy()
    fin_table.columns = ["Staff Name", "Degree", "Total Salary", "Total Income", "Net Income"]
    
    st.markdown("### Financial Performance")
    st.dataframe(fin_table, use_container_width=True, hide_index=True)
    
    # PDF Generation
    if st.button("📄 Generate PDF Report"):
        try:
            pdf_buffer = generate_pdf(dept_df, department, detailed_tables, perf_table, op_source_table, op_value_table, fin_table)
            st.download_button("📥 Download PDF", data=pdf_buffer, file_name=f"{department}_report.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"PDF generation failed: {e}")

else:
    st.info("📤 Please upload a CSV file to begin analysis")
