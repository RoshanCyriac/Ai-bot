document.addEventListener("DOMContentLoaded", function () {
    let inputField = document.getElementById("user-input");
    
    inputField.addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
            sendMessage();
        }
    });
});

function sendMessage(customMessage = null) {
    let inputField = document.getElementById("user-input");
    let userMessage = customMessage || inputField.value.trim();
    
    if (!userMessage) return;

    // Display user message in chatbox
    addMessage("You", userMessage);

    // Clear input field
    inputField.value = "";

    // Show loading indicator
    addMessage("Bot", "Thinking...");

    // Send message to backend
    fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: userMessage })
    })
    .then(response => response.json())
    .then(data => {
        // Remove "Thinking..." message and show AI response
        removeLastMessage();
        addMessage("Bot", data.reply);
    })
    .catch(error => {
        console.error("Error:", error);
        removeLastMessage();
        addMessage("Bot", "Oops! Something went wrong.");
    });
}

function addMessage(sender, message) {
    let chatbox = document.getElementById("chatbox");
    let messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender.toLowerCase());
    messageDiv.innerHTML = `<strong>${sender}:</strong> ${message}`;
    chatbox.appendChild(messageDiv);

    // Auto-scroll to latest message
    chatbox.scrollTop = chatbox.scrollHeight;
}

function removeLastMessage() {
    let chatbox = document.getElementById("chatbox");
    let lastMessage = chatbox.lastElementChild;
    if (lastMessage) {
        chatbox.removeChild(lastMessage);
    }
}
