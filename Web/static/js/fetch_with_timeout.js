// ✅ 10초 타임아웃 적용된 fetchWithTimeout 함수
async function fetchWithTimeout(url, options = {}, timeout = 10000) { // 기본 타임아웃 10초
    const controller = new AbortController();
    const signal = controller.signal;

    // 지정된 시간 후 요청 취소
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    const loadsigns = document.getElementsByClassName("loading-sign");
    for (let i=0; i<loadsigns.length; i++){
        loadsigns[i].style.display = "block"
    }
    try {
        const response = await fetch(url, { ...options, signal });
        clearTimeout(timeoutId); // 성공하면 타임아웃 해제
        return await response.json(); // JSON 응답 처리
    } catch (error) {
        if (error.name === "AbortError") {
            throw new Error("⏳ 요청이 시간 초과되었습니다!");
        }
        throw error; // 기타 오류 처리
    } finally {
        for (let i=0; i<loadsigns.length; i++){
            loadsigns[i].style.display = "none"
        }
    }
}