// Global variables
let currentConversationId = null;
let reminders = [];

// Initialize the application
document.addEventListener("DOMContentLoaded", function() {
    // Set up event listeners
    const inputField = document.getElementById("user-input");
    inputField.addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            sendMessage();
        }
    });
    
    // Set up filter listeners
    if (document.getElementById("date-filter")) {
        document.getElementById("date-filter").addEventListener("change", loadReminders);
    }
    
    if (document.getElementById("show-completed")) {
        document.getElementById("show-completed").addEventListener("change", loadReminders);
    }
    
    // New chat button
    if (document.getElementById("new-chat-btn")) {
        document.getElementById("new-chat-btn").addEventListener("click", startNewChat);
    }
    
    // Load initial data
    if (typeof loadUpcomingReminders === 'function') {
        loadUpcomingReminders();
    }
    
    if (typeof loadConversations === 'function') {
        loadConversations();
    }
    
    if (typeof loadReminders === 'function') {
        loadReminders();
    }
    
    // Start a new conversation
    startNewChat();
});

// Chat functions
function startNewChat() {
    currentConversationId = null;
    
    document.getElementById("chatbox").innerHTML = `
        <div class="message bot">
            <strong>Assistant:</strong> Hello! I'm your advanced AI assistant. I can help with both reminders and general questions. Try saying:
            <ul>
                <li>"Remind me to call mom tomorrow"</li>
                <li>"What's the capital of France?"</li>
                <li>"Show me all my reminders"</li>
                <li>"Tell me a joke"</li>
            </ul>
        </div>
    `;
    
    document.getElementById("user-input").focus();
}

async function sendMessage() {
    const inputField = document.getElementById("user-input");
    const userMessage = inputField.value.trim();
    
    if (!userMessage) return;
    
    // Display user message
    addMessage("You", userMessage);
    // Clear input field
    inputField.value = "";
    
    // Show loading indicator
    const loadingId = addMessage("Assistant", "Thinking...");
    
    try {
        // Send message to backend
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: userMessage,
                conversation_id: currentConversationId
            })
        });
        
        if (!response.ok) {
            throw new Error("Network response was not ok");
        }
        
        const data = await response.json();
        
        // Update conversation ID if provided
        if (data.conversation_id) {
            currentConversationId = data.conversation_id;
            
            // Update UI to show we're in a conversation
            updateConversationUI();
        }
        
        // Remove "Thinking..." message and show AI response
        removeLastMessage();
        addMessage("Assistant", data.reply);
        
        // Check if the message was about reminders and reload reminders
        if (userMessage.toLowerCase().includes("remind") || 
            userMessage.toLowerCase().includes("reminder") ||
            data.reply.includes("Reminder added") ||
            data.reply.includes("reminder") ||
            data.reply.includes("✅")) {
            
            // Reload reminders and upcoming reminders
            if (typeof loadReminders === 'function') {
                loadReminders();
            }
            
            if (typeof loadUpcomingReminders === 'function') {
                loadUpcomingReminders();
            }
        }
    } catch (error) {
        console.error("Error:", error);
        removeLastMessage();
        addMessage("Assistant", "Oops! Something went wrong.");
    }
}

// Update UI to show we're in a conversation
function updateConversationUI() {
    // Add active conversation indicator if needed
    if (currentConversationId && document.querySelector('.conversation-indicator') === null) {
        const chatHeader = document.querySelector('.chat-header');
        if (chatHeader) {
            const indicator = document.createElement('div');
            indicator.className = 'conversation-indicator';
            indicator.innerHTML = `<span>Ongoing conversation</span>`;
            chatHeader.appendChild(indicator);
        }
    }
    
    // Update conversation list
    loadConversations();
}

function addMessage(sender, message) {
    let chatbox = document.getElementById("chatbox");
    let messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender.toLowerCase());
    messageDiv.innerHTML = `<strong>${sender}:</strong> ${message}`;
    chatbox.appendChild(messageDiv);

    // Auto-scroll to latest message
    chatbox.scrollTop = chatbox.scrollHeight;
    
    return messageDiv;
}

function removeLastMessage() {
    let chatbox = document.getElementById("chatbox");
    let lastMessage = chatbox.lastElementChild;
    if (lastMessage) {
        chatbox.removeChild(lastMessage);
    }
}

// Function to show all reminders
function showReminders() {
    sendMessage("show reminders");
}

// Add the missing functions

