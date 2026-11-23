"use strict";
const chatForm = document.querySelector(".chat-input-area");
const chatInput = document.querySelector(".chat-input");
const sendButton = document.querySelector(".send-btn");
const chatMessages = document.querySelector(".chat-messages");
const chatHistoryList = document.querySelector(".chat-history-list");
if (!chatForm || !chatInput || !sendButton || !chatMessages || !chatHistoryList) {
    throw new Error("Chat form elements are missing from the page.");
}
const historyList = chatHistoryList;
const input = chatInput;
const messageContainer = chatMessages;
function resizeChatInput() {
    input.style.height = "auto";
    const maxHeight = Number.parseFloat(getComputedStyle(input).maxHeight);
    input.style.height = `${Math.min(input.scrollHeight, maxHeight)}px`;
    input.style.overflowY =
        input.scrollHeight > maxHeight ? "auto" : "hidden";
}
input.addEventListener("input", resizeChatInput);
let googleIdToken = null;
let threadId = crypto.randomUUID();
window.addEventListener("pageshow", () => {
    messageContainer.replaceChildren();
    input.value = "";
    threadId = crypto.randomUUID();
});
window.addEventListener("stride:authenticated", (event) => {
    const detail = event.detail;
    if (typeof detail?.credential !== "string" || !detail.credential) {
        throw new Error("Google sign-in did not provide an ID token.");
    }
    googleIdToken = detail.credential;
    void refreshChatHistory().catch((error) => {
        const message = error instanceof Error ? error.message : String(error);
        console.error("Unable to load chat history:", error);
    });
});
window.addEventListener("stride:new-chat", () => {
    threadId = crypto.randomUUID();
});
window.addEventListener("stride:load-chat", (event) => {
    const detail = event.detail;
    if (typeof detail?.chatId !== "string" || !googleIdToken) {
        appendMessage("error", "Sign in before opening a saved chat.");
        return;
    }
    void loadChat(detail.chatId, googleIdToken).catch((error) => {
        const message = error instanceof Error ? error.message : String(error);
        console.error("Unable to open chat:", error);
        appendMessage("error", `Unable to open chat: ${message}`);
    });
});
function appendMessage(role, text) {
    const message = document.createElement("p");
    message.className = `chat-message ${role}-message`;
    message.textContent = text;
    messageContainer.appendChild(message);
    if (role !== "error")
        document.querySelector(".main-workspace")?.classList.add("active-chat");
}
function isChatSummary(value) {
    if (typeof value !== "object" || value === null) {
        return false;
    }
    const chat = value;
    return typeof chat.chat_id === "string" && typeof chat.title === "string";
}
function isChatDetails(value) {
    if (!isChatSummary(value)) {
        return false;
    }
    return ("messages" in value &&
        Array.isArray(value.messages) &&
        value.messages.every(isChatMessage));
}
function isChatMessage(value) {
    if (typeof value !== "object" || value === null) {
        return false;
    }
    return ("role" in value &&
        (value.role === "user" || value.role === "assistant") &&
        "content" in value &&
        typeof value.content === "string");
}
async function refreshChatHistory() {
    if (!googleIdToken) {
        return;
    }
    const response = await fetch("http://127.0.0.1:8002/chats", {
        headers: { Authorization: `Bearer ${googleIdToken}` },
    });
    if (!response.ok) {
        throw new Error(`History request returned ${response.status}.`);
    }
    const data = await response.json();
    if (!Array.isArray(data) || !data.every(isChatSummary)) {
        throw new Error("The chat history response was invalid.");
    }
    historyList.replaceChildren();
    for (const chat of data) {
        const item = document.createElement("li");
        const button = document.createElement("button");
        button.type = "button";
        button.className = "history-item";
        button.dataset.chatId = chat.chat_id;
        button.textContent = chat.title;
        item.appendChild(button);
        historyList.appendChild(item);
    }
}
async function loadChat(chatId, credential) {
    const response = await fetch(`http://127.0.0.1:8002/chats/${encodeURIComponent(chatId)}`, { headers: { Authorization: `Bearer ${credential}` } });
    if (!response.ok) {
        throw new Error(`Chat request returned ${response.status}.`);
    }
    const data = await response.json();
    if (!isChatDetails(data)) {
        throw new Error("The saved chat response was invalid.");
    }
    threadId = data.chat_id;
    messageContainer.replaceChildren();
    for (const message of data.messages) {
        appendMessage(message.role, message.content);
    }
}
async function sendToBackend(userMessage, currentThreadId, credential) {
    const response = await fetch("http://127.0.0.1:8002/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${credential}`,
        },
        body: JSON.stringify({ query: userMessage, thread_id: currentThreadId }),
    });
    if (response.status === 401) {
        googleIdToken = null;
        window.dispatchEvent(new Event("stride:authentication-required"));
    }
    if (!response.ok) {
        const detail = await response.text();
        throw new Error(`Proxy returned ${response.status}: ${detail}`);
    }
    return response.text();
}
chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const query = input.value.trim();
    if (!query) {
        return;
    }
    if (!googleIdToken) {
        window.dispatchEvent(new Event("stride:authentication-required"));
        return;
    }
    appendMessage("user", query);
    input.value = "";
    sendButton.disabled = true;
    const currentThreadId = threadId;
    const credential = googleIdToken;
    try {
        const reply = await sendToBackend(query, currentThreadId, credential);
        if (threadId === currentThreadId) {
            appendMessage("assistant", reply);
            void refreshChatHistory().catch((error) => {
                const message = error instanceof Error ? error.message : String(error);
                console.error("Unable to refresh chat history:", error);
                appendMessage("error", `Unable to refresh chat history: ${message}`);
            });
        }
    }
    catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        console.error("Chat request failed:", error);
        if (threadId === currentThreadId) {
            appendMessage("error", "Chat request failed. Please try again later");
        }
    }
    finally {
        sendButton.disabled = false;
        input.focus();
    }
});
