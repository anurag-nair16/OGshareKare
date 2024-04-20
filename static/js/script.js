function validateForm() {
    var password = document.getElementById("password").value;
    var confirmPassword = document.getElementById("confirmPassword").value;

    if (password != confirmPassword) {
        alert("Passwords do not match");
        return false;
    }
    return true;
}


document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.querySelector('.hamburger');
    const navUL = document.querySelector('nav ul');

    // Toggle the menu when clicking the hamburger
    hamburger.addEventListener('click', function(event) {
        event.stopPropagation(); // Prevent the event from bubbling up
        navUL.classList.toggle('show');
    });

    // Close the menu when clicking outside of it
    document.body.addEventListener('click', function(event) {
        const isClickInsideNav = navUL.contains(event.target);
        const isClickInsideHamburger = hamburger.contains(event.target);

        if (!isClickInsideNav && !isClickInsideHamburger) {
            navUL.classList.remove('show');
        }
    });
});


function logout() {
    fetch('/logout/')
    .then(response => response.json())
    .then(data => {
        if(data.success) {
            window.location.href = '/login/';
        } else {
            alert('Logout failed');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

