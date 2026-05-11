console.log("Tinda Express Loaded");

function previewParcelImage(event){

    const file = event.target.files[0];

    if(!file) return;

    const preview = document.getElementById("parcelPreview");
    const image = document.getElementById("parcelPreviewImg");

    image.src = URL.createObjectURL(file);

    preview.style.display = "block";
}