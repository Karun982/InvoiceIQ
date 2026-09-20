const API_URL = "http://127.0.0.1:8000";

const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");

const selectedFile = document.getElementById("selected-file");
const fileName = document.getElementById("file-name");
const fileSize = document.getElementById("file-size");

const removeFileButton = document.getElementById("remove-file");
const processButton = document.getElementById("process-btn");

const processing = document.getElementById("processing");
const result = document.getElementById("upload-result");


let currentFile = null;


function selectFile(file) {

    if (!file) {
        return;
    }

    const allowed = [
        "application/pdf",
        "image/png",
        "image/jpeg"
    ];

    if (!allowed.includes(file.type)) {
        alert("Please select a PDF, PNG or JPG file.");
        return;
    }

    currentFile = file;

    fileName.textContent = file.name;

    const sizeKB = (file.size / 1024).toFixed(1);

    fileSize.textContent = `${sizeKB} KB`;

    selectedFile.style.display = "flex";

    processButton.disabled = false;

    result.style.display = "none";
}


fileInput.addEventListener("change", () => {

    selectFile(fileInput.files[0]);

});


dropZone.addEventListener("dragover", (event) => {

    event.preventDefault();

    dropZone.classList.add("dragover");

});


dropZone.addEventListener("dragleave", () => {

    dropZone.classList.remove("dragover");

});


dropZone.addEventListener("drop", (event) => {

    event.preventDefault();

    dropZone.classList.remove("dragover");

    const file = event.dataTransfer.files[0];

    selectFile(file);

});


removeFileButton.addEventListener("click", () => {

    currentFile = null;

    fileInput.value = "";

    selectedFile.style.display = "none";

    processButton.disabled = true;

});


processButton.addEventListener("click", async () => {

    if (!currentFile) {
        return;
    }

    processButton.disabled = true;

    processing.style.display = "block";

    result.style.display = "none";


    const formData = new FormData();

    formData.append("file", currentFile);


    try {

        const response = await fetch(
            `${API_URL}/api/documents/upload`,
            {
                method: "POST",
                body: formData
            }
        );


        const data = await response.json();


        if (!response.ok) {
            throw new Error(
                data.detail || "Document processing failed."
            );
        }


        result.style.display = "block";

        result.innerHTML = `
            <h3>Document processed successfully</h3>

            <p>
                <strong>Document:</strong>
                ${data.document.transaction_id || "N/A"}
            </p>

            <p>
                <strong>Type:</strong>
                ${data.document.document_type}
            </p>

            <p>
                <strong>Party:</strong>
                ${data.document.party_name || "N/A"}
            </p>

            <p>
                <strong>Total:</strong>
                ${data.document.currency || ""}
                ${data.document.total_amount || 0}
            </p>

            <br>

            <a
                href="dashboard.html"
                class="btn btn-primary"
            >
                View Dashboard
            </a>
        `;


    } catch (error) {

        result.style.display = "block";

        result.style.borderColor = "#6b3038";

        result.style.background = "#1c0e11";

        result.innerHTML = `
            <h3>Processing failed</h3>

            <p>
                ${error.message}
            </p>
        `;

    } finally {

        processing.style.display = "none";

        processButton.disabled = false;

    }

});