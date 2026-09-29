<template>
  <div class="app"
    @dragenter.prevent="onDragEnter"
    @dragover.prevent="onDragOver"
    @dragleave.prevent="onDragLeave"
    @drop.prevent="onDrop">
    <div class="container">
      <!-- Header -->
      <header class="header">
        <div class="header-content">
          <h1 class="title">
            <span class="icon">✍️</span>
            Tri-Copy-Writer
          </h1>
          <p class="subtitle">Multiple copy variations for every project</p>
        </div>
      </header>

      <!-- Main Interface -->
      <main class="main">
        <div class="copy-container">
          <!-- Messages Display -->
          <div class="messages" ref="messagesContainer">
            <div v-if="messages.length === 0" class="welcome-message">
              <ul class="welcome-list">
                <li>📧 <strong>Email Subject Lines</strong> - Boost open rates</li>
                <li>🎯 <strong>Headlines</strong> - Grab attention instantly</li>
                <li>📱 <strong>Social Media</strong> - Engage your audience</li>
                <li>🛍️ <strong>Product Copy</strong> - Drive conversions</li>
              </ul>
            </div>

            <div v-for="(message, index) in messages" :key="index" class="message-group">
              <!-- User Message -->
              <div class="message user-message">
                <div class="message-content">
                  <span class="user-icon">👤</span>
                  <strong>You:</strong> {{ message.userText }}
                </div>
              </div>

              <!-- AI Response -->
              <div v-if="message.copyResponse" class="copy-responses">
                <!-- Primary Response -->
                <div class="primary-response">
                  <div class="response-header">
                    <span class="response-icon">💡</span>
                    <span class="response-label">Primary Response</span>
                  </div>
                  <div class="response-content">{{ message.copyResponse.primary_response }}</div>
                </div>

                <!-- Copy Variations -->
                <div class="copy-variations">
                  <h4>Copy Variations</h4>
                  <div class="variations-grid">
                    <div
                      v-for="(variation, variationIndex) in message.copyResponse.multi_version_copy_responses"
                      :key="variationIndex"
                      class="copy-variation"
                      :class="getVariationClass(variationIndex)"
                    >
                      <div class="variation-header">
                        <span class="variation-icon">{{ getVariationIcon(variationIndex) }}</span>
                        <span class="variation-label">Version {{ variationIndex + 1 }}</span>
                        <button @click="copyToClipboard(variation)" class="copy-btn">📋</button>
                      </div>
                      <div class="variation-content">{{ variation }}</div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Loading State -->
              <div v-if="message.loading" class="loading-responses">
                <div class="loading-primary">
                  <div class="loading-header">
                    <span class="response-icon">💡</span>
                    <span class="response-label">Generating...</span>
                  </div>
                  <div class="loading-content">
                    <div class="loading-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
                <div class="loading-variations">
                  <h4>Copy Variations</h4>
                  <div class="variations-grid">
                    <div v-for="i in versionsConfigured" :key="i" class="loading-variation">
                      <div class="loading-header">
                        <span class="variation-icon">✨</span>
                        <span class="variation-label">Version {{ i }}</span>
                      </div>
                      <div class="loading-content">
                        <div class="loading-dots">
                          <span></span>
                          <span></span>
                          <span></span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Session Info -->
              <div v-if="message.sessionInfo" class="session-info">
                <small>
                  Session: {{ message.sessionInfo.session_id.slice(0, 8) }}... |
                  {{ message.sessionInfo.duration_ms }}ms |
                  {{ message.sessionInfo.versions_generated }} variations |
                  <span v-if="message.sessionInfo.cost_usd">
                    ${{ message.sessionInfo.cost_usd.toFixed(6) }}
                  </span>
                  <span v-else>No cost data</span>
                </small>
              </div>
            </div>
          </div>

          <!-- Context Files Pills -->
          <div v-if="contextFiles.length > 0" class="context-files">
            <div class="context-file-list">
              <div
                v-for="(file, index) in contextFiles"
                :key="index"
                class="context-file"
              >
                <span class="file-icon">📎</span>
                <span class="file-name">{{ file.name }}</span>
                <button @click="removeFile(index)" class="remove-btn">×</button>
              </div>
            </div>
          </div>

          <!-- Input Area -->
          <div class="input-area">
            <div class="input-container">
              <textarea
                v-model="currentMessage"
                @keydown.enter.prevent="handleEnter"
                placeholder="Describe the copy you need... (e.g., 'Write email subject lines for a product launch')"
                class="message-input"
                :disabled="isLoading"
                rows="3"
                ref="messageInput"
              ></textarea>
              <button
                @click="sendMessage"
                class="send-button"
                :disabled="isLoading || !currentMessage.trim()"
              >
                <span v-if="isLoading">⏳</span>
                <span v-else>✨ Generate Copy</span>
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>

    <!-- Minimal Drag Overlay -->
    <div v-if="isDragOver" class="drag-overlay">
      <div class="drag-indicator">Drop files for context</div>
    </div>

    <!-- Toast Notifications -->
    <div v-if="toast.show" class="toast" :class="toast.type">
      {{ toast.message }}
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'App',
  data() {
    return {
      messages: [],
      currentMessage: '',
      isLoading: false,
      apiBaseUrl: 'http://127.0.0.1:8000',
      contextFiles: [],
      isDragOver: false,
      sessionId: null, // Track session ID for conversation continuity
      versionsConfigured: 3, // Default to 3, will be updated from backend
      toast: {
        show: false,
        message: '',
        type: 'success'
      }
    }
  },
  methods: {
    handleEnter(event) {
      if (!event.shiftKey) {
        this.sendMessage()
      }
    },

    async sendMessage() {
      if (!this.currentMessage.trim() || this.isLoading) {
        return
      }

      const userText = this.currentMessage.trim()
      this.currentMessage = ''

      // Add user message with loading state
      const messageIndex = this.messages.length
      this.messages.push({
        userText,
        loading: true,
        copyResponse: null,
        sessionInfo: null
      })

      this.isLoading = true

      try {
        // Scroll to bottom
        this.$nextTick(() => {
          this.scrollToBottom()
        })

        // Prepare request data
        const requestData = {
          message: userText
        }

        // Add session_id for conversation continuity if it exists
        if (this.sessionId) {
          requestData.session_id = this.sessionId
        }

        // Add context files if any
        if (this.contextFiles.length > 0) {
          requestData.context_files = this.contextFiles.map(file => ({
            name: file.name,
            content: file.content
          }))
        }

        // Call the backend API
        const response = await axios.post(`${this.apiBaseUrl}/copy`, requestData)

        // Store session_id for future requests (conversation continuity)
        if (response.data.session_id) {
          this.sessionId = response.data.session_id
        }

        // Update message with copy response
        this.messages[messageIndex] = {
          userText,
          loading: false,
          copyResponse: response.data.copy_response,
          sessionInfo: {
            session_id: response.data.session_id,
            duration_ms: response.data.duration_ms,
            cost_usd: response.data.cost_usd,
            versions_generated: response.data.versions_generated
          }
        }

      } catch (error) {
        console.error('Error sending message:', error)

        // Show error state with dynamic number of variations
        const errorVariations = []
        const errorMessages = [
          "Error: Could not connect to the copywriting service",
          "Please verify the backend is running on port 8000",
          "Try refreshing the page and asking again",
          "Check your network connection and try again",
          "Backend service may be temporarily unavailable",
          "Please wait a moment and retry your request",
          "Service connection failed - please retry",
          "Unable to reach the copywriting service",
          "Connection timeout - please try again",
          "Service unavailable - check backend status"
        ]

        // Generate the correct number of error variations
        for (let i = 0; i < this.versionsConfigured; i++) {
          errorVariations.push(errorMessages[i % errorMessages.length])
        }

        this.messages[messageIndex] = {
          userText,
          loading: false,
          copyResponse: {
            primary_response: "Sorry, I encountered an error generating copy. Please check if the backend server is running and try again.",
            multi_version_copy_responses: errorVariations
          },
          sessionInfo: null
        }
      }

      this.isLoading = false

      // Scroll to bottom after response
      this.$nextTick(() => {
        this.scrollToBottom()
      })
    },

    scrollToBottom() {
      const container = this.$refs.messagesContainer
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    },

    getVariationClass(index) {
      const classes = ['variation-1', 'variation-2', 'variation-3', 'variation-4', 'variation-5']
      return classes[index % classes.length]
    },

    getVariationIcon(index) {
      const icons = ['🎯', '✨', '🚀', '💎', '⭐']
      return icons[index % icons.length]
    },

    async copyToClipboard(text) {
      try {
        await navigator.clipboard.writeText(text)
        this.showToast('Copied to clipboard!', 'success')
      } catch (err) {
        this.showToast('Failed to copy to clipboard', 'error')
      }
    },

    showToast(message, type = 'success') {
      this.toast = {
        show: true,
        message,
        type
      }
      setTimeout(() => {
        this.toast.show = false
      }, 3000)
    },

    formatFileSize(bytes) {
      if (bytes < 1024) return bytes + ' B'
      if (bytes < 1024 * 1024) return Math.round(bytes / 1024) + ' KB'
      return Math.round(bytes / (1024 * 1024)) + ' MB'
    },

    removeFile(index) {
      this.contextFiles.splice(index, 1)
      this.showToast('Context file removed', 'success')
    },

    // Drag and Drop handlers
    onDragEnter(e) {
      this.isDragOver = true
    },

    onDragOver(e) {
      this.isDragOver = true
    },

    onDragLeave(e) {
      // Only set to false if we're leaving the input area entirely
      if (!e.currentTarget.contains(e.relatedTarget)) {
        this.isDragOver = false
      }
    },

    async onDrop(e) {
      this.isDragOver = false

      const files = Array.from(e.dataTransfer.files)

      for (const file of files) {
        // Only accept text files
        if (file.type.startsWith('text/') || file.name.endsWith('.md') || file.name.endsWith('.txt')) {
          try {
            const content = await this.readFileAsText(file)

            // Check if file already exists
            const existingIndex = this.contextFiles.findIndex(f => f.name === file.name)
            if (existingIndex !== -1) {
              this.contextFiles[existingIndex] = {
                name: file.name,
                content: content
              }
              this.showToast(`Updated context file: ${file.name}`, 'success')
            } else {
              this.contextFiles.push({
                name: file.name,
                content: content
              })
              this.showToast(`Added context file: ${file.name}`, 'success')
            }
          } catch (error) {
            this.showToast(`Failed to read file: ${file.name}`, 'error')
          }
        } else {
          this.showToast(`Unsupported file type: ${file.name}`, 'error')
        }
      }
    },

    readFileAsText(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = e => resolve(e.target.result)
        reader.onerror = reject
        reader.readAsText(file)
      })
    }
  },

  async mounted() {
    // Focus on input when component mounts
    this.$refs.messageInput?.focus()

    // Fetch backend configuration
    try {
      const response = await fetch(`${this.apiBaseUrl}/config`)
      if (response.ok) {
        const config = await response.json()
        this.versionsConfigured = config.versions_configured || 3
        console.log(`✅ Backend configured for ${this.versionsConfigured} copy variations`)
      }
    } catch (error) {
      console.warn('Could not fetch backend configuration, using default of 3 versions:', error)
    }
  }
}
</script>

