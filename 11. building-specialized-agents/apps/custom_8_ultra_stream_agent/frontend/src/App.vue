<template>
  <div class="app-container">
    <!-- Header -->
    <header class="app-header">
      <h1>🔍 Ultra Stream Agent</h1>
      <div class="status-indicators">
        <span class="status-badge" :class="{ active: streamActive }">
          Stream: {{ streamActive ? "Active" : "Inactive" }}
        </span>
        <span class="status-badge" :class="{ active: inspectorActive }">
          Inspector: {{ inspectorActive ? "Active" : "Inactive" }}
        </span>
        <span class="status-badge info"> Logs: {{ totalLogs }} </span>
        <span class="status-badge info"> Index: {{ currentIndex }} </span>
      </div>
    </header>

    <!-- Main Content - Split View -->
    <main class="main-content">
      <!-- Left Panel - Inspector Agent -->
      <section class="panel inspector-panel">
        <div class="panel-header">
          <div>
            <h2>🔎 Inspector Agent</h2>
            <span class="panel-subtitle"
              >Ask questions about the log stream</span
            >
          </div>
          <div class="toggle-controls">
            <label class="toggle-item">
              <input
                type="checkbox"
                v-model="showThinking"
                class="toggle-checkbox"
              />
              <span class="toggle-label">💭 Thinking</span>
            </label>
            <label class="toggle-item">
              <input
                type="checkbox"
                v-model="showToolUse"
                class="toggle-checkbox"
              />
              <span class="toggle-label">🔧 Tools</span>
            </label>
          </div>
        </div>

        <div class="chat-container">
          <!-- Chat Messages -->
          <div class="messages-area" ref="inspectorMessagesContainer">
            <div
              v-for="msg in filteredInspectorMessages"
              :key="msg.id"
              :class="['message', `message-${msg.message_type}`]"
            >
              <!-- User Message -->
              <div v-if="msg.message_type === 'user'" class="message-content">
                <span class="message-icon">👤</span>
                <div class="message-text">{{ msg.message }}</div>
              </div>

              <!-- Assistant Message -->
              <div
                v-else-if="msg.message_type === 'assistant'"
                class="message-content"
              >
                <span class="message-icon">🤖</span>
                <div
                  class="message-text markdown-content"
                  v-html="renderMarkdown(msg.message)"
                ></div>
              </div>

              <!-- Alert Message -->
              <div
                v-else-if="msg.message_type === 'alert'"
                class="message-content alert-content"
              >
                <span class="message-icon">🚨</span>
                <div class="message-text">
                  <strong>ALERT:</strong> {{ msg.message }}
                  <div v-if="msg.produced_log" class="alert-details">
                    <small
                      >Indices: {{ msg.produced_log.start_index }} -
                      {{ msg.produced_log.end_index }}</small
                    >
                    <small v-if="msg.produced_log.user_id"
                      >User: {{ msg.produced_log.user_id }}</small
                    >
                  </div>
                </div>
              </div>

              <!-- System Message -->
              <div
                v-else-if="msg.message_type === 'system'"
                class="message-content system-content"
              >
                <span class="message-icon">ℹ️</span>
                <div class="message-text">{{ msg.message }}</div>
              </div>

              <!-- Thinking Message -->
              <div
                v-else-if="msg.message_type === 'thinking'"
                class="message-content thinking-content"
              >
                <span class="message-icon">💭</span>
                <div class="message-text">{{ msg.message }}</div>
              </div>

              <!-- Tool Use Message -->
              <div
                v-else-if="msg.message_type === 'tool_use'"
                class="message-content tool-use-content"
              >
                <span class="message-icon">🔧</span>
                <div class="message-text">{{ msg.message }}</div>
              </div>

              <div class="message-timestamp">
                {{ formatTime(msg.timestamp) }}
              </div>
            </div>

            <!-- Loading indicator -->
            <div v-if="inspectorLoading" class="loading-indicator">
              <div class="thinking-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span class="thinking-text">Inspector Agent is thinking...</span>
            </div>
          </div>

          <!-- Chat Input -->
          <div class="chat-input-container">
            <input
              v-model="inspectorQuery"
              @keyup.enter="sendInspectorQuery"
              type="text"
              placeholder="Ask about logs (e.g., 'Show errors for user123' or 'What happened in the last hour?')"
              class="chat-input"
              :disabled="!inspectorActive"
            />
            <button
              @click="sendInspectorQuery"
              class="send-button"
              :disabled="!inspectorActive || !inspectorQuery.trim()"
            >
              Send
            </button>
          </div>
        </div>
      </section>

      <!-- Right Panel - Stream Agent -->
      <section class="panel stream-panel">
        <div class="panel-header">
          <div>
            <h2>📊 Stream Agent</h2>
            <span class="panel-subtitle">Live processed log stream</span>
          </div>
        </div>

        <div class="stream-container">
          <!-- Stream Messages -->
          <div class="stream-area" ref="streamMessagesContainer">
            <!-- Context Clear Messages -->
            <div
              v-for="status in systemStatuses"
              :key="status.id"
              class="stream-item system-status"
            >
              <span class="status-icon">🔄</span>
              <span class="status-text">{{ status.message }}</span>
              <span class="item-timestamp">{{
                formatTime(status.timestamp)
              }}</span>
            </div>

            <!-- Processed Logs -->
            <div
              v-for="log in streamLogs"
              :key="log.id"
              :class="['stream-item', `severity-${log.log_severity}`]"
            >
              <div class="log-header">
                <span class="log-index">#{{ log.log_index }}</span>
                <span
                  :class="['severity-badge', `severity-${log.log_severity}`]"
                >
                  {{ log.log_severity.toUpperCase() }}
                </span>
                <span v-if="log.user_id" class="user-badge">
                  User: {{ log.user_id }}
                </span>
              </div>

              <div class="log-summary">
                {{ log.log_summary }}
              </div>

              <div class="log-footer">
                <span class="log-id">{{ log.log_id }}</span>
                <span class="item-timestamp">{{
                  formatTime(log.timestamp)
                }}</span>
              </div>
            </div>
          </div>

          <!-- Stream Stats -->
          <div class="stream-stats">
            <div class="stat-item">
              <span class="stat-label">High:</span>
              <span class="stat-value high">{{ severityCounts.high }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Medium:</span>
              <span class="stat-value medium">{{ severityCounts.medium }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Low:</span>
              <span class="stat-value low">{{ severityCounts.low }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Total:</span>
              <span class="stat-value">{{ streamLogs.length }}</span>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, nextTick } from "vue";
import axios from "axios";
import MarkdownIt from "markdown-it";

// Configure axios to use the backend URL
axios.defaults.baseURL = "http://127.0.0.1:8002";

// Initialize markdown renderer
const md = new MarkdownIt({
  breaks: true, // Convert \n to <br>
  linkify: true, // Auto-convert URLs to links
  typographer: true, // Enable smart quotes
});

export default {
  name: "UltraStreamAgent",
  setup() {
    // State
    const streamActive = ref(false);
    const inspectorActive = ref(false);
    const totalLogs = ref(0);
    const currentIndex = ref(0);
    const inspectorMessages = ref([]);
    const streamLogs = ref([]);
    const systemStatuses = ref([]);
    const inspectorQuery = ref("");
    const ws = ref(null);
    const inspectorLoading = ref(false);
    const showThinking = ref(true);
    const showToolUse = ref(true);

    // Refs for scroll containers
    const inspectorMessagesContainer = ref(null);
    const streamMessagesContainer = ref(null);

    // Computed
    const severityCounts = computed(() => {
      const counts = { high: 0, medium: 0, low: 0 };
      streamLogs.value.forEach((log) => {
        counts[log.log_severity]++;
      });
      return counts;
    });

    const filteredInspectorMessages = computed(() => {
      return inspectorMessages.value.filter((msg) => {
        if (msg.message_type === "thinking" && !showThinking.value) {
          return false;
        }
        if (msg.message_type === "tool_use" && !showToolUse.value) {
          return false;
        }
        return true;
      });
    });

    // Methods
    const formatTime = (timestamp) => {
      const date = new Date(timestamp);
      return date.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
    };

    const renderMarkdown = (text) => {
      if (!text) return "";
      return md.render(text);
    };

    const scrollToBottom = (container) => {
      if (container) {
        nextTick(() => {
          container.scrollTop = container.scrollHeight;
        });
      }
    };

    const sendInspectorQuery = async () => {
      if (!inspectorQuery.value.trim() || !inspectorActive.value) return;

      const query = inspectorQuery.value.trim();
      inspectorQuery.value = "";

      // Ensure inspectorMessages is an array
      if (!Array.isArray(inspectorMessages.value)) {
        inspectorMessages.value = [];
      }

      // Add user message
      inspectorMessages.value.push({
        id: Date.now(),
        message: query,
        message_type: "user",
        timestamp: new Date().toISOString(),
      });

      scrollToBottom(inspectorMessagesContainer.value);

      // Start loading
      inspectorLoading.value = true;

      try {
        const response = await axios.post("/inspector/query", {
          query,
          context_window: 50,
        });

        // Ensure array before adding assistant response
        if (!Array.isArray(inspectorMessages.value)) {
          inspectorMessages.value = [];
        }

        // Add assistant response
        inspectorMessages.value.push({
          id: Date.now() + 1,
          message: response.data.response,
          message_type: "assistant",
          timestamp: new Date().toISOString(),
        });

        scrollToBottom(inspectorMessagesContainer.value);
      } catch (error) {
        console.error("Error sending query:", error);
        inspectorMessages.value.push({
          id: Date.now() + 1,
          message: "Error: Failed to process query. Please try again.",
          message_type: "system",
          timestamp: new Date().toISOString(),
        });
      } finally {
        // Stop loading
        inspectorLoading.value = false;
      }
    };

    const loadInitialData = async () => {
      try {
        // Load status
        const statusResponse = await axios.get("/status");
        streamActive.value = statusResponse.data.stream_agent_active;
        inspectorActive.value = statusResponse.data.inspector_agent_active;
        totalLogs.value = statusResponse.data.total_logs_processed;
        currentIndex.value = statusResponse.data.current_line_index;

        // Load recent logs
        const logsResponse = await axios.get("/logs/recent?limit=50");
        streamLogs.value = logsResponse.data.reverse(); // Show oldest first

        // Load recent messages
        const messagesResponse = await axios.get("/messages/recent?limit=20");
        inspectorMessages.value = messagesResponse.data
          ? messagesResponse.data.reverse()
          : []; // Show oldest first
      } catch (error) {
        console.error("Error loading initial data:", error);
      }
    };

    const connectWebSocket = () => {
      const wsUrl = `ws://127.0.0.1:8002/ws`;
      ws.value = new WebSocket(wsUrl);

      ws.value.onopen = () => {
        console.log("WebSocket connected");
      };

      ws.value.onmessage = (event) => {
        const message = JSON.parse(event.data);

        switch (message.type) {
          case "stream_update":
            // Add new log to stream
            streamLogs.value.push(message.data);
            totalLogs.value++;
            currentIndex.value = Math.max(
              currentIndex.value,
              message.data.log_index + 1
            );

            // Keep only last 100 logs
            if (streamLogs.value.length > 100) {
              streamLogs.value.shift();
            }

            scrollToBottom(streamMessagesContainer.value);
            break;

          case "inspector_chat":
            // Add message to inspector chat
            inspectorMessages.value.push(message.data);
            scrollToBottom(inspectorMessagesContainer.value);
            break;

          case "inspector_thinking":
            // Add thinking message to inspector chat
            inspectorMessages.value.push({
              ...message.data,
              message_type: "thinking",
            });
            scrollToBottom(inspectorMessagesContainer.value);
            break;

          case "inspector_tool_use":
            // Add tool use message to inspector chat
            inspectorMessages.value.push({
              ...message.data,
              message_type: "tool_use",
            });
            scrollToBottom(inspectorMessagesContainer.value);
            break;

          case "alert":
            // Add alert to inspector chat
            inspectorMessages.value.push({
              id: Date.now(),
              message: message.data.message,
              message_type: "alert",
              produced_log: message.data,
              timestamp: message.data.timestamp,
            });
            scrollToBottom(inspectorMessagesContainer.value);
            break;

          case "system_status":
            // Add system status to stream
            systemStatuses.value.push({
              id: Date.now(),
              ...message.data,
            });

            // Keep only last 10 statuses
            if (systemStatuses.value.length > 10) {
              systemStatuses.value.shift();
            }
            break;

          case "connected":
            console.log("Connected:", message.data.message);
            break;
        }
      };

      ws.value.onerror = (error) => {
        console.error("WebSocket error:", error);
      };

      ws.value.onclose = () => {
        console.log("WebSocket disconnected. Reconnecting in 3 seconds...");
        setTimeout(connectWebSocket, 3000);
      };
    };

    // Lifecycle
    onMounted(() => {
      // Refs are automatically bound by Vue, no need for querySelector

      loadInitialData();
      connectWebSocket();
    });

    onUnmounted(() => {
      if (ws.value) {
        ws.value.close();
      }
    });

    return {
      streamActive,
      inspectorActive,
      totalLogs,
      currentIndex,
      inspectorMessages,
      streamLogs,
      systemStatuses,
      inspectorQuery,
      inspectorLoading,
      severityCounts,
      formatTime,
      renderMarkdown,
      sendInspectorQuery,
      inspectorMessagesContainer,
      streamMessagesContainer,
      showThinking,
      showToolUse,
      filteredInspectorMessages,
    };
  },
};
</script>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
}

/* Header */
.app-header {
  background: #1a1a1a;
  border-bottom: 1px solid #333;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.app-header h1 {
  font-size: 1.5rem;
  color: #fff;
  margin: 0;
}

.status-indicators {
  display: flex;
  gap: 1rem;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  background: #2a2a2a;
  color: #666;
  font-size: 0.875rem;
  transition: all 0.3s ease;
}

.status-badge.active {
  background: #10b981;
  color: white;
}

.status-badge.info {
  background: #3b82f6;
  color: white;
}

/* Main Content */
.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* Panels */
.panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.inspector-panel {
  border-right: 1px solid #333;
}

.panel-header {
  background: #1a1a1a;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #333;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.panel-header h2 {
  font-size: 1.25rem;
  color: #fff;
  margin: 0;
}

.panel-subtitle {
  font-size: 0.875rem;
  color: #888;
  display: block;
  margin-top: 0.25rem;
}

.toggle-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.toggle-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
}

