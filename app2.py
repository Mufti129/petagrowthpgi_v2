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
# Membaca langsung dari file CSV di direktori yang sama dengan app.py
CSV_FILE_PATH = "df_persen_growth.csv"

@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        # Handle string parsing atau pembersihan dasar jika diperlukan
        if 'Persen Growth' in df.columns:
            df['Persen Growth'] = pd.to_numeric(df['Persen Growth'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Gagal memuat file '{file_path}'. Pastikan file berada di folder yang sama dengan app.py. Error: {e}")
        return None

df_clean = load_data(CSV_FILE_PATH)

if df_clean is not None:
    # Dictionary warna global agar konsisten di semua metode
    color_map = {
        'baik': 'green', 'tinggi': 'green', 'extreme high': 'darkgreen', 'ekstrem (superstar)': 'darkgreen',
        'sedang': 'orange', 'extreme': 'darkgreen', 'sangat baik': 'blue',
        'jelek': 'red', 'rendah': 'red', 'extreme low': 'darkred', 'kurang baik': 'pink'
    }

    # ==============================================================================
    # 2. INISIALISASI PETA FOLIUM (OPENSTREETMAP)
    # ==============================================================================
    # Mengambil koordinat rata-rata dari data jika tersedia untuk auto-center otomatis
    lat_center = df_clean['latitude_cabang'].mean() if 'latitude_cabang' in df_clean.columns else -6.2088
    lon_center = df_clean['longitude_cabang'].mean() if 'longitude_cabang' in df_clean.columns else 106.8456

    m = folium.Map(location=[lat_center, lon_center], zoom_start=11)

    # Layer 1: Heatmap
    fg_heatmap = folium.FeatureGroup(name='Glow Heatmap Growth', show=True)
    if 'Growth' in df_clean.columns:
        heat_data = [[row['latitude_cabang'], row['longitude_cabang'], row['Growth']] for i, row in df_clean.iterrows()]
    else:
        # Fallback menggunakan Persen Growth jika kolom Growth nominal tidak ada
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

        # 1. Distribusi ke Layer StdDev
        val_std = row.get('Kategori_By_StdDev')
        if val_std == 'Sedang': buat_marker(val_std).add_to(fg_std_sedang)
        elif val_std == 'Tinggi': buat_marker(val_std).add_to(fg_std_tinggi)

        # 2. Distribusi ke Layer Percentile
        val_pct = row.get('Kategori_By_Percentile')
        if val_pct == 'Rendah': buat_marker(val_pct).add_to(fg_pct_rendah)
        elif val_pct == 'Sedang': buat_marker(val_pct).add_to(fg_pct_sedang)
        elif val_pct == 'Tinggi': buat_marker(val_pct).add_to(fg_pct_tinggi)

        # 3. Distribusi ke Layer Atasan (KPI)
        val_ats = row.get('Kategori_Atasan')
        if val_ats == 'Sangat Baik': buat_marker(val_ats).add_to(fg_ats_sangat_baik)
        elif val_ats == 'Baik': buat_marker(val_ats).add_to(fg_ats_baik)
        elif val_ats == 'Kurang Baik': buat_marker(val_ats).add_to(fg_ats_kurang_baik)
        elif val_ats == 'Jelek': buat_marker(val_ats).add_to(fg_ats_jelek)

        # 4. Distribusi ke Layer Hibrida
        val_hib = row.get('Kategori_Hibrida')
        if val_hib == 'Ekstrem (Superstar)': buat_marker(val_hib).add_to(fg_hib_super)
        elif val_hib == 'Rendah': buat_marker(val_hib).add_to(fg_hib_rendah)
        elif val_hib == 'Sedang': buat_marker(val_hib).add_to(fg_hib_sedang)
        elif val_hib == 'Tinggi': buat_marker(val_hib).add_to(fg_hib_tinggi)

        # 5. Distribusi ke Layer Z-Score
        val_z = row.get('Kategori_ZScore')
        if val_z == 'Extreme': buat_marker(val_z).add_to(fg_z_extreme)
        elif val_z == 'Baik': buat_marker(val_z).add_to(fg_z_baik)
        elif val_z == 'Sedang': buat_marker(val_z).add_to(fg_z_sedang)

        # 6. Distribusi ke Layer IQR
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
        collapsed=True,          # Mengubah ke True agar menu layer menjadi ikon ringkas
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
    st.subheader("Peta Distribusi Finansial & Geografis")
    st_folium(m, width="100%", height=600, returned_objects=[])

    # ==============================================================================
    # 7. PREVIEW DATABASE (DENGAN FITUR SHOW/HIDE INTERAKTIF)
    # ==============================================================================
    st.markdown("---")
    st.subheader("Preview Dataset Master Terintegrasi")
    
    # Tombol Toggle Interaktif untuk Show/Hide Data Tabel
    show_preview = st.toggle("Tampilkan Preview Tabel Data", value=False)

    if show_preview:
        # Fitur pencarian interaktif di Streamlit
        search_query = st.text_input("Cari berdasarkan Nama Cabang:", "")
        if search_query:
            df_display = df_clean[df_clean['cabang'].str.contains(search_query, case=False, na=False)]
        else:
            df_display = df_clean

        st.write(f"Menampilkan {len(df_display)} dari total {len(df_clean)} data cabang.")
        
        # Render tabel dengan formatting nominal Rupiah & persen otomatis
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
