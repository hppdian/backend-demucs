import os
import shutil
import zipfile
import subprocess
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI()

# Permitir peticiones desde tu web en Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def borrar_archivo(path: str):
    """Función para limpiar archivos temporales después de enviarlos"""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Error borrando temporal: {e}")

@app.get("/")
def home():
    return {"status": "ok", "message": "Backend de Demucs H65 activo"}

@app.post("/separar")
async def separar(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # Rutas temporales de trabajo
    temp_input = f"temp_{file.filename}"
    output_dir = f"salida_{os.path.splitext(file.filename)[0]}"
    zip_filename = f"stems_{os.path.splitext(file.filename)[0]}.zip"
    
    # 1. Guardar el archivo recibido
    with open(temp_input, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # 2. Limpiar carpeta previa si existe
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)

        # 3. Ejecutar Demucs en modo ligero y capturar errores
    try:
        cmd = f'python -m demucs.separate -n htdemucs --two-stems=vocals -o "{output_dir}" "{temp_input}"'
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("Demucs Output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("--- ERROR DETALLADO DE DEMUCS ---")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        raise e
        
        song_name = os.path.splitext(file.filename)[0]
        stems_folder = os.path.join(output_dir, "htdemucs", song_name)

        # 4. Comprimir las 4 pistas (.wav) en un ZIP
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(stems_folder):
                for f in files:
                    file_path = os.path.join(root, f)
                    zipf.write(file_path, arcname=f)

        # 5. Programar limpieza de carpetas temporales
        background_tasks.add_task(borrar_archivo, zip_filename)
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)

        # 6. Devolver el ZIP al usuario
        return FileResponse(
            path=zip_filename, 
            filename=zip_filename, 
            media_type='application/zip'
        )

    except Exception as e:
        return {"error": str(e)}

    finally:
        # Borrar el archivo de audio subido inicialmente
        if os.path.exists(temp_input):
            os.remove(temp_input)