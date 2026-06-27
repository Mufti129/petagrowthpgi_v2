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

st.title("Dashboard Geospasial: Analisis Determinasi & Growth Omzet")
st.markdown("Visualisasi sebaran cabang berdasarkan berbagai metode segmentasi statistik.")

# ==============================================================================
# 1. PENGAMBILAN DATA LOKAL (Repository GitHub yang Sama)
# ==============================================================================
CSV_FILE_PATH = "df_dummy.csv"

@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        if 'Persen Growth' in df.columns:
            df['Persen Growth'] = pd.to_numeric(df['Persen Growth'], errors='coerce').fillna(0)
            
        # Membuat Kolom Kategori_Final secara dinamis berdasarkan standar batas pertumbuhan riil
        if 'Kategori_Final' not in df.columns and 'Persen Growth' in df.columns:
            def hitung_kategori_final(growth):
                if growth >= 70: return "Outstanding"
                elif growth >= 20: return "High Performer"
                elif growth >= 0: return "Average"
                elif growth >= -30: return "Underperformer"
                else: return "Critical"
            df['Kategori_Final'] = df['Persen Growth'].apply(hitung_kategori_final)
            
        return df
    except Exception as e:
        st.error(f"Gagal memuat file '{file_path}'. Pastikan file berada di folder yang sama dengan app.py. Error: {e}")
        return None

df_clean = load_data(CSV_FILE_PATH)

