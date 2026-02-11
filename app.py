import streamlit as st
from PIL import Image, ImageOps
import io
import zipfile

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Ridimensiona Foto", layout="wide")

# --- CSS PER TEMA CHIARO E PULITO ---
st.markdown("""
<style>
    /* Sfondo Bianco e Testo Leggibile */
    .stApp {background-color: #FFFFFF; color: #333333;}
    
    /* Sidebar Grigio Chiaro */
    section[data-testid="stSidebar"] {background-color: #F0F2F6;}
    
    /* Pulsanti BLU evidenti */
    .stButton>button {
        width: 100%; 
        border-radius: 8px; 
        height: 3em; 
        font-weight: bold; 
        background-color: #0068C9; 
        color: white; 
        border: none;
    }
    .stButton>button:hover {background-color: #004B91; color: white;}
    
    /* Titoli più scuri */
    h1, h2, h3 {color: #0E1117;}
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI LAVORO ---
def process_image(img, target_w, target_h, mode, bg_color):
    """Il cervello che ridimensiona le foto"""
    target_size = (int(target_w), int(target_h))
    
    if mode == "✂️ TAGLIA (Riempie tutto)":
        # Zoomma e taglia l'eccesso (Centrato)
        return ImageOps.fit(img, target_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    
    elif mode == "🖼️ ADATTA (Intera con bordi)":
        # Rimpicciolisce per farla stare, aggiunge bordi
        return ImageOps.pad(img, target_size, color=bg_color, centering=(0.5, 0.5))
    
    else: # DEFORMA
        # Allunga o schiaccia
        return img.resize(target_size, Image.Resampling.LANCZOS)

# --- BARRA LATERALE (IMPOSTAZIONI) ---
with st.sidebar:
    st.header("⚙️ Impostazioni")
    
    st.write("### 1. Misure Finali (Pixel)")
    # Colonne per Width (Larghezza) e Height (Altezza)
    c1, c2 = st.columns(2)
    with c1: 
        target_w = st.number_input("Larghezza", value=1080, step=1)
    with c2: 
        target_h = st.number_input("Altezza", value=1080, step=1)
        
    st.divider()
    
    st.write("### 2. Come ridimensiono?")
    resize_mode = st.radio("Scegli metodo:", 
        ["✂️ TAGLIA (Riempie tutto)", 
         "🖼️ ADATTA (Intera con bordi)", 
         "🥴 DEFORMA (Schiaccia/Allunga)"])
    
    # Se sceglie ADATTA, mostriamo il selettore colore
    bg_color = "#FFFFFF" # Default bianco
    if "ADATTA" in resize_mode:
        bg_color = st.color_picker("Scegli colore bordi", "#FFFFFF")
        
    st.divider()
    
    st.write("### 3. Formato File")
    out_format = st.selectbox("Salva come:", ["JPEG (Standard)", "PNG (Alta qualità)", "WEBP (Per siti web)"])
    
    quality = 90
    if "JPEG" in out_format or "WEBP" in out_format:
        quality = st.slider("Qualità %", 10, 100, 90)

# --- PAGINA PRINCIPALE ---
st.title("Ridimensiona Foto in Massa")
st.markdown("Carica quante foto vuoi, imposta le misure a sinistra, scarica lo ZIP.")

# Upload
uploaded_files = st.file_uploader("Trascina qui le foto", accept_multiple_files=True, type=['jpg','png','webp','jpeg'])

if uploaded_files:
    # --- ANTEPRIMA INTELLIGENTE ---
    st.divider()
    
    # Prendiamo la prima foto caricata per farti vedere come verrà
    first_img = Image.open(uploaded_files[0])
    
    # Applichiamo la modifica di prova
    preview_img = process_image(first_img, target_w, target_h, resize_mode, bg_color)
    
    # Mostriamo Prima e Dopo
    c_orig, c_new = st.columns(2)
    with c_orig:
        st.caption(f"Originale ({first_img.width}x{first_img.height})")
        st.image(first_img, use_column_width=True)
    with c_new:
        st.caption(f"RISULTATO ({target_w}x{target_h})")
        st.image(preview_img, use_column_width=True)
        
    # --- TASTONE DI CONFERMA ---
    st.success(f"L'anteprima ti piace? Se clicchi sotto elaboro tutte le **{len(uploaded_files)} foto** così.")
    
    if st.button(f"🚀 SCARICA TUTTO ({len(uploaded_files)} FILE)"):
        
        # Barra di progresso
        progress_bar = st.progress(0)
        zip_buffer = io.BytesIO()
        
        # Pulizia nome formato
        fmt_clean = "JPEG"
        if "PNG" in out_format: fmt_clean = "PNG"
        elif "WEBP" in out_format: fmt_clean = "WEBP"

        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for i, file in enumerate(uploaded_files):
                try:
                    img = Image.open(file)
                    # Elaborazione
                    res = process_image(img, target_w, target_h, resize_mode, bg_color)
                    
                    # Salvataggio
                    img_byte = io.BytesIO()
                    if fmt_clean == 'JPEG':
                        res = res.convert('RGB') # JPEG non vuole trasparenze
                        res.save(img_byte, format=fmt_clean, quality=quality)
                    elif fmt_clean == 'WEBP':
                        res.save(img_byte, format=fmt_clean, quality=quality)
                    else: # PNG
                        res.save(img_byte, format=fmt_clean)
                    
                    # Nome file nello ZIP
                    name_part = file.name.split('.')[0]
                    new_name = f"{target_w}x{target_h}_{name_part}.{fmt_clean.lower()}"
                    
                    zf.writestr(new_name, img_byte.getvalue())
                    
                except Exception as e:
                    st.error(f"Errore sulla foto {file.name}: {e}")
                
                # Avanza barra
                progress_bar.progress((i + 1) / len(uploaded_files))
        
        # Download Finale
        st.download_button(
            label="📦 CLICCA QUI PER SALVARE LO ZIP",
            data=zip_buffer.getvalue(),
            file_name="foto_ridimensionate.zip",
            mime="application/zip",
            type="primary"
        )
