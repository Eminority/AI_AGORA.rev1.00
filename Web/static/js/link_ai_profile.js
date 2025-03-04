document.addEventListener("DOMContentLoaded", function(){
    function redirectToProfile() {
        document.querySelectorAll(".ai_profile").forEach(function (element){
            element.addEventListener("click", function(){
                const profile_id = this.getAttribute("data-profile-id");
                if (profile_id){
                    window.location.href = `/profile/detail?id=${profile_id}`;
                }
            });
        });
    }

    redirectToProfile();
})