<style scoped>
.app {
  min-height: 100vh;
  padding: 0;
  background: #0a0e27;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: #0a0e27;
  padding: 15px;
  text-align: center;
}

.header-content .title {
  font-size: 1.8rem;
  font-weight: 800;
  background: linear-gradient(135deg, #ffffff 0%, #64b5f6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}

.header-content .icon {
  margin-right: 15px;
}

.header-content .subtitle {
  color: #bbbbbb;
  font-size: 0.9rem;
  font-weight: 500;
  margin: 5px 0 0 0;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #0a0e27;
  overflow: hidden;
}

.copy-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.context-files {
  padding: 8px 20px;
  background: transparent;
}

.context-file-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.context-file {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #1a1a2e;
  padding: 6px 10px;
  border-radius: 0;
  border-left: 3px solid #fbbf24;
  font-size: 0.85rem;
  color: #ffffff;
}

.file-icon {
  font-size: 0.9rem;
  color: #fbbf24;
}

.file-name {
  font-weight: 500;
  color: #e5e5e5;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-btn {
  background: none;
  border: none;
  color: #fbbf24;
  cursor: pointer;
  font-weight: bold;
  font-size: 1rem;
  padding: 0;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.remove-btn:hover {
  opacity: 1;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 15px 20px;
  scroll-behavior: smooth;
}

.welcome-message {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 20px;
}

.welcome-list {
  list-style: none;
  padding: 0;
  margin: 0;
  max-width: 450px;
}

.welcome-list li {
  margin: 10px 0;
  color: #999999;
  font-size: 0.9rem;
  line-height: 1.3;
}

.welcome-list strong {
  color: #e5e5e5;
}

.message-group {
  margin-bottom: 25px;
}

.message {
  margin-bottom: 20px;
}

.user-message .message-content {
  background: #0d2818;
  color: #ffffff;
  padding: 15px 20px;
  border-radius: 0;
  max-width: 80%;
  margin-left: auto;
  font-size: 1rem;
  line-height: 1.5;
}

.user-icon {
  margin-right: 8px;
  font-size: 1.1rem;
}

.copy-responses {
  margin-top: 20px;
}

.primary-response {
  background: #1e3a5f;
  border-radius: 0;
  overflow: hidden;
  margin-bottom: 15px;
}

.response-header {
  padding: 12px 15px;
  background: #2a4a6f;
  font-weight: 600;
  color: #ffffff;
}

.response-icon {
  margin-right: 10px;
  font-size: 1.2rem;
}

.response-content {
  padding: 15px;
  background: #1e3a5f;
  color: #ffffff;
  line-height: 1.6;
  font-size: 0.95rem;
}

.copy-variations h4 {
  margin-bottom: 12px;
  color: #ffffff;
  font-size: 1.1rem;
}

.variations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 15px;
}

.copy-variation {
  border-radius: 0;
  overflow: hidden;
  transition: transform 0.2s ease;
}

.copy-variation:hover {
  transform: translateY(-2px);
}

.copy-variation.variation-1 {
  background: #1a1f3a;
}

.copy-variation.variation-2 {
  background: #162a3f;
}

.copy-variation.variation-3 {
  background: #1e2d3d;
}

.copy-variation.variation-4 {
  background: #1a2e3f;
}

.copy-variation.variation-5 {
  background: #182838;
}

.variation-header {
  padding: 12px 15px;
  background: #2a3f5f;
  font-weight: 600;
  color: #ffffff;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.variation-icon {
  margin-right: 10px;
  font-size: 1.2rem;
}

.copy-btn {
  background: #2563eb;
  border: none;
  color: white;
  cursor: pointer;
  padding: 5px 8px;
  border-radius: 0;
  font-size: 1rem;
  transition: background 0.2s ease;
}

.copy-btn:hover {
  background: #1d4ed8;
}

.variation-content {
  padding: 15px;
  background: transparent;
  color: #ffffff;
  line-height: 1.6;
  font-size: 0.95rem;
}

.loading-responses {
  margin-top: 20px;
}

.loading-primary {
  border-radius: 0;
  overflow: hidden;
  background: #1e3a5f;
  margin-bottom: 15px;
}

.loading-variations h4 {
  margin-bottom: 15px;
  color: #ffffff;
  font-size: 1.2rem;
}

.loading-variation {
  border-radius: 0;
  overflow: hidden;
  background: #1a1f3a;
}

.loading-header {
  padding: 12px 15px;
  background: #2a3f5f;
  font-weight: 600;
  color: #ffffff;
}

.loading-content {
  padding: 15px;
  background: transparent;
  color: #ffffff;
}

.loading-dots {
  display: flex;
  gap: 5px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ccc;
  animation: bounce 1.4s ease-in-out infinite both;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  } 40% {
    transform: scale(1);
  }
}

.session-info {
  text-align: center;
  margin-top: 15px;
  color: #888;
  font-size: 0.85rem;
}

.input-area {
  padding: 15px 20px;
  background: transparent;
  position: relative;
  transition: background-color 0.2s ease;
}

.drag-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(10, 14, 39, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  pointer-events: none;
}

.drag-indicator {
  padding: 12px 24px;
  background: #fbbf24;
  color: #0a0e27;
  font-weight: 600;
  font-size: 0.95rem;
  border-radius: 0;
}

.input-container {
  display: flex;
  gap: 12px;
  max-width: 1000px;
  margin: 0 auto;
  align-items: stretch;
}

.message-input {
  flex: 1;
  padding: 10px 15px;
  border: none;
  border-radius: 0 !important;
  font-size: 0.95rem;
  resize: none;
  transition: background-color 0.3s ease;
  background: #1a2244;
  color: #ffffff;
  min-height: 44px;
  font-family: inherit;
  outline: none;
}

.message-input:focus {
  outline: none;
  background: #1e2850;
}

.message-input:disabled {
  background: #0f1726;
  color: rgba(255, 255, 255, 0.4);
}

.send-button {
  padding: 10px 20px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 0 !important;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 600;
  transition: background-color 0.2s ease;
  white-space: nowrap;
  min-width: 120px;
}

.send-button:hover:not(:disabled) {
  background: #1d4ed8;
}

.send-button:disabled {
  background: #333333;
  cursor: not-allowed;
}

.toast {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 15px 20px;
  border-radius: 10px;
  background: #000000;
  color: white;
  font-weight: 600;
  z-index: 1000;
  animation: slideIn 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}

.toast.success {
  background: #000000;
  color: #ffffff;
  border: 1px solid #333333;
}

.toast.error {
  background: #1a0000;
  color: #ff6b6b;
  border: 1px solid #ff3333;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Responsive Design */
@media (max-width: 768px) {
  .app {
    padding: 10px;
  }

  .header-content .title {
    font-size: 1.5rem;
  }

  .messages {
    padding: 15px;
  }

  .variations-grid {
    grid-template-columns: 1fr;
  }

  .input-area {
    padding: 15px;
  }

  .input-container {
    flex-direction: column;
  }

  .message-input {
    width: 100%;
  }

  .send-button {
    align-self: stretch;
  }
}
</style>