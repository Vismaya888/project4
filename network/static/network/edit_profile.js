document.addEventListener('DOMContentLoaded', function() {
    // Preview profile picture
    document.getElementById('profile-pic-input').addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                document.querySelector('.profile-pic-preview').style.backgroundImage = `url(${e.target.result})`;
            }
            reader.readAsDataURL(file);
        }
    });

    // Preview cover photo
    document.getElementById('cover-input').addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                document.querySelector('.cover-preview').style.backgroundImage = `url(${e.target.result})`;
            }
            reader.readAsDataURL(file);
        }
    });
}); 