document.addEventListener("DOMContentLoaded", function () {

    const API_URL = "http://127.0.0.1:8000";

    const input = document.getElementById("file-input");
    const chooseBtn = document.getElementById("choose-btn");
    const uploadBtn = document.getElementById("upload-btn");

    const fileNameBox = document.getElementById("file-name");
    const filesList = document.getElementById("selected-files-list");
    const result = document.getElementById("result");
    const dropzone = document.getElementById("dropzone");


    console.log("InvoiceIQ upload.js loaded");


    if (!input || !chooseBtn || !uploadBtn || !fileNameBox || !filesList || !result) {
        console.error("InvoiceIQ upload elements are missing.");
        return;
    }


    // =====================================================
    // SELECTED FILES
    // =====================================================

    let selectedFiles = [];


    // =====================================================
    // CHOOSE DOCUMENTS
    // =====================================================

    chooseBtn.addEventListener("click", function (event) {

        event.preventDefault();

        /*
         * Do NOT clear input.value here.
         * We want multiple selections across multiple
         * Choose Documents clicks.
         */

        input.click();

    });


    // =====================================================
    // FILE SELECTION
    // =====================================================

    input.addEventListener("change", function () {

        const newlySelectedFiles =
            Array.from(input.files || []);


        console.log(
            "New files selected:",
            newlySelectedFiles.length
        );


        if (!newlySelectedFiles.length) {
            return;
        }


        /*
         * ADD new files to existing list.
         * Don't replace the old files.
         */

        newlySelectedFiles.forEach(function (file) {

            const alreadyExists =
                selectedFiles.some(function (existingFile) {

                    return (
                        existingFile.name === file.name &&
                        existingFile.size === file.size &&
                        existingFile.lastModified === file.lastModified
                    );

                });


            if (!alreadyExists) {
                selectedFiles.push(file);
            }

        });


        console.log(
            "Total selected files:",
            selectedFiles.length
        );


        renderSelectedFiles();

    });


    // =====================================================
    // DRAG & DROP
    // =====================================================

    if (dropzone) {

        ["dragenter", "dragover"].forEach(function (eventName) {

            dropzone.addEventListener(
                eventName,
                function (event) {

                    event.preventDefault();
                    event.stopPropagation();

                    dropzone.classList.add("dragover");

                }
            );

        });


        ["dragleave", "drop"].forEach(function (eventName) {

            dropzone.addEventListener(
                eventName,
                function (event) {

                    event.preventDefault();
                    event.stopPropagation();

                    dropzone.classList.remove("dragover");

                }
            );

        });


        dropzone.addEventListener(
            "drop",
            function (event) {

                const droppedFiles =
                    Array.from(
                        event.dataTransfer.files || []
                    );


                if (!droppedFiles.length) {
                    return;
                }


                droppedFiles.forEach(function (file) {

                    const alreadyExists =
                        selectedFiles.some(function (existingFile) {

                            return (
                                existingFile.name === file.name &&
                                existingFile.size === file.size &&
                                existingFile.lastModified === file.lastModified
                            );

                        });


                    if (!alreadyExists) {
                        selectedFiles.push(file);
                    }

                });


                renderSelectedFiles();

            }
        );

    }


    // =====================================================
    // RENDER FILE LIST
    // =====================================================

    function renderSelectedFiles() {

        if (!selectedFiles.length) {

            fileNameBox.style.display = "none";

            filesList.innerHTML = "";

            uploadBtn.style.display = "none";

            return;
        }


        fileNameBox.style.display = "block";

        uploadBtn.style.display = "inline-flex";

        uploadBtn.disabled = false;


        uploadBtn.textContent =
            `Process ${selectedFiles.length} document${
                selectedFiles.length === 1 ? "" : "s"
            } →`;


        filesList.innerHTML = "";


        selectedFiles.forEach(function (file, index) {

            const row =
                document.createElement("div");


            row.className =
                "selected-file-row";


            row.innerHTML = `

                <div class="selected-file-info">

                    <div class="selected-file-icon">
                        ${getFileExtension(file.name)}
                    </div>


                    <div>

                        <strong>
                            ${escapeHtml(file.name)}
                        </strong>

                        <span>
                            ${formatFileSize(file.size)}
                        </span>

                    </div>

                </div>


                <button
                    type="button"
                    class="remove-file-btn"
                    data-index="${index}"
                    title="Remove document"
                >
                    ×
                </button>

            `;


            filesList.appendChild(row);

        });


        // =================================================
        // REMOVE INDIVIDUAL FILE
        // =================================================

        filesList
            .querySelectorAll(".remove-file-btn")
            .forEach(function (button) {

                button.addEventListener(
                    "click",
                    function () {

                        const index =
                            Number(button.dataset.index);


                        selectedFiles.splice(
                            index,
                            1
                        );


                        renderSelectedFiles();

                    }
                );

            });

    }


    // =====================================================
    // PROCESS ALL DOCUMENTS
    // =====================================================

    uploadBtn.addEventListener(
        "click",
        async function (event) {

            event.preventDefault();


            if (!selectedFiles.length) {

                showError(
                    "Please select at least one document."
                );

                return;
            }


            uploadBtn.disabled = true;

            chooseBtn.disabled = true;


            result.style.display = "block";


            const totalFiles =
                selectedFiles.length;


            const results = [];


            // =================================================
            // PROCESS ONE BY ONE
            // =================================================

            for (
                let i = 0;
                i < totalFiles;
                i++
            ) {

                const file =
                    selectedFiles[i];


                result.innerHTML = `

                    <div>

                        <strong>
                            Processing document
                            ${i + 1}
                            of
                            ${totalFiles}
                        </strong>

                        <p style="margin-top:6px;">
                            ${escapeHtml(file.name)}
                        </p>

                    </div>

                `;


                try {

                    const formData =
                        new FormData();


                    formData.append(
                        "file",
                        file
                    );


                    const response =
                        await fetch(
                            `${API_URL}/api/documents/upload`,
                            {
                                method: "POST",
                                body: formData
                            }
                        );


                    let data;


                    try {

                        data =
                            await response.json();

                    } catch {

                        throw new Error(
                            "Server returned an invalid response."
                        );

                    }


                    if (!response.ok) {

                        throw new Error(
                            data.detail ||
                            "Document processing failed."
                        );

                    }


                    const uploadedDocument = data.document || data;

// Save the successfully uploaded invoice as the
// currently selected invoice for AI chat.
if (uploadedDocument.id) {
    localStorage.setItem(
        "selectedDocumentId",
        String(uploadedDocument.id)
    );

    console.log(
        "Selected invoice for AI chat:",
        uploadedDocument.id
    );
}

results.push({
    success: true,
    file: file.name,
    document: uploadedDocument
});


                } catch (error) {

                    console.error(
                        "InvoiceIQ processing error:",
                        file.name,
                        error
                    );


                    results.push({

                        success: false,

                        file: file.name,

                        error:
                            error.message ||
                            "Processing failed."

                    });

                }

            }


            showResults(results);


            uploadBtn.disabled = false;

            chooseBtn.disabled = false;

        }
    );


    // =====================================================
    // SHOW RESULTS
    // =====================================================

    function showResults(results) {

        const successful =
            results.filter(
                item => item.success
            );


        const failed =
            results.filter(
                item => !item.success
            );


        result.style.display = "block";


        result.innerHTML = `

            <div>

                <h3
                    style="
                        margin-bottom:16px;
                        font-family:'Space Grotesk',sans-serif;
                    "
                >
                    ${
                        failed.length === 0
                            ? "✓ All documents processed"
                            : "Processing completed"
                    }
                </h3>


                <div class="upload-results-list">

                    ${
                        results.map(function (item) {

                            if (item.success) {

                                const doc =
                                    item.document;


                                return `

                                    <div
                                        class="
                                            upload-result-item
                                            success
                                        "
                                    >

                                        <strong>
                                            ✓
                                            ${escapeHtml(
                                                item.file
                                            )}
                                        </strong>


                                        <span>
                                            ${escapeHtml(
                                                doc.document_type ||
                                                "OTHER"
                                            )}

                                            ·

                                            ${money(
                                                doc.total_amount
                                            )}
                                        </span>

                                    </div>

                                `;

                            }


                            return `

                                <div
                                    class="
                                        upload-result-item
                                        failed
                                    "
                                >

                                    <strong>
                                        ✕
                                        ${escapeHtml(
                                            item.file
                                        )}
                                    </strong>


                                    <span>
                                        ${escapeHtml(
                                            item.error
                                        )}
                                    </span>

                                </div>

                            `;

                        }).join("")
                    }

                </div>


                <p
                    style="
                        margin-top:14px;
                        color:var(--muted);
                        font-size:11px;
                    "
                >

                    ${successful.length}
                    of
                    ${results.length}
                    documents processed successfully.

                </p>


                ${
                    successful.length > 0
                        ? `
                            <a
                                href="dashboard.html"
                                class="btn btn-primary"
                                style="margin-top:12px;"
                            >
                                View dashboard →
                            </a>
                        `
                        : ""
                }

            </div>

        `;

    }


    // =====================================================
    // ERROR
    // =====================================================

    function showError(message) {

        result.style.display = "block";


        result.innerHTML = `

            <div>

                <strong
                    style="color:var(--red);"
                >
                    Upload error
                </strong>


                <p
                    style="
                        margin-top:7px;
                        color:var(--muted);
                    "
                >
                    ${escapeHtml(message)}
                </p>

            </div>

        `;

    }


    // =====================================================
    // FILE EXTENSION
    // =====================================================

    function getFileExtension(name) {

        const extension =
            name
                .split(".")
                .pop()
                .toUpperCase();


        if (extension === "JPEG") {
            return "JPG";
        }


        return extension;

    }


    // =====================================================
    // FILE SIZE
    // =====================================================

    function formatFileSize(bytes) {

        if (!bytes) {
            return "0 KB";
        }


        const kb =
            bytes / 1024;


        if (kb < 1024) {
            return `${kb.toFixed(1)} KB`;
        }


        return `${(
            kb / 1024
        ).toFixed(1)} MB`;

    }


    // =====================================================
    // MONEY
    // =====================================================

    function money(value) {

        return `₹${Number(
            value || 0
        ).toLocaleString(
            "en-IN",
            {
                maximumFractionDigits: 2
            }
        )}`;

    }


    // =====================================================
    // ESCAPE HTML
    // =====================================================

    function escapeHtml(value) {

        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");

    }

});