.toggle-checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #3b82f6;
}

.toggle-label {
  font-size: 0.875rem;
  color: #a0a0a0;
  transition: color 0.2s ease;
}

.toggle-item:hover .toggle-label {
  color: #e0e0e0;
}

/* Inspector Panel - Chat */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 1rem;
  scroll-behavior: smooth;
  max-width: 100%;
}

.message {
  margin-bottom: 1rem;
  animation: slideIn 0.3s ease;
  max-width: 100%;
  overflow: hidden;
}

.message-content {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
}

.message-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.message-text {
  flex: 1;
  padding: 0.75rem;
  border-radius: 8px;
  background: #2a2a2a;
  color: #e0e0e0;
  line-height: 1.5;
  word-wrap: break-word;
  word-break: break-word;
  overflow-wrap: anywhere;
  max-width: calc(100% - 3rem);
  overflow-x: auto;
}

.message-user .message-text {
  background: #3b82f6;
  color: white;
}

.message-assistant .message-text {
  background: #2a2a2a;
  border: 1px solid #444;
}

.message-alert .message-text {
  background: #dc2626;
  color: white;
}

.message-system .message-text {
  background: #1e40af;
  color: white;
  font-size: 0.875rem;
}

.message-thinking .message-text {
  background: rgba(139, 92, 246, 0.15);
  color: #a78bfa;
  font-size: 0.875rem;
  font-style: italic;
  border: 1px solid rgba(139, 92, 246, 0.3);
}

