import os
import shutil
import subprocess
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI()

# Permite peticiones desde tu sitio en Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/separar")
async def separar(file: UploadFile = File(...)):
    temp_input = f"temp_{file.filename}"
    output_dir = "salida_temp"

    # Guardar archivo enviado
    with open(temp_input, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    # Ejecutar Demucs
    subprocess.run(f'demucs -o "{output_dir}" "{temp_input}"', shell=True, check=True)

    song_name = os.path.splitext(file.filename)[0]
    base_path = os.path.join(output_dir, "htdemucs", song_name)

    # Limpiar entrada
    os.remove(temp_input)

    # Regresar ruta de vocales como prueba rápida
    return {"mensaje": "Completado", "folder": song_name}