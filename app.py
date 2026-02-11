import streamlit as st
from PIL import Image, ImageOps
import io
import zipfile

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Image Lab Pro", layout="wide")

# CSS: Stile Dark "Adobe Style"
st.markdown("""
<style>
    /* Sfondo scuro professionale */
    .stApp {background-color: #121212; color: #e0e0e0;}
    
    /* Sidebar grigio scuro */
    section[data-testid="stSidebar"] {background-color: #1e1e1e;}
    
    /* Pulsanti VERDI (Azione) */
    .stButton>button {
        width: 100%; 
        border-radius: 8px; 
        height: 3em; 
        font-weight: bold; 
        font-size: 16px;
        background-color: #2e7d32; 
        color: white;
        border: none;
    }
    .stButton>button:hover {background-color: #1b5e20; color: white;}
    
    /* Input Fields più scuri */
    .stNumberInput input {background-color: #2c2c2c; color: white;}
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI ELABORAZIONE ---
def process_image(img, target_w, target_h, mode, bg_color):
    target_size = (int(target_w), int(target_h))
    
    if mode == "CROP (Riempimento Smart)":
        # Taglia i bordi in eccesso per riempire il frame (tipo Instagram)
        return ImageOps.fit(img, target_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    
    elif mode == "FIT (Adatta con Bordi)":
        # Rimpicciolisce la foto per farla entrare, riempie il vuoto con colore
        return ImageOps.pad(img, target_size, color=bg_color, centering=(0.5, 0.5))
    
    elif mode == "STRETCH (Deforma)":
        # Forza le dimensioni (sconsigliato ma a volte serve)
        return img.resize(target_size, Image.Resampling.LANCZOS)
        
    return img

# --- SIDEBAR (CONTROLLI) ---
with st.sidebar:
    st.header("🎛️ CONTROLLI LAB")
    
    st.info("1. DIMENSIONI (Pixel)")
    c1, c2 = st.columns(2)
    with c1: w_input = st.number_input("Larghezza", value=1080, step=1)
    with c2: h_input = st.number_input("Altezza", value=1080, step=1)
    
    st.divider()
    
    st.info("2. METODO DI TAGLIO")
    resize_mode = st.radio("Logica:", 
        ["CROP (Riempimento Smart)", "FIT (Adatta con Bordi)", "STRETCH (Deforma)"])
    
    bg_col = "#000000"
    if "FIT" in resize_mode:
        bg_col = st.color_picker("Colore Bordi", "#000000")
        
    st.divider()
    
    st.info("3. ESPORTAZIONE")
    out_fmt = st.selectbox("Formato", ["JPEG", "PNG", "WEBP"])
    quality = st.slider("Qualità %", 10, 100, 90)

# --- MAIN AREA ---
st.title("Image Lab Pro 🧪")
st.markdown("Carica le tue foto, imposta le misure a sinistra, scarica lo ZIP.")

files = st.file_uploader("Trascina qui le foto (Batch)", accept_multiple_files=True, type=['jpg','png','webp','jpeg'])

if files:
    # --- ANTEPRIMA ---
    st.write("---")
    col_preview, col_action = st.columns([1, 2])
    
    # Prendi la prima foto per mostrare l'esempio
    first_img = Image.open(files[0])
    preview_res = process_image(first_img, w_input, h_input, resize_mode, bg_col)
    
    with col_preview:
        st.caption("👁️ ANTEPRIMA (1° FOTO)")
        st.image(preview_res, caption=f"Output: {w_input}x{h_input}px", use_column_width=True)
    
    with col_action:
        st.subheader(f"Pronto a elaborare {len(files)} foto?")
        st.write(f"Verranno tutte ridimensionate a **{w_input}x{h_input}** usando il metodo **{resize_mode}**.")
        
        # TASTO AZIONE
        if st.button(f"🚀 ELABORA {len(files)} FOTO"):
            
            progress_bar = st.progress(0)
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for i, file in enumerate(files):
                    try:
                        img = Image.open(file)
                        res = process_image(img, w_input, h_input, resize_mode, bg_col)
                        
                        # Salvataggio in RAM
                        img_byte = io.BytesIO()
                        if out_fmt == 'JPEG':
                            res = res.convert('RGB')
                            res.save(img_byte, format=out_fmt, quality=quality)
                        else:
                            res.save(img_byte, format=out_fmt, quality=quality)
                        
                        # Aggiungi allo ZIP con nome pulito
                        clean_name = file.name.split('.')[0]
                        new_name = f"{w_input}x{h_input}_{clean_name}.{out_fmt.lower()}"
                        zf.writestr(new_name, img_byte.getvalue())
                        
                    except Exception as e:
                        st.error(f"Errore su {file.name}")
                    
                    progress_bar.progress((i + 1) / len(files))
            
            st.success("✅ Fatto!")
            st.download_button(
                label="📦 SCARICA ZIP COMPLETO",
                data=zip_buffer.getvalue(),
                file_name="imagelab_export.zip",
                mime="application/zip",
                type="primary"
            )

else:
    st.info("👈 Inizia configurando le dimensioni nella barra laterale.")
