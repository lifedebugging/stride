const chatForm = document.querySelector<HTMLFormElement>(".chat-input-area");
const chatInput = document.querySelector<HTMLInputElement>(".chat-input");
const sendButton = document.querySelector<HTMLButtonElement>(".send-btn");
const chatMessages = document.querySelector<HTMLDivElement>(".chat-messages");

if (!chatForm || !chatInput || !sendButton || !chatMessages) {
    throw new Error("Chat form elements are missing from the page.");
}

const messageContainer = chatMessages;
let googleIdToken: string | null = null;
let threadId =
    sessionStorage.getItem("stride_thread_id") || crypto.randomUUID();
sessionStorage.setItem("stride_thread_id", threadId);

window.addEventListener("stride:authenticated", (event) => {
    const detail = (event as CustomEvent<{ credential?: unknown }>).detail;
    if (typeof detail?.credential !== "string" || !detail.credential) {
        throw new Error("Google sign-in did not provide an ID token.");
    }

    googleIdToken = detail.credential;
});

window.addEventListener("stride:new-chat", () => {
    threadId = crypto.randomUUID();
    sessionStorage.setItem("stride_thread_id", threadId);
});

function appendMessage(role: "user" | "assistant" | "error", text: string): void {
    const message = document.createElement("p");
    message.className = `chat-message ${role}-message`;
    message.textContent = text;
    messageContainer.appendChild(message);
}

async function sendToBackend(
    userMessage: string,
    currentThreadId: string,
    credential: string,
): Promise<string> {
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

    const query = chatInput.value.trim();
    if (!query) {
        return;
    }

    if (!googleIdToken) {
        appendMessage("error", "Sign in with Google before sending a message.");
        return;
    }

    appendMessage("user", query);
    chatInput.value = "";
    sendButton.disabled = true;
    const currentThreadId = threadId;
    const credential = googleIdToken;

    try {
        const reply = await sendToBackend(query, currentThreadId, credential);
        if (threadId === currentThreadId) {
            appendMessage("assistant", reply);
        }
    } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        console.error("Chat request failed:", error);
        if (threadId === currentThreadId) {
            appendMessage("error", `Chat request failed: ${message}`);
        }
    } finally {
        sendButton.disabled = false;
        chatInput.focus();
    }
});