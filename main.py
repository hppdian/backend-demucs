import os
import shutil
import zipfile
import subprocess
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def borrar_archivo(path: str):
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
    filename_clean = "".join([c for c in file.filename if c.isalnum() or c in (".", "_", "-")])
    temp_input = f"temp_{filename_clean}"
    output_dir = f"salida_{os.path.splitext(filename_clean)[0]}"
    zip_filename = f"stems_{os.path.splitext(filename_clean)[0]}.zip"
    
    with open(temp_input, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)

        # RUTA EXACTA DEL PYTHON DEL ENTORNO VIRTUAL
        python_executable = os.path.join(os.getcwd(), ".venv", "bin", "python")
        if not os.path.exists(python_executable):
            python_executable = "python"

        cmd = f'"{python_executable}" -m demucs.separate -n htdemucs --two-stems=vocals -o "{output_dir}" "{temp_input}"'
        
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("Demucs Output:", result.stdout)

        # Buscador dinámico de pistas para que el ZIP no salga vacío
        archivos_encontrados = 0
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(output_dir):
                for f in files:
                    if f.endswith(('.wav', '.mp3', '.flac')):
                        file_path = os.path.join(root, f)
                        zipf.write(file_path, arcname=f)
                        archivos_encontrados += 1

        background_tasks.add_task(borrar_archivo, zip_filename)
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)

        return FileResponse(
            path=zip_filename, 
            filename=zip_filename, 
            media_type='application/zip'
        )

    except subprocess.CalledProcessError as e:
        print("--- ERROR DETALLADO DE DEMUCS ---")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return {"error": "Error al procesar el audio con Demucs", "details": e.stderr}

    except Exception as e:
        print("Error general:", str(e))
        return {"error": str(e)}

    finally:
        if os.path.exists(temp_input):
            os.remove(temp_input)