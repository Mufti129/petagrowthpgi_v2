import pandas as pd
import folium
from folium.plugins import HeatMap, GroupedLayerControl
import streamlit as st
from streamlit_folium import st_folium

# ==============================================================================
# CONFIG CONFIGURATION UTAMA STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="Dashboard Analisis Omzet & Growth Cabang",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Dashboard Geospasial: Analisis Determinasi & Growth Omzet")
st.markdown("Visualisasi sebaran cabang berdasarkan berbagai metode segmentasi statistik.")

# ==============================================================================
# 1. PENGAMBILAN DATA LOKAL (Repository GitHub yang Sama)
# ==============================================================================
CSV_FILE_PATH = "df_persen_growth.csv"

@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        if 'Persen Growth' in df.columns:
            df['Persen Growth'] = pd.to_numeric(df['Persen Growth'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Gagal memuat file '{file_path}'. Pastikan file berada di folder yang sama dengan app.py. Error: {e}")
        return None

df_clean = load_data(CSV_FILE_PATH)

if df_clean is not None:
    color_map = {
        'baik': 'green', 'tinggi': 'green', 'extreme high': 'darkgreen', 'ekstrem (superstar)': 'darkgreen',
        'sedang': 'orange', 'extreme': 'darkgreen', 'sangat baik': 'blue',
        'jelek': 'red', 'rendah': 'red', 'extreme low': 'darkred', 'kurang baik': 'pink'
    }

    # ==============================================================================
    # 2. INISIALISASI PETA FOLIUM (OPENSTREETMAP)
    # ==============================================================================
    lat_center = df_clean['latitude_cabang'].mean() if 'latitude_cabang' in df_clean.columns else -6.2088
    lon_center = df_clean['longitude_cabang'].mean() if 'longitude_cabang' in df_clean.columns else 106.8456

    m = folium.Map(location=[lat_center, lon_center], zoom_start=11)

    fg_heatmap = folium.FeatureGroup(name='Glow Heatmap Growth', show=True)
    if 'Growth' in df_clean.columns:
        heat_data = [[row['latitude_cabang'], row['longitude_cabang'], row['Growth']] for i, row in df_clean.iterrows()]
    else:
        heat_data = [[row['latitude_cabang'], row['longitude_cabang'], row['Persen Growth']] for i, row in df_clean.iterrows()]
        
    HeatMap(heat_data, radius=15, blur=20, gradient={0.4: 'blue', 0.7: 'lime', 1: 'yellow'}).add_to(fg_heatmap)
    fg_heatmap.add_to(m)

    # ==============================================================================
    # 3. DEKLARASI FEATURE GROUP MANUALLY
    # ==============================================================================
    fg_std_sedang = folium.FeatureGroup(name="StdDev - Sedang", show=False)
    fg_std_tinggi = folium.FeatureGroup(name="StdDev - Tinggi", show=False)

    fg_pct_rendah = folium.FeatureGroup(name="Percentile - Rendah", show=False)
    fg_pct_sedang = folium.FeatureGroup(name="Percentile - Sedang", show=False)
    fg_pct_tinggi = folium.FeatureGroup(name="Percentile - Tinggi", show=False)

    fg_ats_sangat_baik = folium.FeatureGroup(name="Atasan - Sangat Baik", show=False)
    fg_ats_baik = folium.FeatureGroup(name="Atasan - Baik", show=False)
    fg_ats_kurang_baik = folium.FeatureGroup(name="Atasan - Kurang Baik", show=False)
    fg_ats_jelek = folium.FeatureGroup(name="Atasan - Jelek", show=False)

    fg_hib_super = folium.FeatureGroup(name="Hibrida - Ekstrem (Superstar)", show=False)
    fg_hib_rendah = folium.FeatureGroup(name="Hibrida - Rendah", show=False)
    fg_hib_sedang = folium.FeatureGroup(name="Hibrida - Sedang", show=False)
    fg_hib_tinggi = folium.FeatureGroup(name="Hibrida - Tinggi", show=False)

    fg_z_extreme = folium.FeatureGroup(name="ZScore - Extreme", show=False)
    fg_z_baik = folium.FeatureGroup(name="ZScore - Baik", show=False)
    fg_z_sedang = folium.FeatureGroup(name="ZScore - Sedang", show=False)

    fg_iqr_exhigh = folium.FeatureGroup(name="IQR - Extreme High", show=False)
    fg_iqr_rendah = folium.FeatureGroup(name="IQR - Rendah", show=False)
    fg_iqr_sedang = folium.FeatureGroup(name="IQR - Sedang", show=False)
    fg_iqr_tinggi = folium.FeatureGroup(name="IQR - Tinggi", show=False)

    all_fgs = [
        fg_std_sedang, fg_std_tinggi,
        fg_pct_rendah, fg_pct_sedang, fg_pct_tinggi,
        fg_ats_sangat_baik, fg_ats_baik, fg_ats_kurang_baik, fg_ats_jelek,
        fg_hib_super, fg_hib_rendah, fg_hib_sedang, fg_hib_tinggi,
        fg_z_extreme, fg_z_baik, fg_z_sedang,
        fg_iqr_exhigh, fg_iqr_rendah, fg_iqr_sedang, fg_iqr_tinggi
    ]
    for fg in all_fgs:
        fg.add_to(m)

    # ==============================================================================
    # 4. PLOTTING MARKER CABANG KE FEATURE GROUP
    # ==============================================================================
    for i, row in df_clean.iterrows():
        popup_content = (
            f"<div style='font-family: Arial, sans-serif; width: 220px;'>"
            f"  <h4 style='margin:0 0 5px 0; color:#333;'>Cabang: {row.get('cabang', '-')}</h4>"
            f"  <hr style='margin:5px 0; border:0; border-top:1px solid #eee;'>"
            f"  <b>Lama Beroperasi:</b> {row.get('lama_buka_bulan', '-')} bulan<br>"
            f"  <b>Omset Jan25:</b> Rp {int(row.get('Omset Jan25', 0)):,}<br>"
            f"  <b>Omset Mei26:</b> Rp {int(row.get('Omset Mei26', 0)):,}<br>"
            f"  <b>Persen Growth:</b> {row.get('Persen Growth', 0) * 100:.2f}%<br>"
            f"  <hr style='margin:5px 0; border:0; border-top:1px solid #eee;'>"
            f"  <b>Kategori IQR:</b> {row.get('Kategori_IQR', '-')}<br>"
            f"  <b>Kategori StdDev:</b> {row.get('Kategori_By_StdDev', '-')}<br>"
            f"  <b>Kategori Percentile:</b> {row.get('Kategori_By_Percentile', '-')}<br>"
            f"  <b>Kategori Atasan:</b> {row.get('Kategori_Atasan', '-')}<br>"
            f"  <b>Kategori Hibrida:</b> {row.get('Kategori_Hibrida', '-')}<br>"
            f"  <b>Kategori Z-Score:</b> {row.get('Kategori_ZScore', '-')}"
            f"</div>"
        )

        def buat_marker(warna_kat):
            return folium.CircleMarker(
                location=[row['latitude_cabang'], row['longitude_cabang']],
                radius=6,
                color=color_map.get(str(warna_kat).strip().lower(), 'gray'),
                fill=True,
                fill_opacity=0.8,
                popup=folium.Popup(popup_content, max_width=250)
            )

        # Distribusi ke Layer Masing-masing
        val_std = row.get('Kategori_By_StdDev')
        if val_std == 'Sedang': buat_marker(val_std).add_to(fg_std_sedang)
        elif val_std == 'Tinggi': buat_marker(val_std).add_to(fg_std_tinggi)

        val_pct = row.get('Kategori_By_Percentile')
        if val_pct == 'Rendah': buat_marker(val_pct).add_to(fg_pct_rendah)
        elif val_pct == 'Sedang': buat_marker(val_pct).add_to(fg_pct_sedang)
        elif val_pct == 'Tinggi': buat_marker(val_pct).add_to(fg_pct_tinggi)

        val_ats = row.get('Kategori_Atasan')
        if val_ats == 'Sangat Baik': buat_marker(val_ats).add_to(fg_ats_sangat_baik)
        elif val_ats == 'Baik': buat_marker(val_ats).add_to(fg_ats_baik)
        elif val_ats == 'Kurang Baik': buat_marker(val_ats).add_to(fg_ats_kurang_baik)
        elif val_ats == 'Jelek': buat_marker(val_ats).add_to(fg_ats_jelek)

        val_hib = row.get('Kategori_Hibrida')
        if val_hib == 'Ekstrem (Superstar)': buat_marker(val_hib).add_to(fg_hib_super)
        elif val_hib == 'Rendah': buat_marker(val_hib).add_to(fg_hib_rendah)
        elif val_hib == 'Sedang': buat_marker(val_hib).add_to(fg_hib_sedang)
        elif val_hib == 'Tinggi': buat_marker(val_hib).add_to(fg_hib_tinggi)

        val_z = row.get('Kategori_ZScore')
        if val_z == 'Extreme': buat_marker(val_z).add_to(fg_z_extreme)
        elif val_z == 'Baik': buat_marker(val_z).add_to(fg_z_baik)
        elif val_z == 'Sedang': buat_marker(val_z).add_to(fg_z_sedang)

        val_iqr = row.get('Kategori_IQR')
        if val_iqr == 'Extreme High': buat_marker(val_iqr).add_to(fg_iqr_exhigh)
        elif val_iqr == 'Rendah': buat_marker(val_iqr).add_to(fg_iqr_rendah)
        elif val_iqr == 'Sedang': buat_marker(val_iqr).add_to(fg_iqr_sedang)
        elif val_iqr == 'Tinggi': buat_marker(val_iqr).add_to(fg_iqr_tinggi)

    # ==============================================================================
    # 5. CONFIG LAYERS MENU (KANAN ATAS - COLLAPSED MODE)
    # ==============================================================================
    grouped_overlays = {
        "Metode Statistik Dasar": [fg_heatmap],
        "Metode 1: Standar Deviasi": [fg_std_sedang, fg_std_tinggi],
        "Metode 2: Percentile Binning": [fg_pct_rendah, fg_pct_sedang, fg_pct_tinggi],
        "Metode 3: Kategori Atasan (KPI)": [fg_ats_sangat_baik, fg_ats_baik, fg_ats_kurang_baik, fg_ats_jelek],
        "Metode 4: Hibrida Superstar": [fg_hib_super, fg_hib_rendah, fg_hib_sedang, fg_hib_tinggi],
        "Metode 6: Kategori Z-Score": [fg_z_extreme, fg_z_baik, fg_z_sedang],
        "Metode 7: Rentang IQR": [fg_iqr_exhigh, fg_iqr_rendah, fg_iqr_sedang, fg_iqr_tinggi],
    }

    GroupedLayerControl(
        grouped_overlays,
        exclusive_groups=False,  
        collapsed=True,          
        position='topright'
    ).add_to(m)

    # Kotak Legenda Warna Statis HTML
    legend_html = '''
         <div style="position: fixed;
                     bottom: 50px; left: 70px; width: 230px; height: auto;
                     border:2px solid #ccc; z-index:9999; font-size:11px;
                     background-color:white; opacity:0.95; padding: 10px;
                     font-family: Arial, sans-serif; border-radius: 6px;
                     box-shadow: 2px 2px 6px rgba(0,0,0,0.2);">
           <b style="font-size:12px; color:#333;">Panduan Warna Penanda:</b><br>
           <div style="margin-top:4px;"><i style="background:darkgreen; width:10px; height:10px; float:left; margin-right:8px; border-radius:50%;"></i><b>Extreme / Superstar</b></div>
           <div style="margin-top:4px;"><i style="background:blue; width:10px; height:10px; float:left; margin-right:8px; border-radius:50%;"></i><b>Sangat Baik (Atasan)</b></div>
           <div style="margin-top:4px;"><i style="background:green; width:10px; height:10px; float:left; margin-right:8px; border-radius:50%;"></i><b>Baik / Tinggi</b></div>
           <div style="margin-top:4px;"><i style="background:orange; width:10px; height:10px; float:left; margin-right:8px; border-radius:50%;"></i><b>Sedang</b></div>
           <div style="margin-top:4px;"><i style="background:pink; width:10px; height:10px; float:left; margin-right:8px; border-radius:50%;"></i><b>Kurang Baik</b></div>
           <div style="margin-top:4px;"><i style="background:red; width:10px; height:10px; float:left; margin-right:8px; border-radius:50%;"></i><b>Rendah / Jelek / Low</b></div>
           <hr style="margin:6px 0; border:0; border-top:1px solid #ddd;">
           <b>Glow Heatmap:</b> Akumulasi Volume Growth.
         </div>
         '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # ==============================================================================
    # 6. RENDER INDUK PETA DI STREAMLIT
    # ==============================================================================
    st.subheader("🗺️ Peta Distribusi Finansial & Geografis")
    st_folium(m, width="100%", height=600, returned_objects=[])

    # ==============================================================================
    # 7. PREVIEW DATABASE (DENGAN FITUR SHOW/HIDE INTERAKTIF)
    # ==============================================================================
    st.markdown("---")
    st.subheader("📋 Preview Dataset Master Terintegrasi")
    
    show_preview = st.toggle("Tampilkan Preview Tabel Data", value=False)

    if show_preview:
        search_query = st.text_input("🔍 Cari berdasarkan Nama Cabang:", "")
        if search_query:
            df_display = df_clean[df_clean['cabang'].str.contains(search_query, case=False, na=False)]
        else:
            df_display = df_clean

        st.write(f"Menampilkan {len(df_display)} dari total {len(df_clean)} data cabang.")
        
        st.dataframe(
            df_display, 
            use_container_width=True,
            column_config={
                "Omset Jan25": st.column_config.NumberColumn(format="Rp %',d"),
                "Omset Mei26": st.column_config.NumberColumn(format="Rp %',d"),
                "Persen Growth": st.column_config.NumberColumn(format="%.2f%%"),
            }
        )
    else:
        st.info("💡 Klik tombol toggle di atas jika ingin menampilkan preview tabel data cabang.")

    # ==============================================================================
    # 8. SUMMARY STATISTIK METODE SEGMENTASI
    # ==============================================================================
    st.markdown("---")
    st.header("📈 Summary Distribusi & Batasan Metode")
    
    # Indikator Total Populasi Utama
    st.subheader("=== TOTAL POPULASI DATA: 1157 CABANG ===")

    # Membuat Komponen Tab di Streamlit agar Tampilan Ringkas & Profesional
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "StdDev", "Percentile", "Atasan (KPI)", "Hibrida", "Z-Score", "IQR"
    ])

    with tab1:
        st.markdown("#### 📌 SUMMARY METODE: Standar Deviasi")
        df_std = pd.DataFrame([
            {"Nama Kategori": "Sedang", "Kriteria Batasan": "-42.17% s/d 345.94%", "Jumlah Cabang": 1125, "Persentase (%)": "97.23%"},
            {"Nama Kategori": "Tinggi", "Kriteria Batasan": "355.18% s/d 13007.41%", "Jumlah Cabang": 32, "Persentase (%)": "2.77%"}
        ])
        st.table(df_std)

    with tab2:
        st.markdown("#### 📌 SUMMARY METODE: Percentile")
        df_pct = pd.DataFrame([
            {"Nama Kategori": "Sedang", "Kriteria Batasan": "3.47% s/d 71.99%", "Jumlah Cabang": 578, "Persentase (%)": "49.96%"},
            {"Nama Kategori": "Rendah", "Kriteria Batasan": "-42.17% s/d 3.42%", "Jumlah Cabang": 290, "Persentase (%)": "25.06%"},
            {"Nama Kategori": "Tinggi", "Kriteria Batasan": "72.7% s/d 13007.41%", "Jumlah Cabang": 289, "Persentase (%)": "24.98%"}
        ])
        st.table(df_pct)

    with tab3:
        st.markdown("#### 📌 SUMMARY METODE: Atasan (KPI)")
        df_ats = pd.DataFrame([
            {"Nama Kategori": "Sangat Baik", "Kriteria Batasan": "35.2% s/d 13007.41%", "Jumlah Cabang": 505, "Persentase (%)": "43.65%"},
            {"Nama Kategori": "Baik", "Kriteria Batasan": "0.0% s/d 34.88%", "Jumlah Cabang": 479, "Persentase (%)": "41.40%"},
            {"Nama Kategori": "Kurang Baik", "Kriteria Batasan": "-33.34% s/d -0.04%", "Jumlah Cabang": 169, "Persentase (%)": "14.61%"},
            {"Nama Kategori": "Jelek", "Kriteria Batasan": "-42.17% s/d -35.3%", "Jumlah Cabang": 4, "Persentase (%)": "0.35%"}
        ])
        st.table(df_ats)

    with tab4:
        st.markdown("#### 📌 SUMMARY METODE: Hibrida")
        df_hib = pd.DataFrame([
            {"Nama Kategori": "Sedang", "Kriteria Batasan": "10.34% s/d 48.14%", "Jumlah Cabang": 381, "Persentase (%)": "32.93%"},
            {"Nama Kategori": "Tinggi", "Kriteria Batasan": "48.32% s/d 910.06%", "Jumlah Cabang": 380, "Persentase (%)": "32.84%"},
            {"Nama Kategori": "Rendah", "Kriteria Batasan": "-42.17% s/d 10.26%", "Jumlah Cabang": 380, "Persentase (%)": "32.84%"},
            {"Nama Kategori": "Ekstrem (Superstar)", "Kriteria Batasan": "1014.98% s/d 13007.41%", "Jumlah Cabang": 16, "Persentase (%)": "1.38%"}
        ])
        st.table(df_hib)

    with tab5:
        st.markdown("#### 📌 SUMMARY METODE: Z-Score")
        df_z = pd.DataFrame([
            {"Nama Kategori": "Sedang", "Kriteria Batasan": "-42.17% s/d 345.94%", "Jumlah Cabang": 1125, "Persentase (%)": "97.23%"},
            {"Nama Kategori": "Baik", "Kriteria Batasan": "355.18% s/d 1577.42%", "Jumlah Cabang": 23, "Persentase (%)": "1.99%"},
            {"Nama Kategori": "Extreme", "Kriteria Batasan": "1690.89% s/d 13007.41%", "Jumlah Cabang": 9, "Persentase (%)": "0.78%"}
        ])
        st.table(df_z)

    with tab6:
        st.markdown("#### 📌 SUMMARY METODE: IQR (Interquartile Range)")
        df_iqr = pd.DataFrame([
            {"Nama Kategori": "Sedang", "Kriteria Batasan": "3.47% s/d 71.36%", "Jumlah Cabang": 577, "Persentase (%)": "49.87%"},
            {"Nama Kategori": "Rendah", "Kriteria Batasan": "-42.17% s/d 3.42%", "Jumlah Cabang": 290, "Persentase (%)": "25.06%"},
            {"Nama Kategori": "Tinggi", "Kriteria Batasan": "71.99% s/d 183.28%", "Jumlah Cabang": 203, "Persentase (%)": "17.55%"},
            {"Nama Kategori": "Extreme High", "Kriteria Batasan": "184.55% s/d 13007.41%", "Jumlah Cabang": 87, "Persentase (%)": "7.52%"}
        ])
        st.table(df_iqr)
