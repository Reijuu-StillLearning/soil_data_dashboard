import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Analisis Tanah", layout="wide")
st.title("Dashboard Analisis Tanah")


@st.cache_data
def load_data():
    
    return pd.read_excel("soil-2008-2021-all div.xlsx") 


df = load_data()
st.sidebar.header("Filter Data")
df_filtered = df.copy()


# 1. Filter pt 
opsi_estate = df['ESTATE_NAME'].dropna().unique()
estate = st.sidebar.selectbox("Pilih PT / Estate", opsi_estate)
df_filtered = df[df['ESTATE_NAME'] == estate] 

# 2. Filter divisi
opsi_divisi = df_filtered['DIVISION_NAME'].dropna().unique()
divisi = st.sidebar.selectbox("Pilih Divisi", opsi_divisi)
df_filtered = df_filtered[df_filtered['DIVISION_NAME'] == divisi]

# 3. Filter range tahun
min_year, max_year = int(df_filtered['S_YEAR'].min()), int(df_filtered['S_YEAR'].max())
rentang_tahun = st.sidebar.slider("Rentang Tahun", min_value=min_year, max_value=max_year, value=(min_year, max_year))
df_filtered = df_filtered[(df_filtered['S_YEAR'] >= rentang_tahun[0]) & (df_filtered['S_YEAR'] <= rentang_tahun[1])]

# 1. Filter E-Block
opsi_e_block = ["Semua Estate Block"] + list(df_filtered['E_BLOCK_NAME'].dropna().unique())
pilih_e_block = st.sidebar.selectbox("Pilih Estate Block (Opsional)", opsi_e_block)
if pilih_e_block != "Semua Estate Block":
    df_filtered = df_filtered[df_filtered['E_BLOCK_NAME'] == pilih_e_block]

# 2. Filter M-Block 
opsi_m_block = ["Semua Manuring Block"] + list(df_filtered['M_BLOCK_NAME'].dropna().unique())
pilih_m_block = st.sidebar.selectbox("Pilih Manuring Block (Opsional)", opsi_m_block)
if pilih_m_block != "Semua Manuring Block":
    df_filtered = df_filtered[df_filtered['M_BLOCK_NAME'] == pilih_m_block]

# B. Micro Filters 
opsi_sample = ["Semua Sample"] + list(df_filtered['SAMPLE_ID'].dropna().unique())
pilih_sample = st.sidebar.selectbox("Pilih Sample ID (Spesifik):", opsi_sample)

if pilih_sample != "Semua Sample":
    df_filtered = df_filtered[df_filtered['SAMPLE_ID'] == pilih_sample]
    
    col_area, col_depth = st.sidebar.columns(2)
    with col_area:
        pilih_area = st.selectbox("Area:", df_filtered['S_AREA'].dropna().unique())
    with col_depth:
        pilih_depth = st.selectbox("Depth:", df_filtered['S_DEPTH'].dropna().unique())
        
    df_filtered = df_filtered[(df_filtered['S_AREA'] == pilih_area) & (df_filtered['S_DEPTH'] == pilih_depth)]

# 2. Klasifikasi Data
labels_cat = ['Extremely Low', 'Very Low', 'Low', 'Marginal', 'Medium', 'High', 'Extremely high']
kriteria_soil = {
    'S_PH_H2O': [0.0, 3.5, 3.8, 4.0, 4.2, 5.5, 6.5, float('inf')],
    'S_ORG_C': [0.0, 0.8, 1.0, 1.2, 1.5, 2.5, 4.0, float('inf')],
    'S_N': [0.0, 0.08, 0.10, 0.12, 0.15, 0.25, 0.40, float('inf')],
    'S_P_TOTAL': [0.0, 120.0, 150.0, 200.0, 250.0, 400.0, 600.0, float('inf')],
    'S_EXCHG_K': [0.0, 0.08, 0.12, 0.20, 0.25, 0.30, 0.50, float('inf')],
    'S_EXCHG_MG': [0.0, 0.08, 0.12, 0.20, 0.25, 0.30, 0.61, float('inf')],
    'S_CEC': [0.0, 6.0, 9.0, 12.0, 15.0, 18.0, 20.0, float('inf')]
}

bins_ir = [0.0, 8.0, 11.0, 15.0, 20.0, 25.0, 40.0, float('inf')]
bins_pc = [0.0, 10.0, 20.0, 30.0, 40.0, 60.0, 100.0, float('inf')]
# Batch klasifikasi
for col, bins in kriteria_soil.items():
    if col in df_filtered.columns:
        df_filtered[f'{col}_Class'] = pd.cut(df_filtered[col], bins=bins, labels=labels_cat)

