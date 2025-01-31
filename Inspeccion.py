import streamlit as st
import os
import pandas as pd
import zipfile
from datetime import datetime
from fpdf import FPDF
from PIL import Image
from io import BytesIO
import send2trash

        # Definir carpetas base donde se almacenan los proyectos y archivos comprimidos
BASE_DIR = "./"
PROJECTS_DIR = os.path.join(BASE_DIR, "Proyecto")  # Carpeta donde se crearán los proyectos
CACHE_DIR = os.path.join(BASE_DIR, "CACHE")  # Carpeta donde se almacenarán los archivos ZIP

# Crear las carpetas si no existen
os.makedirs(PROJECTS_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

def get_saved_projects():
    """Obtiene una lista de carpetas que representan proyectos guardados"""
    return [f for f in os.listdir(PROJECTS_DIR) if os.path.isdir(os.path.join(PROJECTS_DIR, f))]

def load_or_create_excel(excel_file):
    """Carga o crea un archivo Excel para almacenar actividades"""
    if not os.path.exists(excel_file):
        df = pd.DataFrame(columns=["Fecha", "Actividad", "Descripción", "Imagenes"])
        df['Descripción'] = df['Descripción'].fillna("").astype(str)  # Reemplazar valores nulos con cadenas vacías
        df.to_excel(excel_file, index=False)
    return pd.read_excel(excel_file)

def generate_pdf(project_name, df, image_folder):
    """Genera un PDF con la información del proyecto"""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Título
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(200, 10, txt=f"Informe del Proyecto: {project_name}", ln=True, align='C')
    pdf.ln(10)

    # Contenido
    pdf.set_font('Arial', '', 12)

    for _, row in df.iterrows():
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(200, 10, txt=f"Actividad: {row['Actividad']}", ln=True)
        pdf.set_font('Arial', '', 12)
        pdf.multi_cell(0, 10, txt=f"Descripción: {row['Descripción']}")
        pdf.ln(5)

        # Insertar imágenes
        images = row["Imagenes"].split(", ")
        for img_path in images:
            img_path = img_path.strip()
            full_path = os.path.join(image_folder, os.path.basename(img_path))
            if os.path.exists(full_path):
                pdf.image(full_path, w=80)
                pdf.ln(5)
    
    pdf_output = os.path.join(PROJECTS_DIR, project_name, f"Informe_{project_name}.pdf")
    pdf.output(pdf_output)

    return pdf_output

def compress_project(project_name):
    """Comprime el Excel y las imágenes del proyecto en un archivo ZIP dentro de CACHE"""
    zip_filename = os.path.join(CACHE_DIR, f"{project_name}.zip")
    project_folder = os.path.join(PROJECTS_DIR, project_name)

    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(project_folder):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, PROJECTS_DIR))
    
    return zip_filename

def delete_project(project_name):
    """Mueve un proyecto y todos sus archivos a la papelera"""
    project_path = os.path.join(PROJECTS_DIR, project_name)
    
    if os.path.exists(project_path):
        try:
            send2trash.send2trash(project_path)
            return True
        except Exception as e:
            st.error(f"Error al mover el proyecto a la papelera: {e}")
            return False
    else:
        st.warning(f"El proyecto '{project_name}' no existe.")
        return False

# Crear una nueva pestaña para eliminar proyectos
tab1, tab2, tab3 = st.tabs(["📌 Añadir Actividades", "📂 Proyectos Guardados", "🗑️ Eliminar Proyecto"])

