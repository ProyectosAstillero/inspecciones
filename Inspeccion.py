import streamlit as st
import pandas as pd
import os
from datetime import datetime
from openpyxl import load_workbook
from io import BytesIO
from fpdf import FPDF
from PIL import Image
from docx import Document

# Interfaz para ingresar el nombre del proyecto
st.sidebar.header("Configuración del Proyecto")
PROJECT_NAME = st.sidebar.text_input("Nombre del Proyecto", "MiProyecto")

IMAGE_FOLDER = os.path.join(PROJECT_NAME, "imagenes")
EXCEL_FILE = os.path.join(PROJECT_NAME, "actividades.xlsx")

# Crear carpetas si no existen
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# Cargar o crear archivo Excel
def load_or_create_excel():
    if not os.path.exists(EXCEL_FILE):
        df = pd.DataFrame(columns=["Fecha", "Actividad", "Descripción", "Imagenes"])
        with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl', mode='w') as writer:
            df.to_excel(writer, index=False)
    return pd.read_excel(EXCEL_FILE)

def save_data(actividad, descripcion, image_files):
    df = load_or_create_excel()
    
    # Buscar si la actividad ya existe en el DataFrame
    existing_activity = df[df["Actividad"] == actividad]
    
    image_paths = []
    
    # Si la actividad ya existe, agregar imágenes a las existentes
    if not existing_activity.empty:
        # Obtener las imágenes existentes para esa actividad
        existing_images = existing_activity["Imagenes"].values[0]
        if existing_images:
            image_paths = existing_images.split(", ")

    # Verificar si se han cargado imágenes y guardarlas
    if image_files:
        for image_file in image_files:
            if image_file is not None:  # Verificar que el archivo no sea None
                image_path = os.path.relpath(os.path.join(IMAGE_FOLDER, image_file.name))
                with open(image_path, "wb") as f:
                    f.write(image_file.getbuffer())
                image_paths.append(image_path)

    # Convertir las rutas de las imágenes en una cadena separada por comas
    images_string = ", ".join(image_paths) if image_paths else ""
    
    # Si la actividad ya existe, actualizamos la fila, si no, agregamos una nueva
    if not existing_activity.empty:
        df.loc[df["Actividad"] == actividad, "Imagenes"] = images_string
    else:
        new_data = pd.DataFrame({
            "Fecha": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            "Actividad": [actividad],
            "Descripción": [descripcion],
            "Imagenes": [images_string]
        })
        df = pd.concat([df, new_data], ignore_index=True)
    
    # Guardar el DataFrame actualizado en el archivo Excel
    with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl', mode='w') as writer:
        df.to_excel(writer, index=False)

# Interfaz con Streamlit
st.title("Registro de Actividades")
actividad = st.text_input("Nombre de la actividad")
descripcion = st.text_area("Descripción")

# Opción para subir varias imágenes
image_files = st.file_uploader("Subir imágenes", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="file_uploader")

# Opción para capturar imágenes desde la cámara
use_camera = st.checkbox("Tomar fotos desde la cámara")
if use_camera:
    image_files = [st.camera_input("Captura de cámara")]

if st.button("Guardar"):
    if actividad and descripcion:
        save_data(actividad, descripcion, image_files)
        st.success("Actividad guardada correctamente!")
    else:
        st.warning("Por favor, completa todos los campos.")

# Mostrar datos en un expander
with st.expander("Ver actividades registradas"):
    df = load_or_create_excel()

    # Preparar la columna de imágenes (mostrar las imágenes de la ruta almacenada)
    def render_images(images_string):
        images = images_string.split(", ")
        return "".join([f'<img src="{img}" width="100" />' for img in images if img and os.path.exists(img)])

    # Mostrar el dataframe sin la columna de imagen, pero con las imágenes renderizadas
    st.dataframe(df.drop(columns=["Imagenes"]).style.format({"Imagenes": lambda x: render_images(x)}), use_container_width=True)

from fpdf import FPDF
import os

# Función para generar el informe en PDF
def generate_pdf():
    # Cargar el archivo Excel
    df = load_or_create_excel()
    
    # Crear objeto PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Título con el nombre del proyecto
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(200, 10, txt=f"Informe del Proyecto: {PROJECT_NAME}", ln=True, align='C')
    pdf.ln(10)  # Salto de línea

    # Configuración de la fuente para las actividades
    pdf.set_font('Arial', '', 12)

    # Iterar sobre las actividades
    for _, row in df.iterrows():
        actividad = row["Actividad"]
        descripcion = row["Descripción"]
        imagenes = row["Imagenes"].split(", ")

        # Título de la actividad
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(200, 10, txt=f"Actividad: {actividad}", ln=True)

        # Descripción de la actividad
        pdf.set_font('Arial', '', 12)
        pdf.multi_cell(0, 10, txt=f"Descripción: {descripcion}")
        pdf.ln(5)

        # Insertar las imágenes (si hay)
        for image_path in imagenes:
            if os.path.exists(image_path):
                # Asegúrate de que la imagen esté en un tamaño adecuado para el PDF
                img = Image.open(image_path)
                img_width, img_height = img.size
                aspect_ratio = img_height / img_width
                new_width = 100  # Ancho máximo de la imagen
                new_height = new_width * aspect_ratio

                # Convertir la imagen a formato JPEG si es necesario
                if image_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    pdf.image(image_path, w=new_width, h=new_height)
                    pdf.ln(new_height + 5)  # Dejar espacio después de la imagen
            else:
                pdf.cell(200, 10, txt=f"Imagen no encontrada: {image_path}", ln=True)
        
        pdf.ln(5)  # Salto de línea después de cada actividad

    # Guardar el PDF en un archivo
    pdf_output = os.path.join(PROJECT_NAME, f"Informe_{PROJECT_NAME}.pdf")
    pdf.output(pdf_output)

    return pdf_output

# Botón en Streamlit para generar el informe PDF
if st.button("Generar Informe PDF"):
    pdf_file = generate_pdf()
    st.success(f"Informe PDF generado: {pdf_file}")
    with open(pdf_file, "rb") as f:
        st.download_button("Descargar Informe PDF", f, file_name=os.path.basename(pdf_file))
