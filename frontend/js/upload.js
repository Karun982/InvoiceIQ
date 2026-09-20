document.addEventListener("DOMContentLoaded", () => {

    const API_URL = "http://127.0.0.1:8000";

    const input = document.getElementById("file-input");
    const dropzone = document.getElementById("dropzone");
    const chooseBtn = document.getElementById("choose-btn");
    const uploadBtn = document.getElementById("upload-btn");
    const nameBox = document.getElementById("file-name");
    const result = document.getElementById("result");

    let selectedFile = null;


    /* =====================================================
       SAFETY CHECK
    ===================================================== */

    if (
        !input ||
        !dropzone ||
        !chooseBtn ||
        !uploadBtn ||
        !nameBox ||
        !result
    ) {
        console.error("InvoiceIQ upload elements are missing.");
        return;
    }


    /* =====================================================
       CHOOSE FILE
    ===================================================== */

    chooseBtn.addEventListener("click", (event) => {

        event.preventDefault();

        input.value = "";

        input.click();

    });


    /* =====================================================
       FILE SELECTED
    ===================================================== */

    input.addEventListener("change", () => {

        const file = input.files && input.files[0];

        if (file) {
            selectFile(file);
        }

    });


    /* =====================================================
       DRAG & DROP
    ===================================================== */

    ["dragenter", "dragover"].forEach(eventName => {

        dropzone.addEventListener(eventName, (event) => {

            event.preventDefault();
            event.stopPropagation();

            dropzone.classList.add("dragover");

        });

    });


    ["dragleave", "drop"].forEach(eventName => {

        dropzone.addEventListener(eventName, (event) => {

            event.preventDefault();
            event.stopPropagation();

            dropzone.classList.remove("dragover");

        });

    });


    dropzone.addEventListener("drop", (event) => {

        const files = event.dataTransfer.files;

        if (!files || files.length === 0) {
            return;
        }

        selectFile(files[0]);

    });


    /* =====================================================
       SELECT FILE
    ===================================================== */

    function selectFile(file) {

        if (!file) {
            return;
        }


        const allowedTypes = [
            "application/pdf",
            "image/jpeg",
            "image/jpg",
            "image/png"
        ];


        const allowedExtensions = [
            ".pdf",
            ".jpg",
            ".jpeg",
            ".png"
        ];


        const fileName = file.name.toLowerCase();

        const validType =
            allowedTypes.includes(file.type) ||
            allowedExtensions.some(ext =>
                fileName.endsWith(ext)
            );


        if (!validType) {

            showError(
                "Please select a PDF, JPG, JPEG or PNG file."
            );

            return;
        }


        selectedFile = file;


        nameBox.textContent =
            `Selected: ${file.name}`;


        nameBox.style.display = "block";


        uploadBtn.style.display = "inline-flex";

        uploadBtn.disabled = false;

        uploadBtn.textContent =
            "Process document →";


        result.style.display = "none";

        result.innerHTML = "";


        dropzone.classList.add("file-selected");

    }


    /* =====================================================
       UPLOAD
    ===================================================== */

    uploadBtn.addEventListener("click", async (event) => {

        event.preventDefault();


        if (!selectedFile) {

            showError(
                "Please choose a document first."
            );

            return;
        }


        uploadBtn.disabled = true;

        uploadBtn.textContent =
            "Processing...";


        result.style.display = "block";

        result.innerHTML = `
            <div>
                <strong>Processing document...</strong>
                <p style="margin-top:6px;">
                    InvoiceIQ is extracting and analyzing your document.
                </p>
            </div>
        `;


        try {

            const formData = new FormData();

            formData.append(
                "file",
                selectedFile
            );


            const response = await fetch(
                `${API_URL}/api/documents/upload`,
                {
                    method: "POST",
                    body: formData
                }
            );


            let data;

            try {

                data = await response.json();

            } catch {

                throw new Error(
                    "The server returned an invalid response."
                );

            }


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    data.message ||
                    "Document upload failed."
                );

            }


            const document =
                data.document || data;


            showSuccess(document);


        } catch (error) {

            console.error(
                "InvoiceIQ upload error:",
                error
            );


            showError(
                error.message ||
                "Unable to process the document."
            );


        } finally {

            uploadBtn.disabled = false;

            uploadBtn.textContent =
                "Process document →";

        }

    });


    /* =====================================================
       SUCCESS
    ===================================================== */

    function showSuccess(document) {

        const total =
            Number(
                document.total_amount || 0
            );


        result.style.display = "block";


        result.innerHTML = `

            <div>

                <h3 style="
                    margin-bottom:18px;
                    font-family:'Space Grotesk',sans-serif;
                ">
                    ✓ Document processed
                </h3>


                <div style="
                    display:grid;
                    grid-template-columns:
                    repeat(2,minmax(0,1fr));
                    gap:12px;
                ">


                    <div style="
                        padding:14px;
                        border:1px solid var(--border);
                        border-radius:12px;
                        background:var(--surface);
                    ">

                        <small style="
                            display:block;
                            color:var(--muted);
                            font-size:10px;
                            margin-bottom:5px;
                        ">
                            DOCUMENT TYPE
                        </small>

                        <strong>
                            ${escapeHtml(
                                document.document_type || "—"
                            )}
                        </strong>

                    </div>


                    <div style="
                        padding:14px;
                        border:1px solid var(--border);
                        border-radius:12px;
                        background:var(--surface);
                    ">

                        <small style="
                            display:block;
                            color:var(--muted);
                            font-size:10px;
                            margin-bottom:5px;
                        ">
                            TRANSACTION ID
                        </small>

                        <strong>
                            ${escapeHtml(
                                document.transaction_id || "—"
                            )}
                        </strong>

                    </div>


                    <div style="
                        padding:14px;
                        border:1px solid var(--border);
                        border-radius:12px;
                        background:var(--surface);
                    ">

                        <small style="
                            display:block;
                            color:var(--muted);
                            font-size:10px;
                            margin-bottom:5px;
                        ">
                            PARTY
                        </small>

                        <strong>
                            ${escapeHtml(
                                document.party_name || "—"
                            )}
                        </strong>

                    </div>


                    <div style="
                        padding:14px;
                        border:1px solid var(--border);
                        border-radius:12px;
                        background:var(--surface);
                    ">

                        <small style="
                            display:block;
                            color:var(--muted);
                            font-size:10px;
                            margin-bottom:5px;
                        ">
                            TOTAL
                        </small>

                        <strong>
                            ₹${total.toLocaleString("en-IN")}
                        </strong>

                    </div>


                </div>

            </div>
        `;

    }


    /* =====================================================
       ERROR
    ===================================================== */

    function showError(message) {

        result.style.display = "block";


        result.innerHTML = `

            <div>

                <strong style="
                    color:var(--red);
                ">
                    Upload failed
                </strong>

                <p style="
                    margin-top:7px;
                    color:var(--muted);
                ">
                    ${escapeHtml(message)}
                </p>

            </div>

        `;

    }


    /* =====================================================
       HTML ESCAPE
    ===================================================== */

    function escapeHtml(value) {

        return String(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");

    }


});