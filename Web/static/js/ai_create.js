document.addEventListener("DOMContentLoaded", function(){
    document.getElementById("yoloDetectForm").addEventListener("submit", async function (event) {
        event.preventDefault();

        const fileInput = document.getElementById("original_image");
        if (!fileInput.files.length) {
            alert("파일을 선택하세요.");
            return;
        }

        const formData = new FormData();
<<<<<<< HEAD
        formData.append("file", fileInput.files[0]);

        // 서버에 이미지 업로드 요청
        const response = await fetch("{{ request.url_for('list_from_object_detect') }}", {
=======
        formData.append("original_image", fileInput.files[0]);

        // 서버에 이미지 업로드 요청
        const yoloDetectFormRequestURL = document.getElementById("yoloDetectForm").getAttribute("data-object-detect-url");
        const response = await fetch(yoloDetectFormRequestURL, {
>>>>>>> dev0
            method: "POST",
            body: formData
        });

        const result = await response.json();
        console.log("서버 응답:", result);

        // 서버에서 받은 list 데이터를 기반으로 radio 버튼 생성
<<<<<<< HEAD
        generateRadioButtons(result.object);
=======
        if (result.result == true){
            generateRadioButtons(result.data);
            document.getElementById("generateAI_area").style = "display: block;";
        }
>>>>>>> dev0
    });

    function generateRadioButtons(options) {
        const container = document.getElementById("detected-list");
        container.innerHTML = "";  // 기존 내용 초기화

<<<<<<< HEAD
        if (!options.length) {
            container.innerHTML = "<p>감지된 객체가 없습니다.</p>";
            return;
        }

        options.forEach((option, index) => {
            const label = document.createElement("label");
            label.innerHTML = `
                <input type="radio" name="name" value="${option} required" ${index === 0 ? "checked" : ""}>
                ${option}
=======
        Object.entries(options).forEach(([key, data], index) => {
            const label = document.createElement("label");
            label.innerHTML = `
                <input type="radio" name="name" value="${data.name}" data-filename="${key}" required ${index === 0 ? "checked" : ""}>
                ${data.name}
>>>>>>> dev0
            `;
            container.appendChild(label);
            container.appendChild(document.createElement("br"));  // 줄바꿈
        });
<<<<<<< HEAD
=======
        if (container.innerHTML === ""){
            let nothing_in_image = document.createElement("p");
            nothing_in_image.innerHTML = `감지된 물체가 없습니다.`
            container.appendChild(nothing_in_image)
        }
>>>>>>> dev0
    }


    //submit 시 새로고침 방지
    document.getElementById("ImageSelectedForm").addEventListener("submit", async function (event) {
        event.preventDefault();
<<<<<<< HEAD

        const selectedObject = document.querySelector('input[name="selected-object"]:checked');

=======
        const selectedObject = document.querySelector('input[name="name"]:checked');
        const selectedAI = document.querySelector('input[name="ai"]:checked')
>>>>>>> dev0
        if (!selectedObject) {
            alert("객체를 선택하세요.");
            return;
        }

        const formData = new FormData();
        formData.append("selected_object", selectedObject.value);
<<<<<<< HEAD

        // FastAPI 서버에 선택한 객체 정보 전송
        const response = await fetch("{{ request.url_for('create_profile') }}", {
=======
        formData.append("file_path", selectedObject.getAttribute("data-filename"));
        formData.append("ai", selectedAI.value);
        // FastAPI 서버에 선택한 객체 정보 전송
        const createProfileRequestURL =  document.getElementById("ImageSelectedForm").getAttribute("data-create-profile-url");
        const response = await fetch(createProfileRequestURL, {
>>>>>>> dev0
            method: "POST",
            body: formData
        });

        const result = await response.json();
        console.log("선택한 객체:", result);

<<<<<<< HEAD
        alert(`선택한 객체: ${result.selected}`);
=======
        alert(`선택한 객체 ${selectedObject.value} 로 AI가 생성중입니다...`);
>>>>>>> dev0
    });
})