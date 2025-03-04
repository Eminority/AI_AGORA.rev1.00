import sqlite3
import subprocess
import os
import tempfile

def get_image_from_db(db_path, image_id):
    """DB에서 지정한 ID의 이미지를 BLOB 형식으로 가져옵니다."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT image_blob FROM images WHERE id=?", (image_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def save_image_to_db(db_path, image_id, image_blob):
    """처리된 이미지 BLOB을 DB에 업데이트합니다."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE images SET processed_image_blob=? WHERE id=?", (image_blob, image_id))
    conn.commit()
    conn.close()

def run_img2img(input_image_path, output_dir, workflow_json_path, comfyui_dir):
    """
    ComfyUI의 main.py를 호출하여 img2img 워크플로우를 실행합니다.
    CLI 인자로 워크플로우 파일, 입력 이미지, 출력 디렉토리를 전달합니다.
    """
    main_script = os.path.join(comfyui_dir, "ComfyUI", "main.py")
    
    # 예시: "--workflow", "--input", "--output-directory"와 같이 CLI 옵션을 전달
    command = [
        "python", main_script,
        "--workflow", workflow_json_path,
        "--input", input_image_path,
        "--output-directory", output_dir
    ]
    
    # subprocess.run으로 ComfyUI 프로세스를 실행합니다.
    subprocess.run(command, check=True)
    
    # 워크플로우에 따라 생성된 출력 파일명을 미리 알고 있다고 가정 (예: "result.png")
    output_image_path = os.path.join(output_dir, "result.png")
    return output_image_path

def main():
    db_path = "your_database.db"               # 데이터베이스 파일 경로
    image_id = 1                               # 처리할 이미지의 ID (예시)
    comfyui_dir = r"C:\ComfyUI"                  # ComfyUI가 설치된 디렉토리
    workflow_json_path = r"C:\workflows\img2img_workflow.json"  # img2img용 워크플로우 JSON 파일 경로

    # 1. DB에서 원본 이미지(BLOB) 가져오기
    image_blob = get_image_from_db(db_path, image_id)
    if not image_blob:
        print("지정한 ID의 이미지를 DB에서 찾을 수 없습니다.")
        return

    # 2. 임시 입력 파일 생성
    temp_input_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    with open(temp_input_file.name, "wb") as f:
        f.write(image_blob)

    # 3. 임시 출력 디렉토리 생성
    temp_output_dir = tempfile.mkdtemp()

    try:
        # 4. ComfyUI img2img 프로세스 실행
        output_image_path = run_img2img(temp_input_file.name, temp_output_dir, workflow_json_path, comfyui_dir)
    except subprocess.CalledProcessError as e:
        print("ComfyUI img2img 실행 중 에러 발생:", e)
        return

    # 5. 결과 이미지 읽어오기
    with open(output_image_path, "rb") as f:
        processed_image_blob = f.read()

    # 6. 처리된 이미지 DB에 업데이트
    save_image_to_db(db_path, image_id, processed_image_blob)

    # 임시 파일 및 디렉토리 정리
    os.remove(temp_input_file.name)
    # 추가로 temp_output_dir 내부의 파일들 삭제 필요 시 구현

    print("이미지 처리 및 DB 업데이트가 완료되었습니다.")

if __name__ == "__main__":
    main()