# kondisional klasifikasi area
if 'S_P_AVAILABLE' in df_filtered.columns and 'S_AREA' in df_filtered.columns:
   
    
    mask_ir = df_filtered['S_AREA'] == 'IR'
    mask_pc = df_filtered['S_AREA'] == 'PC'
    df_filtered.loc[mask_ir, 'S_P_AVAILABLE_Class'] = pd.cut(df_filtered.loc[mask_ir, 'S_P_AVAILABLE'], bins=bins_ir, labels=labels_cat)
    df_filtered.loc[mask_pc, 'S_P_AVAILABLE_Class'] = pd.cut(df_filtered.loc[mask_pc, 'S_P_AVAILABLE'], bins=bins_pc, labels=labels_cat)

# 3. ui 
def render_kpi(col, label, value, category):
    cat = str(category)
    if cat in ['Extremely Low', 'Very Low', 'Low']:
        col.metric(label, value, f"- {cat}", delta_color="normal")
    elif cat in ['High', 'Extreme', 'Extremely high']:
        col.metric(label, value, f"{cat}", delta_color="inverse")
    elif cat in ['Marginal', 'Medium']:
        col.metric(label, value, f"{cat}", delta_color="normal")
    else:
        col.metric(label, value, cat, delta_color="off")

if pilih_sample == "Semua Sample":

    # KPI metric
    st.markdown("#### Population Nutrient Summary (Mean)")
    
    # 1. filter KPI
    col_kpi_area, col_kpi_depth = st.columns(2)
    with col_kpi_area:
        kpi_area = st.selectbox("Area KPI:", ['PC', 'IR'], index=0)
    with col_kpi_depth:
        opsi_depth_bersih = ['0-15', '15-45'] 
        kpi_depth = st.selectbox("Kedalaman KPI:", opsi_depth_bersih, index=0)

    df_kpi = df_filtered[
        (df_filtered['S_AREA'].str.strip().str.upper() == kpi_area) & 
        (df_filtered['S_DEPTH'].astype(str).str.contains(kpi_depth.split('-')[0]))
    ]

    # numeric
    df_kpi_numeric = df_kpi.select_dtypes(include=['number'])
    def get_mean_class_kpi(col_name, bins):
        mean_val = df_kpi_numeric[col_name].mean() if col_name in df_kpi_numeric.columns else float('nan')
        if pd.isna(mean_val) or len(df_kpi) == 0: 
            return "NaN", "-"
        
        try:
            cat = pd.cut([mean_val], bins=bins, labels=labels_cat)[0]
            return round(mean_val, 2), str(cat)
        except:
            return round(mean_val, 2), "-"

    mean_ph, cat_ph = get_mean_class_kpi('S_PH_H2O', kriteria_soil['S_PH_H2O'])
    bins_p_aktif = bins_pc if kpi_area == 'PC' else bins_ir
    mean_p, cat_p = get_mean_class_kpi('S_P_AVAILABLE', bins_p_aktif)
    
    mean_k, cat_k = get_mean_class_kpi('S_EXCHG_K', kriteria_soil['S_EXCHG_K'])
    mean_mg, cat_mg = get_mean_class_kpi('S_EXCHG_MG', kriteria_soil['S_EXCHG_MG'])

    colA, colB, colC, colD = st.columns(4)
    render_kpi(colA, "Rata-rata pH", mean_ph, cat_ph)
    render_kpi(colB, "Fosfor (Avail P)", f"{mean_p} ppm" if mean_p != "NaN" else "NaN", cat_p)
    render_kpi(colC, "Kalium (Exch K)", f"{mean_k} me%" if mean_k != "NaN" else "NaN", cat_k)
    render_kpi(colD, "Magnesium (Mg)", f"{mean_mg} me%" if mean_mg != "NaN" else "NaN", cat_mg)

    st.caption(f"*Nilai KPI dihitung dari **{len(df_kpi)}** titik sampel.*")
    
    st.divider()



    # Tren anailisis
    st.subheader("Tren Rata-rata Indikator Tanah")
    
    # pilih feature
    opsi_trend = {
        'pH Level (H2O)': 'S_PH_H2O', 
        'Nitrogen (N)': 'S_N', 
        'Fosfor (Avail P)': 'S_P_AVAILABLE',
        'Karbon Organik': 'S_ORG_C', 
        'Kalium (Exch K)': 'S_EXCHG_K', 
        'Kapasitas Tukar Kation (CEC)': 'S_CEC'
    }
    pilih_trend = st.selectbox("Pilih Feature untuk Dianalisis:", list(opsi_trend.keys()))
    kolom_trend = opsi_trend[pilih_trend]
    
    # tren berdasarkan tahun
    if kolom_trend in df_filtered.columns:
        df_trend = df_filtered.groupby('S_YEAR')[kolom_trend].mean().reset_index()
        
        # line chart
        fig_trend = px.line(
            df_trend, 
            x='S_YEAR', 
            y=kolom_trend, 
            markers=True, 
            title=f"Pergerakan Rata-rata {pilih_trend} per Tahun",
            labels={'S_YEAR': 'Tahun', kolom_trend: f'Nilai {pilih_trend}'}
        )
        fig_trend.update_xaxes(dtick=1) 
        st.plotly_chart(fig_trend, use_container_width=True)

    # Heatmap korelasi 
    st.subheader(f"Heatmap Korelasi (Area {kpi_area} | Kedalaman {kpi_depth})")
    
    drop_cols_heatmap = ['ESTATE_ID', 'DIVISION_ID', 'E_BLOCK_ID', 'M_BLOCK_ID', 'SAMPLE_ID', 'S_YEAR']
    df_heatmap = df_kpi.select_dtypes(include=['number']).drop(columns=drop_cols_heatmap, errors='ignore')

    if not df_heatmap.empty and len(df_heatmap) > 1:
        feature_labels = {
            'S_PH_H2O': 'pH tanah (H₂O)', 
            'S_N': 'Nitrogen (N)', 
            'S_P_AVAILABLE': 'Fosfor (P)', 
            'S_ORG_C': 'Karbon organik', 
            'S_EXCHG_K': 'Kalium',
            'S_EXCHG_MG': 'Magnesium' 
        }
        
        df_heatmap_labeled = df_heatmap.rename(columns={col: feature_labels.get(col, col.removeprefix("S_").replace("_", " ").title()) for col in df_heatmap.columns})
        
        fig_corr = px.imshow(df_heatmap_labeled.corr(), text_auto=".1f", aspect="auto", color_continuous_scale='RdBu_r') # type: ignore
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.warning(f"Data tidak cukup untuk merender Correlation Heatmap pada Area {kpi_area} Kedalaman {kpi_depth}.")

    # Data Record
    st.subheader("Data Record")
    kolom_esensial = [
        'S_YEAR', 'S_DATE', 'E_BLOCK_NAME', 'M_BLOCK_NAME', 
        'SAMPLE_ID', 'S_AREA', 'S_DEPTH'
    ] + [col for col in df_filtered.columns if '_Class' in col]

    st.dataframe(df_filtered[kolom_esensial], use_container_width=True, hide_index=True)

