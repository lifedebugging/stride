
interface ChatRequest {
    query: string;
    thread_id: string;
}

interface ChatResponse {
    reply: string;
}


const threadId = sessionStorage.getItem('stride_thread_id') || crypto.randomUUID();
sessionStorage.setItem('stride_thread_id', threadId);

/**
 * Sends a user message to the backend chat service and logs the response.
 * @param userMessage - The message from the user to send to the backend.
 */

export async function sendToBackend(userMessage : string): Promise<void> {

    const payload: ChatRequest = 
    {query: userMessage,
        thread_id: threadId
    }
    const response = await
        fetch("http://127.0.0.1:8001/route",
            {
                method : 'POST',
                headers: { 'Content-Type': 'application/json'},
                body: JSON.stringify(payload),
            });

    if (!response.ok){
        throw new Error(`Server error: ${response.status}`);
    }

    const data: ChatResponse = await response.json();
    console.log(data.reply);

}