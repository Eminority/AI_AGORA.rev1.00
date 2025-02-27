document.addEventListener("DOMContentLoaded", function(){
    function redirectToProfile() {
        document.querySelectorAll(".progress_detail").forEach(function (element){
            element.addEventListener("click", function(){
                const profile_id = this.getAttribute("data-progress-id");
                if (profile_id){
                    window.location.href = `/progress/detail?id=${profile_id}`;
                }
            });
        });
    }

    redirectToProfile();
})