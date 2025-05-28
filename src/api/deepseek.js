export async function sendToDeepSeek(message) {
  const response = await fetch("http://localhost:11434/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
  model: "deepseek-coder",
  messages: [
    {
      role: "system",
      content: "You are an intelligent travel assistant. You can help with travel planning, trip suggestions, currency conversion, weather, and general questions. Respond clearly and helpfully."
    },
    { role: "user", content: message }
  ],
  stream: false
})

  });

  const data = await response.json();
  return data.message.content;
}
