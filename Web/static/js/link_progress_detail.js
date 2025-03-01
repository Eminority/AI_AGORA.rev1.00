document.addEventListener("DOMContentLoaded", function(){
    function redirectToProfile() {
        document.querySelectorAll(".progress_detail").forEach(function (element){
            element.addEventListener("click", function(){
                const progress_id = this.getAttribute("data-progress-id");
                if (progress_id){
                    window.location.href = `/progress/detail?id=${progress_id}`;
                }
            });
        });
    }

    redirectToProfile();
})