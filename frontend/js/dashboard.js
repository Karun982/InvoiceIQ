// ============================================================
// InvoiceIQ Dashboard
// ============================================================

const API_URL = "http://127.0.0.1:8000";


// ============================================================
// HELPERS
// ============================================================

function escapeHtml(value) {

    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


function formatCurrency(amount, currency = "INR") {

    const value = Number(amount || 0);

    if (currency === "INR" || currency === "₹") {
        return `₹${value.toLocaleString("en-IN", {
            maximumFractionDigits: 2
        })}`;
    }

    return `${currency} ${value.toLocaleString("en-IN", {
        maximumFractionDigits: 2
    })}`;
}


function formatDate(value) {

    if (!value) {
        return "—";
    }

    return String(value);
}


// ============================================================
// API HELPER
// ============================================================

async function apiFetch(endpoint, options = {}) {

    const response = await fetch(
        `${API_URL}${endpoint}`,
        {
            ...options,

            headers: {
                "Accept": "application/json",
                ...(options.headers || {})
            }
        }
    );


    if (!response.ok) {

        let errorMessage =
            `Request failed (${response.status})`;

        try {

            const errorData =
                await response.json();

            if (errorData.detail) {
                errorMessage =
                    errorData.detail;
            }

        } catch (_) {
            // Ignore JSON parsing error
        }

        throw new Error(errorMessage);
    }


    return await response.json();
}


// ============================================================
// LOAD DASHBOARD
// ============================================================

async function loadDashboard() {

    console.log("Loading InvoiceIQ dashboard...");


    try {

        // ----------------------------------------------------
        // LOAD ANALYTICS
        // ----------------------------------------------------

        const summary =
            await apiFetch(
                "/api/analytics/summary"
            );


        console.log(
            "Analytics:",
            summary
        );


        renderStats(summary);

        renderChart(summary);


        // ----------------------------------------------------
        // LOAD DOCUMENTS
        // ----------------------------------------------------

        const documentsResponse =
            await apiFetch(
                "/api/documents"
            );


        console.log(
            "Documents:",
            documentsResponse
        );


        let documents =
            documentsResponse;


        // Supports:
        //
        // [...]
        //
        // OR
        //
        // { documents: [...] }

        if (
            documentsResponse &&
            Array.isArray(
                documentsResponse.documents
            )
        ) {

            documents =
                documentsResponse.documents;
        }


        if (!Array.isArray(documents)) {
            documents = [];
        }


        renderDocuments(documents);


    } catch (error) {

        console.error(
            "Dashboard loading error:",
            error
        );


        const documentsContainer =
            window.document.getElementById(
                "documents"
            );


        if (documentsContainer) {

            documentsContainer.innerHTML = `

                <div class="empty">

                    <strong>
                        Failed to load dashboard.
                    </strong>

                    <br>

                    <small>
                        ${escapeHtml(error.message)}
                    </small>

                </div>

            `;
        }
    }
}


// ============================================================
// RENDER STAT CARDS
// ============================================================

function renderStats(summary) {

    const revenue =
        Number(
            summary.revenue ??
            summary.total_revenue ??
            0
        );


    const purchases =
        Number(
            summary.purchases ??
            summary.total_purchases ??
            0
        );


    const expenses =
        Number(
            summary.expenses ??
            summary.total_expenses ??
            0
        );


    const profit =
        Number(
            summary.estimated_profit ??
            summary.profit ??
            (
                revenue -
                purchases -
                expenses
            )
        );


    const documentCount =
        Number(
            summary.document_count ??
            summary.total_documents ??
            summary.documents_count ??
            0
        );


    // --------------------------------------------------------
    // REVENUE
    // --------------------------------------------------------

    const revenueElement =
        window.document.getElementById(
            "revenue"
        );


    if (revenueElement) {

        revenueElement.textContent =
            formatCurrency(revenue);
    }


    // --------------------------------------------------------
    // PURCHASES
    // --------------------------------------------------------

    const purchasesElement =
        window.document.getElementById(
            "purchases"
        );


    if (purchasesElement) {

        purchasesElement.textContent =
            formatCurrency(purchases);
    }


    // --------------------------------------------------------
    // EXPENSES
    // --------------------------------------------------------

    const expensesElement =
        window.document.getElementById(
            "expenses"
        );


    if (expensesElement) {

        expensesElement.textContent =
            formatCurrency(expenses);
    }


    // --------------------------------------------------------
    // PROFIT
    // --------------------------------------------------------

    const profitElement =
        window.document.getElementById(
            "profit"
        );


    if (profitElement) {

        profitElement.textContent =
            formatCurrency(profit);
    }


    // --------------------------------------------------------
    // DOCUMENT COUNT
    // --------------------------------------------------------

    const countElement =
        window.document.getElementById(
            "doc-count"
        );


    if (countElement) {

        countElement.textContent =
            `${documentCount} ${
                documentCount === 1
                    ? "document"
                    : "documents"
            }`;
    }
}


// ============================================================
// FINANCIAL CHART
// ============================================================

function renderChart(summary) {

    const chart =
        window.document.getElementById(
            "chart"
        );


    if (!chart) {

        console.error(
            "Chart element not found."
        );

        return;
    }


    const revenue =
        Number(
            summary.revenue ??
            summary.total_revenue ??
            0
        );


    const purchases =
        Number(
            summary.purchases ??
            summary.total_purchases ??
            0
        );


    const expenses =
        Number(
            summary.expenses ??
            summary.total_expenses ??
            0
        );


    const data = [

        {
            label: "Revenue",
            value: revenue
        },

        {
            label: "Purchases",
            value: purchases
        },

        {
            label: "Expenses",
            value: expenses
        }

    ];


    const maxValue =
        Math.max(
            ...data.map(
                item => item.value
            ),
            1
        );


    chart.innerHTML = "";


    data.forEach(item => {

        const column =
            window.document.createElement(
                "div"
            );


        column.className =
            "chart-column";


        const height =
            item.value === 0
                ? 3
                : Math.max(
                    (item.value / maxValue) * 80,
                    5
                );


        column.innerHTML = `

            <div
                class="chart-bar"
                style="height:${height}%"
            ></div>

            <div class="chart-label">
                ${escapeHtml(item.label)}
            </div>

            <div class="chart-value">
                ${escapeHtml(
                    formatCurrency(item.value)
                )}
            </div>

        `;


        chart.appendChild(column);

    });
}


// ============================================================
// RENDER DOCUMENTS
// ============================================================

function renderDocuments(documents) {

    const container =
        window.document.getElementById(
            "documents"
        );


    if (!container) {

        console.error(
            "Documents container not found."
        );

        return;
    }


    if (
        !Array.isArray(documents) ||
        documents.length === 0
    ) {

        container.innerHTML = `

            <div class="empty">

                <strong>
                    No documents yet.
                </strong>

                <br>

                <small>
                    Upload an invoice to get started.
                </small>

            </div>

        `;

        return;
    }


    // Newest first
    const recentDocuments =
        [...documents].reverse();


    container.innerHTML =
        recentDocuments
            .map(doc => {

                const id =
                    Number(doc.id);


                const transactionId =
                    doc.transaction_id ||
                    "Untitled";


                const party =
                    doc.party_name ||
                    "Unknown party";


                const type =
                    String(
                        doc.document_type ||
                        "OTHER"
                    ).toUpperCase();


                const amount =
                    Number(
                        doc.total_amount ||
                        0
                    );


                const currency =
                    doc.currency ||
                    "INR";


                return `

                    <div
                        class="document-row"
                        data-document-id="${id}"
                        onclick="openDocumentDetails(${id})"
                        role="button"
                        tabindex="0"
                        style="
                            cursor:pointer;
                            pointer-events:auto;
                            position:relative;
                            z-index:10;
                        "
                    >

                        <div class="document-icon">

                            ${getDocumentIcon(type)}

                        </div>


                        <div class="document-info">

                            <strong>

                                ${escapeHtml(
                                    transactionId
                                )}

                            </strong>


                            <span>

                                ${escapeHtml(
                                    party
                                )}

                            </span>

                        </div>


                        <div class="document-amount">

                            <strong>

                                ${escapeHtml(
                                    formatCurrency(
                                        amount,
                                        currency
                                    )
                                )}

                            </strong>


                            <span>

                                ${escapeHtml(type)}

                            </span>

                        </div>

                    </div>

                `;

            })
            .join("");
}


// ============================================================
// CREATE DOCUMENT ROW
// ============================================================

function createDocumentRow(doc) {

    const id =
        Number(doc.id);


    const transactionId =
        doc.transaction_id ||
        "Untitled document";


    const partyName =
        doc.party_name ||
        "Unknown party";


    const type =
        String(
            doc.document_type ||
            "OTHER"
        ).toUpperCase();


    const amount =
        Number(
            doc.total_amount ||
            0
        );


    const currency =
        doc.currency ||
        "INR";


    return `

        <div
            class="document-row"
            data-document-id="${id}"
            onclick="openDocumentDetails(${id})"
            role="button"
            tabindex="0"
            style="
                cursor:pointer;
                pointer-events:auto;
                position:relative;
                z-index:10;
            "
        >

            <div class="document-icon">

                ${getDocumentIcon(type)}

            </div>


            <div class="document-info">

                <strong>

                    ${escapeHtml(
                        transactionId
                    )}

                </strong>


                <span>

                    ${escapeHtml(
                        partyName
                    )}

                </span>

            </div>


            <div class="document-amount">

                <strong>

                    ${escapeHtml(
                        formatCurrency(
                            amount,
                            currency
                        )
                    )}

                </strong>


                <span>

                    ${escapeHtml(type)}

                </span>

            </div>

        </div>

    `;
}


// ============================================================
// DOCUMENT ICON
// ============================================================

function getDocumentIcon(type) {

    if (type === "SALES") {
        return "↗";
    }


    if (type === "PURCHASE") {
        return "↓";
    }


    if (type === "EXPENSE") {
        return "○";
    }


    return "•";
}


// ============================================================
// DOCUMENT DETAILS MODAL
// ============================================================

function createDocumentModal() {

    let modal =
        window.document.getElementById(
            "document-details-modal"
        );


    // Modal already exists
    if (modal) {
        return modal;
    }


    // --------------------------------------------------------
    // CREATE MODAL
    // --------------------------------------------------------

    modal =
        window.document.createElement(
            "div"
        );


    modal.id =
        "document-details-modal";


    modal.innerHTML = `

        <!-- BACKDROP -->

        <div
            id="document-details-backdrop"
            style="
                position:fixed;
                inset:0;
                background:rgba(0,0,0,0.75);
                z-index:9998;
            "
        ></div>


        <!-- MODAL -->

        <div
            id="document-details-box"
            style="
                position:fixed;
                top:50%;
                left:50%;
                transform:translate(-50%, -50%);
                width:min(760px, 90vw);
                max-height:85vh;
                overflow-y:auto;
                background:#101116;
                color:#ffffff;
                border:1px solid #292c38;
                border-radius:18px;
                z-index:9999;
                box-shadow:0 25px 80px rgba(0,0,0,0.6);
            "
        >

            <!-- HEADER -->

            <div
                style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                    padding:24px;
                    border-bottom:1px solid #292c38;
                "
            >

                <div>

                    <div
                        style="
                            font-size:11px;
                            letter-spacing:1.5px;
                            color:#85889a;
                            margin-bottom:5px;
                        "
                    >
                        DOCUMENT DETAILS
                    </div>


                    <h2
                        style="
                            margin:0;
                            font-size:24px;
                        "
                    >
                        Document
                    </h2>

                </div>


                <button
                    id="document-details-close"
                    type="button"
                    aria-label="Close"
                    style="
                        width:38px;
                        height:38px;
                        border:1px solid #30333f;
                        border-radius:10px;
                        background:#181a22;
                        color:white;
                        font-size:22px;
                        cursor:pointer;
                    "
                >
                    ×
                </button>

            </div>


            <!-- CONTENT -->

            <div
                id="document-details-content"
                style="
                    padding:24px;
                "
            >
                Loading...
            </div>

        </div>

    `;


    window.document.body.appendChild(
        modal
    );


    // --------------------------------------------------------
    // CLOSE BUTTON
    // --------------------------------------------------------

    const closeButton =
        window.document.getElementById(
            "document-details-close"
        );


    if (closeButton) {

        closeButton.onclick =
            closeDocumentDetails;
    }


    // --------------------------------------------------------
    // BACKDROP
    // --------------------------------------------------------

    const backdrop =
        window.document.getElementById(
            "document-details-backdrop"
        );


    if (backdrop) {

        backdrop.onclick =
            closeDocumentDetails;
    }


    return modal;
}


// ============================================================
// OPEN DOCUMENT DETAILS
// ============================================================

async function openDocumentDetails(
    documentId
) {

    // ========================================================
    // SAVE SELECTED INVOICE FOR AI ASSISTANT
    // ========================================================

    localStorage.setItem(
        "selectedDocumentId",
        String(documentId)
    );


    console.log(
        "Opening document:",
        documentId
    );


    // Create modal
    const modal =
        createDocumentModal();


    const content =
        window.document.getElementById(
            "document-details-content"
        );


    if (!modal || !content) {

        console.error(
            "Document modal could not be created."
        );

        return;
    }


    // --------------------------------------------------------
    // FORCE MODAL VISIBLE
    // --------------------------------------------------------

    modal.style.display =
        "block";


    modal.style.position =
        "fixed";


    modal.style.inset =
        "0";


    modal.style.zIndex =
        "9997";


    // --------------------------------------------------------
    // LOADING STATE
    // --------------------------------------------------------

    content.innerHTML = `

        <div
            style="
                padding:30px;
                text-align:center;
                color:#999;
            "
        >
            Loading document...
        </div>

    `;


    try {

        // ----------------------------------------------------
        // API REQUEST
        // ----------------------------------------------------

        const response =
            await fetch(
                `${API_URL}/api/documents/${encodeURIComponent(
                    documentId
                )}`,
                {
                    method: "GET",

                    headers: {
                        "Accept":
                            "application/json"
                    }
                }
            );


        console.log(
            "Document API status:",
            response.status
        );


        if (!response.ok) {

            let message =
                `Failed to load document (${response.status})`;


            try {

                const errorData =
                    await response.json();


                if (errorData.detail) {

                    message =
                        errorData.detail;
                }

            } catch (_) {
                // Ignore
            }


            throw new Error(
                message
            );
        }


        const doc =
            await response.json();


        console.log(
            "Document received:",
            doc
        );


        renderDocumentDetails(
            doc
        );


    } catch (error) {

        console.error(
            "Document details error:",
            error
        );


        content.innerHTML = `

            <div
                style="
                    padding:18px;
                    background:#351820;
                    border:1px solid #7b2939;
                    border-radius:10px;
                    color:#ff7187;
                "
            >

                ${escapeHtml(
                    error.message
                )}

            </div>

        `;
    }
}


// ============================================================
// RENDER DOCUMENT DETAILS
// ============================================================

function renderDocumentDetails(doc) {

    const content =
        window.document.getElementById(
            "document-details-content"
        );


    if (!content) {

        console.error(
            "Document details content not found."
        );

        return;
    }


    const type =
        String(
            doc.document_type ||
            "OTHER"
        ).toUpperCase();


    const currency =
        doc.currency ||
        "INR";


    const items =
        Array.isArray(doc.items)
            ? doc.items
            : [];


    content.innerHTML = `

        <!-- DOCUMENT TYPE -->

        <div
            style="
                display:inline-block;
                padding:7px 12px;
                border-radius:999px;
                background:#211c48;
                color:#a99cff;
                font-size:12px;
                font-weight:700;
                letter-spacing:.5px;
                margin-bottom:20px;
            "
        >
            ${escapeHtml(type)}
        </div>


        <!-- BASIC DETAILS -->

        <div
            style="
                display:grid;
                grid-template-columns:
                    repeat(
                        auto-fit,
                        minmax(200px, 1fr)
                    );
                gap:12px;
                margin-bottom:20px;
            "
        >

            ${detailCard(
                "Transaction ID",
                doc.transaction_id
            )}


            ${detailCard(
                "Party",
                doc.party_name
            )}


            ${detailCard(
                "Transaction Date",
                formatDate(
                    doc.transaction_date
                )
            )}


            ${detailCard(
                "Due Date",
                formatDate(
                    doc.due_date
                )
            )}


            ${detailCard(
                "Currency",
                currency
            )}


            ${detailCard(
                "Payment Status",
                doc.payment_status
            )}

        </div>


        <!-- FINANCIAL DETAILS -->

        <div
            style="
                display:grid;
                grid-template-columns:
                    repeat(
                        3,
                        1fr
                    );
                gap:12px;
                margin-bottom:24px;
            "
        >

            ${financialCard(
                "Subtotal",
                formatCurrency(
                    doc.subtotal,
                    currency
                )
            )}


            ${financialCard(
                "Tax",
                formatCurrency(
                    doc.tax,
                    currency
                )
            )}


            ${financialCard(
                "Total",
                formatCurrency(
                    doc.total_amount,
                    currency
                )
            )}

        </div>


        <!-- ASK AI ABOUT THIS INVOICE -->

        <div
            style="
                margin-bottom:24px;
                padding:16px;
                border:1px solid #292c38;
                background:#15171e;
                border-radius:12px;
            "
        >
            <button
                type="button"
                onclick="openInvoiceChat(${Number(doc.id)})"
                style="
                    width:100%;
                    padding:13px 18px;
                    border:0;
                    border-radius:10px;
                    background:#5b4cff;
                    color:#ffffff;
                    font-size:14px;
                    font-weight:700;
                    cursor:pointer;
                "
            >
                Ask AI about this invoice
            </button>
        </div>


        <!-- LINE ITEMS -->

        <div>

            <div
                style="
                    font-size:14px;
                    font-weight:700;
                    margin-bottom:12px;
                "
            >
                Line Items
            </div>


            ${
                items.length
                    ? createItemsTable(
                        items,
                        currency
                    )
                    : `
                        <div
                            style="
                                padding:20px;
                                border:1px solid #292c38;
                                border-radius:10px;
                                color:#888;
                            "
                        >
                            No line items available.
                        </div>
                    `
            }

        </div>

    `;
}


// ============================================================
// DETAIL CARD
// ============================================================

function detailCard(
    label,
    value
) {


    const displayValue =
        value === null ||
        value === undefined ||
        value === ""
            ? "—"
            : value;


    return `

        <div
            style="
                padding:16px;
                border:1px solid #292c38;
                background:#15171e;
                border-radius:12px;
            "
        >

            <span
                style="
                    display:block;
                    color:#85889a;
                    font-size:11px;
                    text-transform:uppercase;
                    letter-spacing:.7px;
                    margin-bottom:7px;
                "
            >
                ${escapeHtml(label)}
            </span>


            <strong
                style="
                    display:block;
                    color:#ffffff;
                    font-size:14px;
                    word-break:break-word;
                "
            >
                ${escapeHtml(displayValue)}
            </strong>

        </div>

    `;
}


// ============================================================
// FINANCIAL CARD
// ============================================================

function financialCard(
    label,
    value
) {


    return `

        <div
            style="
                padding:18px;
                border:1px solid #292c38;
                background:#15171e;
                border-radius:12px;
            "
        >

            <span
                style="
                    display:block;
                    color:#85889a;
                    font-size:11px;
                    text-transform:uppercase;
                    letter-spacing:.7px;
                    margin-bottom:8px;
                "
            >
                ${escapeHtml(label)}
            </span>


            <strong
                style="
                    display:block;
                    color:#ffffff;
                    font-size:18px;
                "
            >
                ${escapeHtml(value)}
            </strong>

        </div>

    `;
}


// ============================================================
// LINE ITEMS TABLE
// ============================================================

function createItemsTable(
    items,
    currency
) {


    return `

        <div
            style="
                overflow-x:auto;
                border:1px solid #292c38;
                border-radius:12px;
            "
        >

            <table
                style="
                    width:100%;
                    border-collapse:collapse;
                    min-width:600px;
                "
            >

                <thead>

                    <tr
                        style="
                            background:#15171e;
                            border-bottom:1px solid #292c38;
                        "
                    >

                        <th
                            style="
                                text-align:left;
                                padding:14px;
                                color:#85889a;
                                font-size:12px;
                            "
                        >
                            Description
                        </th>


                        <th
                            style="
                                text-align:left;
                                padding:14px;
                                color:#85889a;
                                font-size:12px;
                            "
                        >
                            Quantity
                        </th>


                        <th
                            style="
                                text-align:left;
                                padding:14px;
                                color:#85889a;
                                font-size:12px;
                            "
                        >
                            Unit Price
                        </th>


                        <th
                            style="
                                text-align:left;
                                padding:14px;
                                color:#85889a;
                                font-size:12px;
                            "
                        >
                            Amount
                        </th>

                    </tr>

                </thead>


                <tbody>

                    ${
                        items
                            .map(
                                item => `

                                    <tr
                                        style="
                                            border-bottom:1px solid #292c38;
                                        "
                                    >

                                        <td
                                            style="
                                                padding:14px;
                                                color:#ffffff;
                                            "
                                        >
                                            ${escapeHtml(
                                                item.description ||
                                                "—"
                                            )}
                                        </td>


                                        <td
                                            style="
                                                padding:14px;
                                                color:#cccccc;
                                            "
                                        >
                                            ${escapeHtml(
                                                item.quantity ??
                                                "—"
                                            )}
                                        </td>


                                        <td
                                            style="
                                                padding:14px;
                                                color:#cccccc;
                                            "
                                        >
                                            ${escapeHtml(
                                                formatCurrency(
                                                    item.unit_price,
                                                    currency
                                                )
                                            )}
                                        </td>


                                        <td
                                            style="
                                                padding:14px;
                                                color:#ffffff;
                                            "
                                        >
                                            <strong>
                                                ${escapeHtml(
                                                    formatCurrency(
                                                        item.amount,
                                                        currency
                                                    )
                                                )}
                                            </strong>
                                        </td>

                                    </tr>

                                `
                            )
                            .join("")
                    }

                </tbody>

            </table>

        </div>

    `;
}


// ============================================================
// OPEN AI CHAT FOR SELECTED INVOICE
// ============================================================

function openInvoiceChat(documentId) {

    const id = Number(documentId);

    if (!Number.isInteger(id) || id <= 0) {

        console.error(
            "Invalid document ID:",
            documentId
        );

        return;
    }

    localStorage.setItem(
        "selectedDocumentId",
        String(id)
    );

    window.location.href =
        `chat.html?document_id=${encodeURIComponent(id)}`;
}


// ============================================================
// CLOSE DOCUMENT DETAILS
// ============================================================

function closeDocumentDetails() {

    const modal =
        window.document.getElementById(
            "document-details-modal"
        );


    if (modal) {

        modal.style.display =
            "none";
    }
}


// ============================================================
// RESET DEMO DATA
// ============================================================

function setupResetButton() {

    const resetButton =
        window.document.getElementById(
            "reset-demo-btn"
        );


    if (!resetButton) {

        console.error(
            "Reset button #reset-demo-btn not found."
        );

        return;
    }


    console.log(
        "Reset button connected."
    );


    resetButton.addEventListener(
        "click",
        async () => {

            const confirmed =
                window.confirm(
                    "Are you sure you want to delete all demo data?"
                );


            if (!confirmed) {
                return;
            }


            const originalText =
                resetButton.textContent;


            resetButton.disabled =
                true;


            resetButton.textContent =
                "Resetting...";


            try {

                const result =
                    await apiFetch(
                        "/api/reset",
                        {
                            method: "POST"
                        }
                    );


                console.log(
                    "Reset result:",
                    result
                );


                if (!result.success) {

                    throw new Error(
                        result.message ||
                        "Reset failed."
                    );
                }


                // Reload dashboard
                window.location.reload();


            } catch (error) {

                console.error(
                    "Reset error:",
                    error
                );


                window.alert(
                    `Reset failed: ${error.message}`
                );


                resetButton.disabled =
                    false;


                resetButton.textContent =
                    originalText;
            }

        }
    );
}


// ============================================================
// KEYBOARD SUPPORT
// ============================================================

window.document.addEventListener(
    "keydown",
    event => {

        // ESC closes modal
        if (event.key === "Escape") {

            closeDocumentDetails();
        }


        // ENTER opens focused document
        if (
            event.key === "Enter" &&
            event.target.classList &&
            event.target.classList.contains(
                "document-row"
            )
        ) {

            const id =
                event.target.getAttribute(
                    "data-document-id"
                );


            if (id) {

                openDocumentDetails(
                    Number(id)
                );
            }
        }

    }
);


// ============================================================
// START DASHBOARD
// ============================================================

window.addEventListener(
    "DOMContentLoaded",
    () => {

        console.log(
            "InvoiceIQ dashboard started."
        );


        setupResetButton();


        loadDashboard();

    }
);


// ============================================================
// MAKE FUNCTIONS GLOBALLY AVAILABLE
// ============================================================
//
// Required because document rows use:
// onclick="openDocumentDetails(...)"
//
// ============================================================

window.openDocumentDetails =
    openDocumentDetails;


window.closeDocumentDetails =
    closeDocumentDetails;


window.openInvoiceChat =
    openInvoiceChat;