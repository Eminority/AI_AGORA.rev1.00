from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import subprocess
import os
import tempfile

app = FastAPI()
input 

class Img2ImgRequest(BaseModel):
    input_image_path: str
    workflow_json_path: str

def run_img2img(input_image_path: str, workflow_json_path: str, comfyui_dir: str) -> str:
    """
    ComfyUI의 main.py를 호출하여 img2img 작업을 실행하고,
    결과 이미지의 경로를 반환합니다.
    """
    temp_output_dir = tempfile.mkdtemp()
    main_script = os.path.join(comfyui_dir, "ComfyUI", "main.py")
    
    command = [
        "python", main_script,
        "--workflow", workflow_json_path,
        "--input", input_image_path,
        "--output-directory", temp_output_dir
    ]
    
    subprocess.run(command, check=True)
    output_image_path = os.path.join(temp_output_dir, "result.png")
    return output_image_path

@app.post("/generate-image")
def generate_image(request: Img2ImgRequest, background_tasks: BackgroundTasks):
    comfyui_dir = r"C:\lji\comfyui_clone\ComfyUI"  # ComfyUI 소스 코드 버전 설치 경로 (수정 필요)
    
    try:
        output_image_path = run_img2img(request.input_image_path, request.workflow_json_path, comfyui_dir)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail="Image generation failed") from e
    
    return {"output_image_path": output_image_path}