.message-tool_use .message-text {
  background: rgba(34, 197, 94, 0.15);
  color: #86efac;
  font-size: 0.875rem;
  font-weight: 500;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

/* Markdown Content Styles */
.markdown-content {
  line-height: 1.8;
  overflow-x: auto;
  max-width: 100%;
  word-break: break-word;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4 {
  color: #fff;
  margin-top: 1.75rem;
  margin-bottom: 1rem;
  font-weight: 600;
  line-height: 1.3;
}

.markdown-content h1 {
  font-size: 2rem;
}
.markdown-content h2 {
  font-size: 1.75rem;
}
.markdown-content h3 {
  font-size: 1.5rem;
}
.markdown-content h4 {
  font-size: 1.25rem;
}

.markdown-content p {
  margin: 1rem 0;
}

.markdown-content ul,
.markdown-content ol {
  max-width: 100%;
  list-style-position: outside;
}

.markdown-content li {
  word-wrap: break-word;
  word-break: break-word;
  overflow-wrap: anywhere;
  line-height: 1.6;
  display: list-item;
  list-style: inherit;
}

.markdown-content code {
  background: rgba(59, 130, 246, 0.25);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: "Consolas", "Monaco", monospace;
  font-size: 0.9rem;
  color: #93c5fd;
  border: 1px solid rgba(59, 130, 246, 0.4);
  font-weight: 500;
  box-shadow: 0 1px 3px rgba(59, 130, 246, 0.1);
}

.markdown-content pre {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  padding: 1.25rem;
  border-radius: 8px;
  overflow-x: auto;
  margin: 1.5rem 0;
  max-width: 100%;
  border: 1px solid rgba(59, 130, 246, 0.2);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}

.markdown-content pre code {
  background: none;
  padding: 0;
  color: #e0e0e0;
  border: none;
  box-shadow: none;
  font-size: 0.875rem;
}

.markdown-content strong {
  color: #fff;
  font-weight: 600;
}

.markdown-content em {
  color: #a0a0a0;
}

.markdown-content blockquote {
  border-left: 3px solid #3b82f6;
  padding-left: 1rem;
  margin: 1rem 0;
  color: #a0a0a0;
}

.markdown-content a {
  color: #3b82f6;
  text-decoration: none;
}

.markdown-content a:hover {
  text-decoration: underline;
}

.markdown-content hr {
  border: none;
  border-top: 1px solid #444;
  margin: 1.5rem 0;
}

.alert-details {
  margin-top: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.alert-details small {
  opacity: 0.9;
}

.message-timestamp {
  font-size: 0.75rem;
  color: #666;
  margin-top: 0.25rem;
  margin-left: 2.5rem;
}

.chat-input-container {
  display: flex;
  padding: 1rem;
  background: #1a1a1a;
  border-top: 1px solid #333;
  gap: 0.5rem;
}

.chat-input {
  flex: 1;
  padding: 0.75rem;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 8px;
  color: #e0e0e0;
  font-size: 1.225rem;
  transition: all 0.3s ease;
}

.chat-input:focus {
  outline: none;
  border-color: #3b82f6;
  background: #333;
}

.chat-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-button {
  padding: 0.75rem 1.5rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.send-button:hover:not(:disabled) {
  background: #2563eb;
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Stream Panel */
.stream-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.stream-area {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  scroll-behavior: smooth;
}

.stream-item {
  margin-bottom: 0.75rem;
  padding: 0.75rem;
  background: #2a2a2a;
  border-radius: 8px;
  border-left: 3px solid #444;
  animation: slideIn 0.3s ease;
}

.stream-item.severity-low {
  border-left-color: #10b981;
}

.stream-item.severity-medium {
  border-left-color: #f59e0b;
}

.stream-item.severity-high {
  border-left-color: #ef4444;
}

.system-status {
  background: #1e40af;
  color: white;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border-left-color: #3b82f6;
}

.status-icon {
  font-size: 1.25rem;
}

.status-text {
  flex: 1;
}

.log-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.log-index {
  font-size: 0.875rem;
  color: #888;
  font-weight: 600;
}

.severity-badge {
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.severity-badge.severity-low {
  background: #10b981;
  color: white;
}

.severity-badge.severity-medium {
  background: #f59e0b;
  color: white;
}

.severity-badge.severity-high {
  background: #ef4444;
  color: white;
}

.user-badge {
  padding: 0.125rem 0.5rem;
  background: #6366f1;
  color: white;
  border-radius: 4px;
  font-size: 0.75rem;
}

.log-summary {
  color: #e0e0e0;
  line-height: 1.5;
  margin-bottom: 0.5rem;
}

.log-footer {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #666;
}

.log-id {
  font-family: monospace;
}

.item-timestamp {
  font-size: 0.75rem;
  color: #666;
}

/* Stream Stats */
.stream-stats {
  display: flex;
  padding: 1rem;
  background: #1a1a1a;
  border-top: 1px solid #333;
  gap: 2rem;
  justify-content: center;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.stat-label {
  color: #888;
  font-size: 0.875rem;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: #e0e0e0;
}

.stat-value.high {
  color: #ef4444;
}

.stat-value.medium {
  color: #f59e0b;
}

.stat-value.low {
  color: #10b981;
}

/* Animations */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Loading Animation */
.loading-indicator {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  margin: 0.5rem 0;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 8px;
  animation: slideIn 0.3s ease;
}

.thinking-dots {
  display: flex;
  gap: 0.25rem;
}

.thinking-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #3b82f6;
  animation: thinking 1.4s ease-in-out infinite;
}

.thinking-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.thinking-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes thinking {
  0%,
  60%,
  100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

.thinking-text {
  color: #60a5fa;
  font-size: 0.875rem;
  font-weight: 500;
}

/* Scrollbar Styles */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #1a1a1a;
}

::-webkit-scrollbar-thumb {
  background: #444;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* Responsive */
@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
  }

  .inspector-panel {
    border-right: none;
    border-bottom: 1px solid #333;
  }

  .stream-stats {
    gap: 1rem;
  }
}
</style>

<style>
ol,
li {
  margin-left: 16px !important;
}
</style>
