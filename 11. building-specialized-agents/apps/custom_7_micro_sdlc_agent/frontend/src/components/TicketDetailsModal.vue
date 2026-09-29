<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <div>
          <h2>{{ ticket.title }}</h2>
          <div class="ticket-badges">
            <span class="badge" :class="`badge-${ticket.stage}`">
              {{ ticket.stage }}
            </span>
            <span class="badge" :class="`badge-${ticket.model}`">
              {{ ticket.model }}
            </span>
            <span class="badge badge-id">#{{ ticket.id }}</span>
          </div>
        </div>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>

      <div class="modal-body">
        <!-- Ticket Info -->
        <section class="info-section">
          <h3>📋 Ticket Information</h3>
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">Stage:</span>
              <span class="info-value">{{ ticket.stage }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Model:</span>
              <span class="info-value">{{ ticket.model }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Codebase:</span>
              <span class="info-value">{{ ticket.parent_codebase_path || '.' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Created:</span>
              <span class="info-value">{{ formatDateTime(ticket.created_at) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Updated:</span>
              <span class="info-value">{{ formatDateTime(ticket.updated_at) }}</span>
            </div>
            <div class="info-item" v-if="ticket.plan_path">
              <span class="info-label">Plan Path:</span>
              <span class="info-value mono">{{ ticket.plan_path }}</span>
            </div>
          </div>
        </section>

        <!-- User Request -->
        <section class="info-section">
          <h3>💭 User Request</h3>
          <pre class="content-block">{{ ticket.content_user_request_prompt }}</pre>
        </section>

        <!-- Statistics -->
        <section class="info-section" v-if="hasStats">
          <h3>📊 Statistics</h3>
          <div class="stats-grid">
            <div class="stat-card" v-if="ticket.total_plan_messages > 0">
              <div class="stat-label">Plan Phase</div>
              <div class="stat-values">
                <div class="stat-item">
                  <span class="stat-number">{{ ticket.total_plan_messages }}</span>
                  <span class="stat-desc">messages</span>
                </div>
                <div class="stat-item">
                  <span class="stat-number">{{ ticket.total_plan_tool_calls }}</span>
                  <span class="stat-desc">tool calls</span>
                </div>
              </div>
            </div>
            <div class="stat-card" v-if="ticket.total_build_messages > 0">
              <div class="stat-label">Build Phase</div>
              <div class="stat-values">
                <div class="stat-item">
                  <span class="stat-number">{{ ticket.total_build_messages }}</span>
                  <span class="stat-desc">messages</span>
                </div>
                <div class="stat-item">
                  <span class="stat-number">{{ ticket.total_build_tool_calls }}</span>
                  <span class="stat-desc">tool calls</span>
                </div>
              </div>
            </div>
            <div class="stat-card" v-if="ticket.total_review_messages > 0">
              <div class="stat-label">Review Phase</div>
              <div class="stat-values">
                <div class="stat-item">
                  <span class="stat-number">{{ ticket.total_review_messages }}</span>
                  <span class="stat-desc">messages</span>
                </div>
                <div class="stat-item">
                  <span class="stat-number">{{ ticket.total_review_tool_calls }}</span>
                  <span class="stat-desc">tool calls</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Agent Messages -->
        <section class="info-section" v-if="ticket.agent_messages?.length > 0">
          <h3>🤖 Agent Messages</h3>
          <div class="messages-container">
            <div
              v-for="(message, index) in ticket.agent_messages"
              :key="index"
              class="agent-message"
              :class="`message-${message.type}`"
            >
              <div class="message-header">
                <span class="message-emoji">{{ message.emoji }}</span>
                <span class="message-stage">{{ message.stage }}</span>
                <span class="message-type">{{ message.type }}</span>
              </div>
              <div class="message-content">{{ message.content }}</div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'TicketDetailsModal',
  props: {
    ticket: {
      type: Object,
      required: true
    }
  },
  emits: ['close'],
  setup(props) {
    const hasStats = computed(() => {
      return (
        props.ticket.total_plan_messages > 0 ||
        props.ticket.total_build_messages > 0 ||
        props.ticket.total_review_messages > 0
      )
    })

    const formatDateTime = (dateString) => {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleString()
    }

    return {
      hasStats,
      formatDateTime
    }
  }
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  width: 90%;
  max-width: 900px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1.5rem;
  border-bottom: 1px solid #333;
}

.modal-header h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  color: #fff;
}

.ticket-badges {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.badge-idle { background: rgba(107, 114, 128, 0.2); color: #9ca3af; border: 1px solid rgba(107, 114, 128, 0.3); }
.badge-plan { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
.badge-build { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
.badge-review { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
.badge-shipped { background: rgba(139, 92, 246, 0.2); color: #a78bfa; border: 1px solid rgba(139, 92, 246, 0.3); }
.badge-errored { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
.badge-archived { background: rgba(75, 85, 99, 0.2); color: #9ca3af; border: 1px solid rgba(75, 85, 99, 0.3); }
.badge-sonnet { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
.badge-opus { background: rgba(168, 85, 247, 0.2); color: #a78bfa; border: 1px solid rgba(168, 85, 247, 0.3); }
.badge-id { background: rgba(107, 114, 128, 0.2); color: #9ca3af; border: 1px solid rgba(107, 114, 128, 0.3); }

.close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  color: #888;
  cursor: pointer;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #2a2a2a;
  color: #fff;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.info-section {
  margin-bottom: 2rem;
}

.info-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.125rem;
  color: #fff;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.info-item {
  display: flex;
  gap: 0.5rem;
}

.info-label {
  font-weight: 500;
  color: #a0a0a0;
}

.info-value {
  color: #fff;
}

.info-value.mono {
  font-family: monospace;
  font-size: 0.875rem;
  color: #60a5fa;
}

.content-block {
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 8px;
  padding: 1rem;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  font-size: 0.875rem;
  line-height: 1.5;
  color: #fff;
  margin: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.stat-card {
  background: #2a2a2a;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 1rem;
}

.stat-label {
  font-weight: 600;
  color: #a0a0a0;
  margin-bottom: 0.75rem;
  display: block;
}

.stat-values {
  display: flex;
  gap: 1.5rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-number {
  font-size: 1.5rem;
  font-weight: 700;
  color: #3b82f6;
}

.stat-desc {
  font-size: 0.75rem;
  color: #666;
}

.messages-container {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 0.5rem;
  background: #2a2a2a;
}

.agent-message {
  margin-bottom: 0.75rem;
  padding: 0.75rem;
  border-radius: 6px;
  border-left: 3px solid;
}

.message-text { border-left-color: #3b82f6; background: rgba(59, 130, 246, 0.1); }
.message-thinking { border-left-color: #8b5cf6; background: rgba(139, 92, 246, 0.1); }
.message-tool_use { border-left-color: #10b981; background: rgba(16, 185, 129, 0.1); }
.message-result { border-left-color: #f59e0b; background: rgba(245, 158, 11, 0.1); }
.message-error { border-left-color: #ef4444; background: rgba(239, 68, 68, 0.1); }

.message-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-size: 0.75rem;
}

.message-emoji {
  font-size: 1rem;
}

.message-stage {
  font-weight: 600;
  color: #e0e0e0;
  text-transform: capitalize;
}

.message-type {
  color: #888;
  padding: 0.125rem 0.5rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 9999px;
  font-size: 0.7rem;
}

.message-content {
  font-size: 0.875rem;
  line-height: 1.5;
  color: #a0a0a0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* Scrollbar Styles */
::-webkit-scrollbar {
  width: 8px;
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
</style>