# 🔹 TAB 1: AÑADIR ACTIVIDADES
with tab1:
    st.title("Registro de Actividades")

    # Configuración del Proyecto
    st.sidebar.header("Configuración del Proyecto")
    PROJECT_NAME = st.sidebar.text_input("Nombre del Proyecto")

    PROJECT_CREATED = st.sidebar.button("📂 Crear Proyecto")

    if PROJECT_CREATED and PROJECT_NAME.strip():
        PROJECT_PATH = os.path.join(PROJECTS_DIR, PROJECT_NAME)  # Nueva ruta de proyectos
        IMAGE_FOLDER = os.path.join(PROJECT_PATH, "imagenes")
        EXCEL_FILE = os.path.join(PROJECT_PATH, "actividades.xlsx")

        os.makedirs(IMAGE_FOLDER, exist_ok=True)
        load_or_create_excel(EXCEL_FILE)

        st.sidebar.success(f"✅ Proyecto '{PROJECT_NAME}' creado exitosamente!")

    elif PROJECT_CREATED:
        st.sidebar.error("⚠️ Debes ingresar un nombre válido para el proyecto.")

    # Solo permitir agregar actividades si el proyecto existe
    if not PROJECT_NAME.strip() or not os.path.exists(os.path.join(PROJECTS_DIR, PROJECT_NAME)):  # Actualizar ruta de proyecto
        st.warning("⚠️ Primero debes crear un proyecto desde la barra lateral.")
    else:
        PROJECT_PATH = os.path.join(PROJECTS_DIR, PROJECT_NAME)
        IMAGE_FOLDER = os.path.join(PROJECT_PATH, "imagenes")
        EXCEL_FILE = os.path.join(PROJECT_PATH, "actividades.xlsx")

        actividad = st.text_input("Nombre de la actividad")
        descripcion = st.text_area("Descripción")

        image_files = st.file_uploader("📤 Subir imágenes", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

        use_camera = st.checkbox("📸 Tomar foto con la cámara")
        if use_camera:
            camera_photo = st.camera_input("Captura de cámara")
            if camera_photo:
                image_files = image_files or []  # Asegura que image_files no sea None
                image_files.append(camera_photo)
            else:
                st.warning("⚠️ No se ha capturado ninguna imagen.")

        if st.button("Guardar"):
            if actividad and descripcion:
                df = load_or_create_excel(EXCEL_FILE)

                image_paths = []
                if image_files:
                    for image_file in image_files:
                        image_path = os.path.join(IMAGE_FOLDER, image_file.name)
                        with open(image_path, "wb") as f:
                            f.write(image_file.getbuffer())
                        image_paths.append(image_path)

                images_string = ", ".join(image_paths) if image_paths else ""

                new_data = pd.DataFrame({
                    "Fecha": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                    "Actividad": [actividad],
                    "Descripción": [descripcion],
                    "Imagenes": [images_string]
                })
                df = pd.concat([df, new_data], ignore_index=True)

                df.to_excel(EXCEL_FILE, index=False)
                st.success("✅ Actividad guardada correctamente!")
            else:
                st.warning("⚠️ Por favor, completa todos los campos.")

# 🔹 TAB 2: PROYECTOS GUARDADOS (sin cambios)
with tab2:
    st.title("📂 Proyectos Guardados")

    projects = get_saved_projects()

    if projects:
        selected_project = st.selectbox("Selecciona un proyecto", projects)

        st.write(f"## Proyecto: {selected_project}")

        # Mostrar las actividades e imágenes del proyecto como antes
        excel_file = os.path.join(PROJECTS_DIR, selected_project, "actividades.xlsx")
        if os.path.exists(excel_file):
            df = pd.read_excel(excel_file)
            st.write("### Actividades Registradas")
            st.dataframe(df.drop(columns=["Imagenes"]), use_container_width=True)

        # Mostrar imágenes del proyecto
        image_folder = os.path.join(PROJECTS_DIR, selected_project, "imagenes")
        if os.path.exists(image_folder):
            st.write("### 📷 Imágenes del Proyecto")
            images = [f for f in os.listdir(image_folder) if f.endswith(("png", "jpg", "jpeg"))]

            # Mostrar imágenes en un grid
            cols = st.columns(3)  # Puedes ajustar el número de columnas a tu preferencia
            for i, img in enumerate(images):
                img_path = os.path.join(image_folder, img)
                with cols[i % 3]:  # Repartir las imágenes entre las columnas
                    st.image(img_path, caption=img, use_container_width=True)

        # Botón para generar y descargar PDF
        if st.button("📄 Generar Informe PDF"):
            pdf_file = generate_pdf(selected_project, df, image_folder)
            st.success(f"✅ Informe PDF generado: {pdf_file}")
            with open(pdf_file, "rb") as f:
                st.download_button("⬇️ Descargar Informe PDF", f, file_name=os.path.basename(pdf_file))

        # Botón para descargar ZIP del proyecto
        if st.button("📦 Descargar Proyecto (.zip)"):
            zip_file = compress_project(selected_project)
            st.success(f"✅ Archivo comprimido generado: {zip_file}")
            with open(zip_file, "rb") as f:
                st.download_button("⬇️ Descargar ZIP", f, file_name=os.path.basename(zip_file))

    else:
        st.write("⚠️ No hay proyectos guardados.")

# 🔹 TAB 3: ELIMINAR PROYECTO (sin cambios)
with tab3:
    st.title("🗑️ Eliminar Proyecto")

    # Lista de proyectos guardados
    projects_to_delete = get_saved_projects()

    if projects_to_delete:
        selected_project_to_delete = st.selectbox("Selecciona un proyecto para eliminar", projects_to_delete)

        st.write(f"## Proyecto seleccionado: {selected_project_to_delete}")

        # Confirmación para eliminar
        confirm_delete = st.checkbox(f"⚠️ ¿Estás seguro de eliminar el proyecto '{selected_project_to_delete}'?")
        if confirm_delete:
            if st.button("🗑️ Eliminar Proyecto"):
                if delete_project(selected_project_to_delete):
                    st.success(f"✅ Proyecto '{selected_project_to_delete}' eliminado con éxito.")
                else:
                    st.error(f"⚠️ Error al eliminar el proyecto '{selected_project_to_delete}'.")
    else:
        st.write("⚠️ No hay proyectos para eliminar.")

