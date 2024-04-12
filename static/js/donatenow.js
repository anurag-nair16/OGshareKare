function displayImages() {
    var input = document.getElementById('productImage');
    var imageContainer = document.getElementById('uploadedImages');
    
    if (input.files && input.files.length > 0) {
        for (var i = 0; i < input.files.length; i++) {
            var reader = new FileReader();
            reader.onload = function (e) {
                imageContainer.innerHTML += '<img class="testimage" src="' + e.target.result + '" alt="Uploaded Image">';
            };
            reader.readAsDataURL(input.files[i]);
        }
    }
}

const element = document.getElementById("myBtn");
element.addEventListener("click", displayImages);                                                                       