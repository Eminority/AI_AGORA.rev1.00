////// input type=file, id=imageUpload에서 이미지를 업로드했을 경우
////// id=imagePreview로 미리보기 나오게 하기


document.addEventListener("DOMContentLoaded", function(){
    document.getElementById("imageUpload").addEventListener("change", function (event) {
        const file = event.target.files[0]; // 업로드한 파일 가져오기
        if (file) {
            const reader = new FileReader();
            reader.onload = function (e) {
                const preview = document.getElementById("imagePreview");
                preview.src = e.target.result; // 미리보기 이미지 설정
                preview.style.display = "block"; // 이미지 보이게 설정
            };
            reader.readAsDataURL(file); // 파일을 DataURL로 변환하여 미리보기
        }
    });
});
