// 📌 static/js/chat.js

// 채팅창에 메시지를 추가하는 함수
function addMessageToChat(sender, text, type) {
    let chatBox = document.getElementById("chat-box");
    if (!chatBox) {
        console.error("chat-box 요소를 찾을 수 없습니다.");
        return;
    }

    let messageElement = document.createElement("div");
    messageElement.classList.add("message", type);
    messageElement.innerHTML = `<strong>${sender}:</strong> ${text}`;
    chatBox.appendChild(messageElement);

    // 📌 채팅창 자동 스크롤 (새로운 메시지가 보이도록)
    chatBox.scrollTop = chatBox.scrollHeight;
}
