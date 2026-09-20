const API_URL = "http://127.0.0.1:8000";

const money = (value) =>
    `₹${Number(value || 0).toLocaleString("en-IN", {
        maximumFractionDigits: 2
    })}`;


async function loadDashboard() {

    try {

        const [summaryRes, docsRes] = await Promise.all([
            fetch(`${API_URL}/api/analytics/summary`),
            fetch(`${API_URL}/api/documents`)
        ]);


        if (!summaryRes.ok) {
            throw new Error("Failed to load analytics");
        }

        if (!docsRes.ok) {
            throw new Error("Failed to load documents");
        }


        const summary = await summaryRes.json();
        const docs = await docsRes.json();


        document.getElementById("revenue").textContent =
            money(summary.revenue);


        document.getElementById("purchases").textContent =
            money(summary.purchases);


        document.getElementById("expenses").textContent =
            money(summary.expenses);


        document.getElementById("profit").textContent =
            money(summary.estimated_profit);


        document.getElementById("doc-count").textContent =
            `${summary.document_count || 0} documents`;


        renderChart(summary);


        renderDocuments(
            Array.isArray(docs)
                ? docs
                : (docs.documents || [])
        );


    } catch (error) {

        console.error(
            "InvoiceIQ dashboard error:",
            error
        );


        document
            .querySelectorAll(".stat-value")
            .forEach(element => {
                element.textContent = "—";
            });


        const documents =
            document.getElementById("documents");


        if (documents) {

            documents.innerHTML = `
                <div style="
                    padding:20px;
                    color:var(--muted);
                    font-size:12px;
                ">
                    Could not load dashboard data.
                </div>
            `;

        }

    }

}


/* =========================================================
   FINANCIAL CHART
========================================================= */

function renderChart(summary) {

    const chart =
        document.getElementById("chart");


    if (!chart) {
        return;
    }


    const values = [

        {
            label: "Revenue",
            value: Number(summary.revenue || 0)
        },

        {
            label: "Purchases",
            value: Number(summary.purchases || 0)
        },

        {
            label: "Expenses",
            value: Number(summary.expenses || 0)
        }

    ];


    const max =
        Math.max(
            ...values.map(item => item.value),
            1
        );


    chart.innerHTML = `

        <div style="
            width:100%;
            height:100%;
            min-height:240px;
            display:flex;
            align-items:flex-end;
            gap:28px;
            padding:35px 25px 15px;
        ">

            ${values.map(item => {

                const height =
                    Math.max(
                        6,
                        (item.value / max) * 100
                    );


                return `

                    <div style="
                        flex:1;
                        height:100%;
                        display:flex;
                        flex-direction:column;
                        justify-content:flex-end;
                        align-items:center;
                        gap:10px;
                    ">

                        <strong style="
                            font-family:'Space Grotesk',
                            sans-serif;
                            font-size:11px;
                            color:var(--text);
                        ">
                            ${money(item.value)}
                        </strong>


                        <div style="
                            width:min(75px,65%);
                            height:${height}%;
                            min-height:6px;
                            border-radius:10px 10px 4px 4px;
                            background:linear-gradient(
                                to top,
                                var(--primary),
                                #9b91ff
                            );
                            box-shadow:
                                0 10px 25px
                                rgba(91,76,255,.18);
                            transition:
                                height .5s ease;
                        "></div>


                        <span style="
                            color:var(--muted);
                            font-size:10px;
                            font-weight:600;
                        ">
                            ${item.label}
                        </span>

                    </div>

                `;

            }).join("")}

        </div>
    `;

}


/* =========================================================
   RECENT DOCUMENTS
========================================================= */

function renderDocuments(documents) {

    const box =
        document.getElementById("documents");


    if (!box) {
        return;
    }


    if (!documents.length) {

        box.innerHTML = `

            <div style="
                padding:30px 10px;
                text-align:center;
                color:var(--muted);
                font-size:12px;
            ">

                No documents uploaded yet.

            </div>

        `;

        return;
    }


    box.innerHTML = documents
        .slice(0, 6)
        .map(document => {

            const type =
                String(
                    document.document_type ||
                    "OTHER"
                ).toUpperCase();


            const transactionId =
                document.transaction_id ||
                "Document";


            const party =
                document.party_name ||
                "Unknown party";


            return `

                <div class="document-row">

                    <div class="document-icon">
                        ${getDocumentIcon(type)}
                    </div>


                    <div class="document-info">

                        <strong>
                            ${escapeHtml(transactionId)}
                        </strong>

                        <span>
                            ${escapeHtml(party)}
                        </span>

                    </div>


                    <div
                        class="document-amount">

                        ${money(
                            document.total_amount
                        )}

                    </div>

                </div>

            `;

        })
        .join("");

}


/* =========================================================
   DOCUMENT ICON
========================================================= */

function getDocumentIcon(type) {

    switch (type) {

        case "SALES":
            return "↗";

        case "PURCHASE":
            return "↓";

        case "EXPENSE":
            return "₹";

        default:
            return "DOC";

    }

}


/* =========================================================
   HTML ESCAPE
========================================================= */

function escapeHtml(value) {

    return String(value)
        .replace(/[&<>"']/g, character => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        }[character]));

}


/* =========================================================
   START
========================================================= */

loadDashboard();