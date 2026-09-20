const API_URL = "http://127.0.0.1:8000";


async function loadDashboard() {

    try {

        const response = await fetch(
            `${API_URL}/api/analytics/summary`
        );

        if (!response.ok) {
            throw new Error("Unable to load analytics.");
        }

        const data = await response.json();


        document.getElementById("revenue").textContent =
            `₹${Number(data.revenue || 0).toLocaleString("en-IN")}`;

        document.getElementById("purchases").textContent =
            `₹${Number(data.purchases || 0).toLocaleString("en-IN")}`;

        document.getElementById("expenses").textContent =
            `₹${Number(data.expenses || 0).toLocaleString("en-IN")}`;

        document.getElementById("profit").textContent =
            `₹${Number(data.estimated_profit || 0).toLocaleString("en-IN")}`;


    } catch (error) {

        console.log(
            "Analytics API not connected yet:",
            error.message
        );

    }


    loadDocuments();

}


async function loadDocuments() {

    try {

        const response = await fetch(
            `${API_URL}/api/documents`
        );

        if (!response.ok) {
            throw new Error("Unable to load documents.");
        }

        const data = await response.json();

        const documents = data.documents || [];

        const container =
            document.getElementById("documents-container");


        if (documents.length === 0) {
            return;
        }


        container.innerHTML = "";


        let sales = 0;
        let purchases = 0;
        let expenses = 0;
        let other = 0;


        documents.slice(0, 8).forEach((doc) => {

            const row = document.createElement("div");

            row.className = "document-row";


            row.innerHTML = `
                <div class="document-main">
                    <strong>
                        ${doc.transaction_id || "Unnamed document"}
                    </strong>

                    <span>
                        ${doc.party_name || "Unknown party"}
                    </span>
                </div>

                <div class="document-type">
                    <strong>
                        ${doc.document_type}
                    </strong>

                    <span>
                        ${doc.currency || ""}
                        ${doc.total_amount || 0}
                    </span>
                </div>
            `;


            container.appendChild(row);


            if (doc.document_type === "SALES") {
                sales++;
            } else if (doc.document_type === "PURCHASE") {
                purchases++;
            } else if (doc.document_type === "EXPENSE") {
                expenses++;
            } else {
                other++;
            }

        });


        document.getElementById("sales-count").textContent = sales;

        document.getElementById("purchase-count").textContent =
            purchases;

        document.getElementById("expense-count").textContent =
            expenses;

        document.getElementById("other-count").textContent =
            other;


    } catch (error) {

        console.log(
            "Documents API not connected yet:",
            error.message
        );

    }

}


loadDashboard();