if df_clean is not None:
    # Peta warna berdasarkan teks kategori riil yang ada di Sheet
    color_map = {
        'sedang': 'orange', 'tinggi': 'green', 'rendah': 'red',
        'sangat baik': 'darkgreen', 'baik': 'green', 'cukup': 'orange', 'kurang': 'red',
        'normal': 'orange', 'extreme high': 'darkgreen',
        # Warna khusus Kategori_Final
        'outstanding': 'darkgreen', 'high performer': 'green', 'average': 'orange', 
        'underperformer': 'pink', 'critical': 'red'
    }

    # ==============================================================================
    # 2. INISIALISASI PETA FOLIUM (OPENSTREETMAP)
    # ==============================================================================
    lat_center = df_clean['latitude_cabang'].mean() if 'latitude_cabang' in df_clean.columns else -6.2088
    lon_center = df_clean['longitude_cabang'].mean() if 'longitude_cabang' in df_clean.columns else 106.8456

    m = folium.Map(location=[lat_center, lon_center], zoom_start=11)

    fg_heatmap = folium.FeatureGroup(name='Glow Heatmap Growth', show=True)
    heat_data = [[row['latitude_cabang'], row['longitude_cabang'], row['Persen Growth']] for i, row in df_clean.iterrows()]
        
    HeatMap(heat_data, radius=15, blur=20, gradient={0.4: 'blue', 0.7: 'lime', 1: 'yellow'}).add_to(fg_heatmap)
    fg_heatmap.add_to(m)

    # ==============================================================================
    # 3. DEKLARASI FEATURE GROUP SINKRON DENGAN GOOGLE SHEETS & KATEGORI FINAL
    # ==============================================================================
    # Master Standardisasi Baru: Kategori_Final
    fg_fin_outstanding = folium.FeatureGroup(name="Final - Outstanding", show=True)
    fg_fin_high = folium.FeatureGroup(name="Final - High Performer", show=False)
    fg_fin_average = folium.FeatureGroup(name="Final - Average", show=False)
    fg_fin_under = folium.FeatureGroup(name="Final - Underperformer", show=False)
    fg_fin_critical = folium.FeatureGroup(name="Final - Critical", show=False)

    # 1. Kategori_By_StdDev
    fg_std_sedang = folium.FeatureGroup(name="StdDev - Sedang", show=False)
    fg_std_tinggi = folium.FeatureGroup(name="StdDev - Tinggi", show=False)

    # 2. Kategori_Percentile
    fg_pct_rendah = folium.FeatureGroup(name="Percentile - Rendah", show=False)
    fg_pct_sedang = folium.FeatureGroup(name="Percentile - Sedang", show=False)
    fg_pct_tinggi = folium.FeatureGroup(name="Percentile - Tinggi", show=False)

    # 3. Kategori_KPI_Atasan
    fg_kpi_sangat_baik = folium.FeatureGroup(name="KPI Atasan - Sangat Baik", show=False)
    fg_kpi_baik = folium.FeatureGroup(name="KPI Atasan - Baik", show=False)
    fg_kpi_cukup = folium.FeatureGroup(name="KPI Atasan - Cukup", show=False)
    fg_kpi_kurang = folium.FeatureGroup(name="KPI Atasan - Kurang", show=False)

    # 4. Kategori_ZScore
    fg_z_normal = folium.FeatureGroup(name="ZScore - Normal", show=False)

    # 5. Kategori_IQR
    fg_iqr_normal = folium.FeatureGroup(name="IQR - Normal", show=False)
    fg_iqr_exhigh = folium.FeatureGroup(name="IQR - Extreme High", show=False)

    all_fgs = [
        fg_fin_outstanding, fg_fin_high, fg_fin_average, fg_fin_under, fg_fin_critical,
        fg_std_sedang, fg_std_tinggi,
        fg_pct_rendah, fg_pct_sedang, fg_pct_tinggi,
        fg_kpi_sangat_baik, fg_kpi_baik, fg_kpi_cukup, fg_kpi_kurang,
        fg_z_normal,
        fg_iqr_normal, fg_iqr_exhigh
    ]
    for fg in all_fgs:
        fg.add_to(m)

    # ==============================================================================
    # 4. PLOTTING MARKER CABANG KE FEATURE GROUP
    # ==============================================================================
    for i, row in df_clean.iterrows():
        persen_growth_val = row.get('Persen Growth', 0)
        
        popup_content = (
            f"<div style='font-family: Arial, sans-serif; width: 250px;'>"
            f"  <h4 style='margin:0 0 5px 0; color:#1a73e8;'>Cabang: {row.get('cabang', '-')}</h4>"
            f"  <hr style='margin:5px 0; border:0; border-top:1px solid #eee;'>"
            f"  <b>Omset Jan25:</b> Rp {int(row.get('Omset Jan25', 0)):,}<br>"
            f"  <b>Omset Jan26:</b> Rp {int(row.get('Omset Jan26', 0)):,}<br>"
            f"  <b>Persen Growth:</b> {persen_growth_val:.2f}%<br>"
            f"  <hr style='margin:5px 0; border:0; border-top:2px solid #1a73e8;'>"
            f"  <span style='font-size:12px;color:#1a73e8;'><b>★ KATEGORI FINAL: {row.get('Kategori_Final', '-')}</b></span><br>"
            f"  <hr style='margin:5px 0; border:0; border-top:1px solid #eee;'>"
            f"  <b>Kategori StdDev:</b> {row.get('Kategori_By_StdDev', '-')}<br>"
            f"  <b>Kategori Percentile:</b> {row.get('Kategori_Percentile', '-')}<br>"
            f"  <b>Kategori KPI Atasan:</b> {row.get('Kategori_Atasan', row.get('Kategori_KPI_Atasan', '-'))}<br>"
            f"  <b>Kategori Z-Score:</b> {row.get('Kategori_ZScore', '-')}<br>"
            f"  <b>Kategori IQR:</b> {row.get('Kategori_IQR', '-')}"
            f"</div>"
        )

        def buat_marker(warna_kat):
            return folium.CircleMarker(
                location=[row['latitude_cabang'], row['longitude_cabang']],
                radius=6,
                color=color_map.get(str(warna_kat).strip().lower(), 'gray'),
                fill=True,
                fill_opacity=0.8,
                popup=folium.Popup(popup_content, max_width=270)
            )

        # 0. Distribusi Layer Baru Kategori_Final
        val_final = str(row.get('Kategori_Final', '')).strip()
        if val_final == 'Outstanding': buat_marker(val_final).add_to(fg_fin_outstanding)
        elif val_final == 'High Performer': buat_marker(val_final).add_to(fg_fin_high)
        elif val_final == 'Average': buat_marker(val_final).add_to(fg_fin_average)
        elif val_final == 'Underperformer': buat_marker(val_final).add_to(fg_fin_under)
        elif val_final == 'Critical': buat_marker(val_final).add_to(fg_fin_critical)

        # 1. Distribusi Kategori_By_StdDev
        val_std = str(row.get('Kategori_By_StdDev', '')).strip()
        if val_std == 'Sedang': buat_marker(val_std).add_to(fg_std_sedang)
        elif val_std == 'Tinggi': buat_marker(val_std).add_to(fg_std_tinggi)

        # 2. Distribusi Kategori_Percentile
        val_pct = str(row.get('Kategori_Percentile', '')).strip()
        if val_pct == 'Rendah': buat_marker(val_pct).add_to(fg_pct_rendah)
        elif val_pct == 'Sedang': buat_marker(val_pct).add_to(fg_pct_sedang)
        elif val_pct == 'Tinggi': buat_marker(val_pct).add_to(fg_pct_tinggi)

        # 3. Distribusi Kategori_Atasan / KPI Atasan
        val_kpi = str(row.get('Kategori_Atasan', row.get('Kategori_KPI_Atasan', ''))).strip()
        if val_kpi == 'Sangat Baik': buat_marker(val_kpi).add_to(fg_kpi_sangat_baik)
        elif val_kpi == 'Baik': buat_marker(val_kpi).add_to(fg_kpi_baik)
        elif val_kpi == 'Cukup': buat_marker(val_kpi).add_to(fg_kpi_cukup)
        elif val_kpi == 'Kurang': buat_marker(val_kpi).add_to(fg_kpi_kurang)

        # 4. Distribusi Kategori_ZScore (Sesuai nama kategori riil sheet: "Normal")
        val_z = str(row.get('Kategori_ZScore', '')).strip()
        if val_z == 'Normal': buat_marker(val_z).add_to(fg_z_normal)

        # 5. Distribusi Kategori_IQR
        val_iqr = str(row.get('Kategori_IQR', '')).strip()
        if val_iqr == 'Normal': buat_marker(val_iqr).add_to(fg_iqr_normal)
        elif val_iqr == 'Extreme High': buat_marker(val_iqr).add_to(fg_iqr_exhigh)

    # ==============================================================================
    # 5. CONFIG LAYERS MENU (KANAN ATAS)
    # ==============================================================================
    grouped_overlays = {
        "Hasil Standardisasi": [fg_fin_outstanding, fg_fin_high, fg_fin_average, fg_fin_under, fg_fin_critical],
        "Metode Statistik Dasar": [fg_heatmap],
        "Metode 1: Standar Deviasi": [fg_std_sedang, fg_std_tinggi],
        "Metode 2: Percentile Binning": [fg_pct_rendah, fg_pct_sedang, fg_pct_tinggi],
        "Metode 3: Kategori KPI Atasan": [fg_kpi_sangat_baik, fg_kpi_baik, fg_kpi_cukup, fg_kpi_kurang],
        "Metode 4: Kategori Z-Score": [fg_z_normal],
        "Metode 5: Rentang IQR": [fg_iqr_normal, fg_iqr_exhigh],
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
                     bottom: 50px; left: 70px; width: 240px; height: auto;
                     border:2px solid #ccc; z-index:9999; font-size:11px;
                     background-color:white; opacity:0.95; padding: 10px;
                     font-family: Arial, sans-serif; border-radius: 6px;
                     box-shadow: 2px 2px 6px rgba(0,0,0,0.2);">
           <b style="font-size:12px; color:#333;">Legenda Kategori Final:</b><br>
           <div style="margin-top:4px;"><i style="background:darkgreen; width:10px; height:10px; float:left; margin-right:8px; border-radius:50%;"></i><b>Outstanding (&ge;70%)</b></div>
           <div style="margin-top:4px;"><i style="background:green; width:10px; height:10px; float:left; margin-right:8px; border-radius:50%;"></i><b>High Performer (20% s/d 70%)</b></div>
           <div style="margin-top:4px;"><i style="background:orange; width:10px; height:10px; float:left; margin-right:8px; border-radius:50%;"></i><b>Average (0% s/d 20%)</b></div>
           <div style="margin-top:4px;"><i style="background:pink; width:10px; height:10px; float:left; margin-right:8px; border-radius:50%;"></i><b>Underperformer (-30% s/d 0%)</b></div>
           <div style="margin-top:4px;"><i style="background:red; width:10px; height:10px; float:left; margin-right:8px; border-radius:50%;"></i><b>Critical (&lt; -30%)</b></div>
           <hr style="margin:6px 0; border:0; border-top:1px solid #ddd;">
           <b>Glow Heatmap:</b> Volume Kepadatan Positif.
         </div>
         '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # ==============================================================================
    # 6. RENDER INDUK PETA DI STREAMLIT
    # ==============================================================================
    st.subheader("Peta Distribusi Finansial & Geografis")
    st_folium(m, width="100%", height=600, returned_objects=[])

    # ==============================================================================
    # 7. PREVIEW DATABASE INTERAKTIF (Disertai Kolom Baru Kategori_Final)
    # ==============================================================================
    st.markdown("---")
    st.subheader("Preview Dataset Master Terintegrasi")
    
    show_preview = st.toggle("Tampilkan Preview Tabel Data", value=False)

    if show_preview:
        search_query = st.text_input("Cari berdasarkan Nama Cabang:", "")
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
                "Omset Jan26": st.column_config.NumberColumn(format="Rp %',d"),
                "Persen Growth": st.column_config.NumberColumn(format="%.2f%%"),
            }
        )
    else:
        st.info("Klik tombol toggle di atas jika ingin menampilkan preview tabel data cabang.")

    # ==============================================================================
    # 8. SUMMARY STATISTIK GABUNGAN
    # ==============================================================================
    st.markdown("---")
    st.header("Summary Distribusi")
    st.subheader("TOTAL POPULASI DATA: 1157 CABANG")

    tab_final, tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "★ Kategori Final", "StdDev", "Percentile", "KPI Atasan", "Z-Score", "IQR"
    ])

    with tab_final:
        st.markdown("#### SUMMARY STANDARDISASI: Kategori Performa Final")
        # Menghitung otomatis volume riil dari dataframe setelah fungsi berjalan
        val_counts = df_clean['Kategori_Final'].value_counts()
        df_fin_summary = pd.DataFrame([
            {"Nama Kategori": "Outstanding", "Jumlah Cabang": val_counts.get("Outstanding", 0), "Porsi Data": f"{(val_counts.get('Outstanding', 0)/len(df_clean))*100:.2f}%"},
            {"Nama Kategori": "High Performer", "Jumlah Cabang": val_counts.get("High Performer", 0), "Porsi Data": f"{(val_counts.get('High Performer', 0)/len(df_clean))*100:.2f}%"},
            {"Nama Kategori": "Average", "Jumlah Cabang": val_counts.get("Average", 0), "Porsi Data": f"{(val_counts.get('Average', 0)/len(df_clean))*100:.2f}%"},
            {"Nama Kategori": "Underperformer", "Jumlah Cabang": val_counts.get("Underperformer", 0), "Porsi Data": f"{(val_counts.get('Underperformer', 0)/len(df_clean))*100:.2f}%"},
            {"Nama Kategori": "Critical", "Jumlah Cabang": val_counts.get("Critical", 0), "Porsi Data": f"{(val_counts.get('Critical', 0)/len(df_clean))*100:.2f}%"},
        ])
        st.table(df_fin_summary)

    with tab1:
        st.markdown("#### SUMMARY METODE: Standar Deviasi")
        df_std = pd.DataFrame([
            {"Nama Kategori": "Tinggi", "Jumlah Cabang": 32, "Persentase (%)": "2.77%"},
            {"Nama Kategori": "Sedang", "Jumlah Cabang": 1125, "Persentase (%)": "97.23%"}
        ])
        st.table(df_std)

    with tab2:
        st.markdown("#### SUMMARY METODE: Percentile")
        df_pct = pd.DataFrame([
            {"Nama Kategori": "Tinggi", "Jumlah Cabang": 289, "Persentase (%)": "24.98%"},
            {"Nama Kategori": "Sedang", "Jumlah Cabang": 578, "Persentase (%)": "49.96%"},
            {"Nama Kategori": "Rendah", "Jumlah Cabang": 290, "Persentase (%)": "25.06%"}
        ])
        st.table(df_pct)

    with tab3:
        st.markdown("#### SUMMARY METODE: KPI Atasan")
        df_ats = pd.DataFrame([
            {"Nama Kategori": "Sangat Baik", "Jumlah Cabang": 505, "Persentase (%)": "43.65%"},
            {"Nama Kategori": "Baik", "Jumlah Cabang": 479, "Persentase (%)": "41.40%"},
            {"Nama Kategori": "Cukup", "Jumlah Cabang": 169, "Persentase (%)": "14.61%"},
            {"Nama Kategori": "Kurang", "Jumlah Cabang": 4, "Persentase (%)": "0.35%"}
        ])
        st.table(df_ats)

    with tab4:
        st.markdown("#### SUMMARY METODE: Z-Score")
        df_z = pd.DataFrame([
            {"Nama Kategori": "Normal", "Jumlah Cabang": 1157, "Persentase (%)": "100.00%"}
        ])
        st.table(df_z)

    with tab5:
        st.markdown("#### SUMMARY METODE: IQR")
        df_iqr = pd.DataFrame([
            {"Nama Kategori": "Extreme High", "Jumlah Cabang": 87, "Persentase (%)": "7.52%"},
            {"Nama Kategori": "Normal", "Jumlah Cabang": 1070, "Persentase (%)": "92.48%"}
        ])
        st.table(df_iqr)