// Function to load all reminders
async function loadReminders() {
    try {
        // Get filter values if elements exist
        let dateFilter = "";
        let showCompleted = false;
        
        if (document.getElementById("date-filter")) {
            dateFilter = document.getElementById("date-filter").value;
        }
        
        if (document.getElementById("show-completed")) {
            showCompleted = document.getElementById("show-completed").checked;
        }
        
        // Build query parameters
        let queryParams = new URLSearchParams();
        if (dateFilter) {
            queryParams.append("date", dateFilter);
        }
        queryParams.append("completed", showCompleted);
        
        // Fetch reminders from the API
        const response = await fetch(`/api/reminders?${queryParams.toString()}`);
        
        if (!response.ok) {
            throw new Error("Failed to load reminders");
        }
        
        const data = await response.json();
        reminders = data.reminders || [];
        
        // Update the UI if the reminders list element exists
        const remindersList = document.getElementById("reminders-list");
        if (remindersList) {
            // Clear current list
            remindersList.innerHTML = "";
            
            if (reminders.length === 0) {
                remindersList.innerHTML = "<p class='no-reminders'>No reminders found</p>";
                return;
            }
            
            // Add each reminder to the list
            reminders.forEach(reminder => {
                const reminderElement = document.createElement("div");
                reminderElement.className = "reminder-item";
                
                // Set priority class
                reminderElement.classList.add(`priority-${reminder.priority}`);
                
                // Add completed class if needed
                if (reminder.completed) {
                    reminderElement.classList.add("completed");
                }
                
                // Create reminder content
                reminderElement.innerHTML = `
                    <div class="reminder-content">
                        <div class="reminder-header">
                            <span class="reminder-date">${reminder.date}</span>
                            <div class="reminder-actions">
                                <button class="complete-btn" onclick="completeReminder(${reminder.id})" ${reminder.completed ? 'disabled' : ''}>
                                    <i class="fas fa-check"></i>
                                </button>
                                <button class="delete-btn" onclick="deleteReminder(${reminder.id})">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                        <p class="reminder-message">${reminder.message}</p>
                    </div>
                `;
                
                remindersList.appendChild(reminderElement);
            });
        }
    } catch (error) {
        console.error("Error loading reminders:", error);
    }
}

// Function to load upcoming reminders
async function loadUpcomingReminders() {
    try {
        const upcomingList = document.getElementById("upcoming-list");
        if (!upcomingList) return;
        
        const response = await fetch("/api/reminders/upcoming");
        
        if (!response.ok) {
            throw new Error("Failed to load upcoming reminders");
        }
        
        const data = await response.json();
        const upcomingReminders = data.reminders || [];
        
        // Clear current list
        upcomingList.innerHTML = "";
        
        if (upcomingReminders.length === 0) {
            upcomingList.innerHTML = "<p class='no-reminders'>No upcoming reminders</p>";
            return;
        }
        
        // Add each reminder to the list
        upcomingReminders.forEach(reminder => {
            const reminderElement = document.createElement("div");
            reminderElement.className = "upcoming-item";
            
            // Set priority class
            reminderElement.classList.add(`priority-${reminder.priority}`);
            
            // Create reminder content
            reminderElement.innerHTML = `
                <span class="upcoming-date">${reminder.date}</span>
                <p class="upcoming-message">${reminder.message}</p>
            `;
            
            upcomingList.appendChild(reminderElement);
        });
    } catch (error) {
        console.error("Error loading upcoming reminders:", error);
    }
}

// Function to load conversation history
async function loadConversations() {
    try {
        const conversationList = document.getElementById("conversation-list");
        if (!conversationList) return;
        
        // If we have a conversation ID, try to fetch its details
        if (currentConversationId) {
            try {
                const response = await fetch(`/api/conversations/${currentConversationId}`);
                
                if (response.ok) {
                    const data = await response.json();
                    
                    // Clear existing conversations
                    conversationList.innerHTML = "";
                    
                    const conversationElement = document.createElement("div");
                    conversationElement.className = "conversation-item active";
                    conversationElement.innerHTML = `
                        <span>Conversation ${currentConversationId.substring(0, 8)}...</span>
                    `;
                    conversationList.appendChild(conversationElement);
                }
            } catch (error) {
                console.error("Error fetching conversation:", error);
            }
        }
    } catch (error) {
        console.error("Error loading conversations:", error);
    }
}

// Function to complete a reminder
async function completeReminder(id) {
    try {
        const response = await fetch(`/api/reminder/${id}/complete`, {
            method: "POST"
        });
        
        if (!response.ok) {
            throw new Error("Failed to complete reminder");
        }
        
        // Reload reminders to update the UI
        loadReminders();
    } catch (error) {
        console.error("Error completing reminder:", error);
    }
}

// Function to delete a reminder
async function deleteReminder(id) {
    try {
        const response = await fetch(`/api/reminder/${id}`, {
            method: "DELETE"
        });
        
        if (!response.ok) {
            throw new Error("Failed to delete reminder");
        }
        
        // Reload reminders to update the UI
        loadReminders();
    } catch (error) {
        console.error("Error deleting reminder:", error);
    }
}
