const API_URL = "http://127.0.0.1:8000";

const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const messages = document.getElementById("messages");


function addMessage(text, type) {

    const message = document.createElement("div");

    message.className = `message ${type}`;


    if (type === "ai") {

        message.innerHTML = `
            <div class="message-avatar">
                IQ
            </div>

            <div class="message-content">

                <span class="message-label">
                    InvoiceIQ AI
                </span>

                <p></p>

            </div>
        `;

        // AI response ko safely insert karo
        message.querySelector("p").textContent = text;

    } else {

        message.innerHTML = `
            <div class="message-content">
                <p></p>
            </div>
        `;

        // User input ko safely insert karo
        message.querySelector("p").textContent = text;
    }


    messages.appendChild(message);

    messages.scrollTop = messages.scrollHeight;
}


async function sendMessage(question) {

    addMessage(question, "user");


    try {

        const response = await fetch(
            `${API_URL}/api/chat`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    message: question
                })
            }
        );


        const data = await response.json();


        if (!response.ok) {
            throw new Error(
                data.detail || "AI request failed."
            );
        }


        // Backend /api/chat returns "answer"
        addMessage(
            data.answer,
            "ai"
        );


    } catch (error) {

        addMessage(
            `Unable to connect to InvoiceIQ AI: ${error.message}`,
            "ai"
        );

    }

}


form.addEventListener("submit", (event) => {

    event.preventDefault();

    const question = input.value.trim();


    if (!question) {
        return;
    }


    input.value = "";

    sendMessage(question);

});


document.querySelectorAll(".suggestions button")
    .forEach((button) => {

        button.addEventListener("click", () => {

            const question = button.textContent.trim();

            sendMessage(question);

        });

    });