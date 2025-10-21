import React, { useState } from "react";
import { sendChatMessage } from "../services/chat";
import { MessageSquare, Send } from "lucide-react";

function ChatInterface({ user, onActionComplete }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: `Hello ${user.display_name}! I'm your AI assistant. I can help you manage visitors. Try saying:\n- "approve Ramesh"\n- "show me all pending visitors"\n- "check in Suresh"\n- "deny John Doe"`,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await sendChatMessage(input);
      const assistantMessage = {
        role: "assistant",
        content: response.response,
        action: response.action_taken,
        details: response.details,
      };
      setMessages((prev) => [...prev, assistantMessage]);

      if (response.action_taken) {
        onActionComplete();
      }
    } catch (err) {
      const errorMessage = {
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <MessageSquare />
            AI Copilot
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Ask me to manage visitors, approve/deny requests, or check in/out
            visitors
          </p>
        </div>

        <div className="h-96 overflow-y-auto p-4 space-y-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-2xl px-4 py-3 rounded-lg ${
                  message.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-900"
                }`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
                {message.action && (
                  <div className="mt-2 pt-2 border-t border-gray-300">
                    <p className="text-sm opacity-75">
                      Action: {message.action}
                    </p>
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 px-4 py-3 rounded-lg">
                <p className="text-gray-600">Thinking...</p>
              </div>
            </div>
          )}
        </div>

        <div className="p-4 border-t border-gray-200">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 flex items-center gap-2"
            >
              <Send size={18} />
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatInterface;