else:
    # Single Row
    st.subheader(f"Soil Profile Record: {pilih_sample}")
    
    if len(df_filtered) > 0:
        row_data = df_filtered.iloc[0] 
        
        def clean_metric(val, suffix=""):
            return "NaN" if pd.isna(val) else f"{round(val, 2)}{suffix}"

        col1, col2, col3 = st.columns(3)
        render_kpi(col1, "pH Level", clean_metric(row_data.get('S_PH_H2O')), row_data.get('S_PH_H2O_Class'))
        render_kpi(col2, "Nitrogen (N)", clean_metric(row_data.get('S_N'), " %"), row_data.get('S_N_Class'))
        render_kpi(col3, "Fosfor (Avail P)", clean_metric(row_data.get('S_P_AVAILABLE')), row_data.get('S_P_AVAILABLE_Class'))

        col4, col5, col6 = st.columns(3)
        render_kpi(col4, "Kalium (Exch K)", clean_metric(row_data.get('S_EXCHG_K'), " %"), row_data.get('S_EXCHG_K_Class', '-'))
        render_kpi(col5, "Magnesium (Exch Mg)", clean_metric(row_data.get('S_EXCHG_MG'), " %"), row_data.get('S_EXCHG_MG_Class', '-'))
        render_kpi(col6, "Kapasitas Tukar Kation (CEC)", clean_metric(row_data.get('S_CEC')), row_data.get('S_CEC_Class', '-'))
    else:
        st.warning("Kombinasi Area dan Depth tidak memiliki data observasi.")

#download
st.subheader("Data Export")

st.download_button(
    label="Export CSV",
    data=df_filtered.to_csv(index=False).encode('utf-8'),
    file_name="soil_metrics_terfilter.csv",
    mime='text/csv',
)
