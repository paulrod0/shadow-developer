from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pathlib import Path
import os
import shutil
import zipfile
import ast
import json
import openai
import secrets

app = FastAPI()

UPLOAD_DIR = "/tmp/uploaded_code"  # Carpeta temporal permitida por Vercel
STYLE_PROFILE_PATH = "/tmp/style_profiles.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

openai.api_key = os.getenv("OPENAI_API_KEY")

security = HTTPBasic()
USERS = {
    "admin": "secretpassword",  # Cambia esto en producción
}

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_password = USERS.get(credentials.username)
    if not correct_password or not secrets.compare_digest(credentials.password, correct_password):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return credentials.username

if not os.path.exists(STYLE_PROFILE_PATH):
    with open(STYLE_PROFILE_PATH, "w") as f:
        json.dump({}, f)

def load_profiles():
    with open(STYLE_PROFILE_PATH, "r") as f:
        return json.load(f)

def save_profile(project: str, profile: dict):
    profiles = load_profiles()
    profiles[project] = profile
    with open(STYLE_PROFILE_PATH, "w") as f:
        json.dump(profiles, f, indent=2)

@app.post("/api/upload")
async def upload_repo(file: UploadFile = File(...), username: str = Depends(authenticate)):
    project_name = file.filename.replace(".zip", "")
    user_dir = Path(UPLOAD_DIR) / username
    project_dir = user_dir / project_name
    file_location = user_dir / file.filename
    os.makedirs(project_dir, exist_ok=True)
    os.makedirs(user_dir, exist_ok=True)

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if file.filename.endswith(".zip"):
        with zipfile.ZipFile(file_location, 'r') as zip_ref:
            zip_ref.extractall(project_dir)

        function_names = []
        variable_names = []

        for ext in ["*.py", "*.js", "*.java"]:
            for code_file in project_dir.rglob(ext):
                try:
                    with open(code_file, "r", encoding="utf-8") as f:
                        content = f.read()
                        if ext == "*.py":
                            tree = ast.parse(content)
                            for node in ast.walk(tree):
                                if isinstance(node, ast.FunctionDef):
                                    function_names.append(node.name)
                                elif isinstance(node, ast.Name):
                                    variable_names.append(node.id)
                        else:
                            lines = content.splitlines()
                            for line in lines:
                                if "function" in line or "def" in line:
                                    function_names.append(line.strip())
                                if "=" in line:
                                    parts = line.split("=")
                                    if len(parts[0].strip().split()) >= 1:
                                        variable_names.append(parts[0].strip().split()[-1])
                except:
                    continue

        profile = {
            "function_names": function_names[:10],
            "variable_names": list(set(variable_names))[:10]
        }
        save_profile(f"{username}:{project_name}", profile)

        return JSONResponse({"project": project_name, "message": "Project uploaded and profile created."})

    return JSONResponse({"message": "File uploaded but not a zip."})

@app.get("/api/analyze/{project_name}")
def analyze_code(project_name: str, username: str = Depends(authenticate)):
    profiles = load_profiles()
    profile = profiles.get(f"{username}:{project_name}")
    if not profile:
        return JSONResponse(status_code=404, content={"error": "Profile not found"})
    return profile

@app.post("/api/suggest")
def suggest_code(feature: str = Form(...), project: str = Form(...), username: str = Depends(authenticate)):
    profiles = load_profiles()
    profile = profiles.get(f"{username}:{project}")
    if not profile:
        return JSONResponse(status_code=404, content={"error": "Profile not found"})

    style_info = f"Function names: {profile['function_names']}, Variable names: {profile['variable_names']}"
    prompt = (
        f"You are an assistant developer. Generate a function to: {feature}.\n"
        f"Mimic this coding style:\n{style_info}\n"
        f"Return only the code, no explanations."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a senior developer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        suggestion = response['choices'][0]['message']['content']
    except Exception as e:
        return JSONResponse({"error": str(e)})

    return {"suggestion": suggestion}
