<template>
  <div
    class="ticket-card"
    :class="{ 'not-draggable': !canDrag }"
    @click="$emit('click')"
  >
    <div class="ticket-header">
      <span class="ticket-id">#{{ ticket.id }}</span>
      <span class="ticket-model" :class="modelClass">
        {{ modelLabel }}
      </span>
    </div>

    <h4 class="ticket-title">{{ ticket.title }}</h4>

    <div class="ticket-meta">
      <div class="meta-item">
        📁 Directory: {{ ticket.parent_codebase_path || '.' }}
      </div>
      <div class="meta-item">
        📅 Last updated: {{ formatDate(ticket.created_at) }}
      </div>
    </div>

    <div v-if="ticket.plan_path" class="ticket-plan">
      <span class="plan-icon">📋</span>
      <span class="plan-path">{{ ticket.plan_path }}</span>
    </div>

    <div class="stats-header">
      <span class="stats-title">Messages/Tools per Agent</span>
    </div>

    <div class="ticket-stats">
      <div class="stat stat-plan">
        <span class="stat-label">Plan</span>
        <div class="stat-numbers">
          <span class="stat-value" :class="{ 'pulse': isStageActive('plan') }">
            {{ ticket.total_plan_messages || 0 }}
          </span>
          <span class="stat-divider">/</span>
          <span class="stat-value tool-count">
            {{ ticket.total_plan_tool_calls || 0 }}
          </span>
        </div>
      </div>
      <div class="stat stat-build">
        <span class="stat-label">Build</span>
        <div class="stat-numbers">
          <span class="stat-value" :class="{ 'pulse': isStageActive('build') }">
            {{ ticket.total_build_messages || 0 }}
          </span>
          <span class="stat-divider">/</span>
          <span class="stat-value tool-count">
            {{ ticket.total_build_tool_calls || 0 }}
          </span>
        </div>
      </div>
      <div class="stat stat-review">
        <span class="stat-label">Review</span>
        <div class="stat-numbers">
          <span class="stat-value" :class="{ 'pulse': isStageActive('review') }">
            {{ ticket.total_review_messages || 0 }}
          </span>
          <span class="stat-divider">/</span>
          <span class="stat-value tool-count">
            {{ ticket.total_review_tool_calls || 0 }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TicketCard',
  props: {
    ticket: {
      type: Object,
      required: true
    },
    canDrag: {
      type: Boolean,
      default: true
    }
  },
  computed: {
    modelClass() {
      if (this.ticket.model?.includes('sonnet')) return 'model-sonnet'
      if (this.ticket.model?.includes('opus')) return 'model-opus'
      return 'model-sonnet'
    },
    modelLabel() {
      if (this.ticket.model?.includes('sonnet')) return 'SONNET'
      if (this.ticket.model?.includes('opus')) return 'OPUS'
      return 'SONNET'
    }
  },
  methods: {
    formatDate(dateString) {
      if (!dateString) return 'N/A'

      const date = new Date(dateString)
      const now = new Date()
      const diffMs = now - date
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMins / 60)
      const diffDays = Math.floor(diffHours / 24)

      if (diffMins < 1) return 'just now'
      if (diffMins < 60) return `${diffMins}m ago`
      if (diffHours < 24) return `${diffHours}h ago`
      if (diffDays < 7) return `${diffDays}d ago`

      return date.toLocaleDateString()
    },
    isStageActive(stage) {
      return this.ticket.stage === stage
    }
  }
}
</script>

<style scoped>
.ticket-card {
  background: var(--bg-secondary);
  border: 2px solid var(--golden-primary);
  border-radius: 8px;
  padding: 0.875rem;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  box-shadow: 0 2px 4px rgba(255, 215, 0, 0.2);
}

.ticket-card:hover {
  background: var(--bg-tertiary);
  border-color: var(--golden-secondary);
  box-shadow: 0 4px 8px rgba(255, 215, 0, 0.3);
  transform: translateY(-2px);
}

.ticket-card.not-draggable {
  cursor: pointer;
}

.ticket-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.ticket-id {
  font-size: 0.9rem;
  color: #888;
  font-weight: 600;
}

.ticket-model {
  font-size: 0.7rem;
  padding: 0.125rem 0.375rem;
  border-radius: 9999px;
  font-weight: 600;
  text-transform: uppercase;
}

.model-sonnet {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.model-opus {
  background: rgba(168, 85, 247, 0.2);
  color: #a78bfa;
  border: 1px solid rgba(168, 85, 247, 0.3);
}

.ticket-title {
  margin: 0 0 0.75rem 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: #fff;
  line-height: 1.3;
}

.ticket-meta {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  margin-bottom: 0.5rem;
}

.meta-item {
  font-size: 0.75rem;
  color: #bbb;
}

.meta-label {
  opacity: 0.7;
}

.meta-value {
  color: #888;
}

.ticket-plan {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  background: #2a2a2a;
  border: 1px solid #333;
  border-radius: 4px;
  margin-bottom: 0.5rem;
}

.plan-icon {
  opacity: 0.7;
}

.plan-path {
  color: #a0a0a0;
  font-family: monospace;
  font-size: 0.7rem;
}

.stats-header {
  margin-top: 0.5rem;
  margin-bottom: 0.375rem;
}

.stats-title {
  font-size: 0.65rem;
  color: #bbb;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.ticket-stats {
  display: flex;
  gap: 0.75rem;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  font-size: 0.7rem;
  min-width: 50px;
}

.stat-label {
  color: #aaa;
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-numbers {
  display: flex;
  align-items: center;
  gap: 0.125rem;
  background: #2a2a2a;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  border: 1px solid #333;
}

.stat-value {
  color: #e0e0e0;
  font-weight: 700;
  font-size: 0.75rem;
}

.stat-divider {
  color: #666;
  font-weight: 300;
  font-size: 0.65rem;
}

.tool-count {
  color: #888;
  font-weight: 600;
}

.stat-value.pulse {
  animation: pulse 1.5s ease-in-out infinite;
  color: #3b82f6;
  text-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
}

/* Stat color themes */
.stat-plan .stat-label {
  color: #60a5fa;
}

.stat-plan .stat-numbers {
  background: rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.3);
}

.stat-build .stat-label {
  color: #34d399;
}

.stat-build .stat-numbers {
  background: rgba(16, 185, 129, 0.15);
  border-color: rgba(16, 185, 129, 0.3);
}

.stat-review .stat-label {
  color: #fbbf24;
}

.stat-review .stat-numbers {
  background: rgba(245, 158, 11, 0.15);
  border-color: rgba(245, 158, 11, 0.3);
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* Golden edge ticket states */
.ticket-card.selected {
  border-color: var(--golden-accent);
  box-shadow: 0 0 0 3px rgba(255, 215, 0, 0.4);
}

.ticket-card.dragging {
  border-color: var(--golden-secondary);
  box-shadow: 0 8px 16px rgba(255, 215, 0, 0.4);
  transform: rotate(2deg);
}

.ticket-card.disabled {
  border-color: rgba(255, 215, 0, 0.5);
  opacity: 0.7;
}

/* Accessibility enhancements */
.ticket-card:focus {
  outline: 2px solid var(--golden-accent);
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  .ticket-card {
    transition: none;
  }
}

/* Responsive design adjustments */
@media (max-width: 768px) {
  .ticket-card {
    border-width: 1.5px;
  }
}

@media (max-width: 480px) {
  .ticket-card {
    border-width: 1px;
    box-shadow: 0 1px 2px rgba(255, 215, 0, 0.2);
  }
}
</style>