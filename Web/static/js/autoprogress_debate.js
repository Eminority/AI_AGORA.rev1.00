// AI 토론 자동 진행 함수
async function autoProgressDebate(debateId) {
    while (true) {  // 무한 반복 (AI가 계속 진행되도록)
        try {
            const formData = new URLSearchParams();
            formData.append("id", debateId);
            formData.append("message", "");  // 빈 메시지 전송

            const response = await fetch("/debate/progress", {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: formData
            });

            if (!response.ok) throw new Error("서버 응답 실패");

            const result = await response.json();
            console.log("AI 진행 응답:", result);

            // 📌 AI 응답이 있으면 채팅창에 추가
            if (result.progress) {
                addMessageToChat(result.progress.speaker, result.progress.timestamp + "\n" + result.progress.message, "received");
            } else if (result.message) {
                console.log("AI 토론 종료 메시지 감지:", result.message);
                break; // 📌 AI 진행 중단
            }


            // 📌 일정 시간 대기 후 반복 실행
            await new Promise(resolve => setTimeout(resolve, 2000));

        } catch (error) {
            console.error("AI 진행 실패:", error);
            break; // 에러 발생 시 반복 종료
        }
    }
}
