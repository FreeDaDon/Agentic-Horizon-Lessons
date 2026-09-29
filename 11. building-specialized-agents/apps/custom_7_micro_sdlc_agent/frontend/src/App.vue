<template>
  <div class="app-container">
    <header class="app-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="app-title">{{ appTitle }}</h1>
          <div v-if="activeWorkflows > 0" class="active-indicator">
            <span class="pulse-dot"></span>
            <span>{{ activeWorkflows }} workflow{{ activeWorkflows > 1 ? 's' : '' }} running</span>
          </div>
        </div>
        <div class="header-right">
          <div class="header-stats">
            <span>Plan → Build → Review → Ship</span>
          </div>
          <ThemeToggle />
        </div>
      </div>
    </header>

    <div class="board-container">
      <div class="board-wrapper">
        <div class="kanban-board">
          <div
            v-for="stage in stages"
            :key="stage.name"
            :class="['kanban-column', `column-${stage.name}`]"
          >
            <div class="column-header">
              <div class="column-title">
                <span>{{ stage.label }}</span>
              </div>
              <span class="column-count">{{ ticketsByStage[stage.name]?.length || 0 }}</span>
            </div>

            <div class="column-content">
              <!-- Add button for idle column -->
              <button
                v-if="stage.name === 'idle'"
                @click="showCreateModal = true"
                class="add-ticket-button"
              >
                <span class="plus-icon">+</span> New Ticket
              </button>

              <!-- Use draggable with traditional v-for approach -->
              <draggable
                :list="getTicketsForStage(stage.name)"
                group="tickets"
                :move="checkMove"
                @change="onDragChange($event, stage.name)"
                class="draggable-list"
              >
                <TicketCard
                  v-for="ticket in ticketsByStage[stage.name]"
                  :key="ticket.id"
                  :ticket="ticket"
                  :canDrag="canDrag(ticket.stage)"
                  @click="selectTicket(ticket)"
                />
              </draggable>
              <div v-if="!ticketsByStage[stage.name] || ticketsByStage[stage.name].length === 0" class="empty-state">
                No tickets
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Ticket Modal -->
    <CreateTicketModal
      v-if="showCreateModal"
      :session-info="sessionInfo"
      @close="showCreateModal = false"
      @create="handleCreateTicket"
    />

    <!-- Ticket Details Modal -->
    <TicketDetailsModal
      v-if="selectedTicket"
      :ticket="selectedTicket"
      @close="selectedTicket = null"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { VueDraggableNext } from 'vue-draggable-next'
import { useTicketsStore } from './stores/tickets'
import { useTheme } from './composables/useTheme'
import { useAppTitle } from './composables/useAppTitle'
import TicketCard from './components/TicketCard.vue'
import CreateTicketModal from './components/CreateTicketModal.vue'
import TicketDetailsModal from './components/TicketDetailsModal.vue'
import ThemeToggle from './components/ThemeToggle.vue'

export default {
  name: 'App',
  components: {
    draggable: VueDraggableNext,
    TicketCard,
    CreateTicketModal,
    TicketDetailsModal,
    ThemeToggle
  },
  setup() {
    const store = useTicketsStore()
    const { initializeTheme } = useTheme()
    const { appTitle } = useAppTitle()
    const showCreateModal = ref(false)
    const selectedTicket = ref(null)

    const stages = [
      { name: 'idle', label: 'Idle' },
      { name: 'plan', label: 'Plan' },
      { name: 'build', label: 'Build' },
      { name: 'review', label: 'Review' },
      { name: 'shipped', label: 'Shipped' },
      { name: 'errored', label: 'Errored' },
      { name: 'archived', label: 'Archived' }
    ]

    const ticketsByStage = computed(() => store.ticketsByStage)
    const sessionInfo = computed(() => store.sessionInfo)
    const activeWorkflows = computed(() => {
      // Count tickets in plan, build, or review stages
      const activeStages = ['plan', 'build', 'review']
      return store.tickets.filter(t => activeStages.includes(t.stage)).length
    })

    // Helper to get mutable tickets list for draggable
    const getTicketsForStage = (stageName) => {
      return store.tickets.filter(t => t.stage === stageName)
    }

    const canDrag = (stage) => {
      // Only idle, shipped, errored, and archived can be dragged
      return ['idle', 'shipped', 'errored', 'archived'].includes(stage)
    }

    const checkMove = (evt) => {
      // Check if the item being dragged can be moved
      // evt.draggedContext.element is the ticket being dragged
      const ticket = evt.draggedContext.element
      // Only allow dragging from allowed stages
      return canDrag(ticket.stage)
    }

    const onDragChange = async (event, toStage) => {
      if (event.added) {
        const ticket = event.added.element

        try {
          await store.updateTicketStage(ticket.id, toStage)
        } catch (error) {
          // Revert on error
          await store.fetchTickets()
          alert(`Failed to move ticket: ${error.response?.data?.detail || error.message}`)
        }
      }
    }

    const handleCreateTicket = async (ticketData) => {
      try {
        await store.createTicket(ticketData)
        showCreateModal.value = false
        // Fetch tickets again to ensure UI is in sync
        await store.fetchTickets()
      } catch (error) {
        alert(`Failed to create ticket: ${error.message}`)
      }
    }

    const selectTicket = (ticket) => {
      selectedTicket.value = ticket
    }

    onMounted(async () => {
      initializeTheme()
      await store.fetchTickets()
      await store.fetchSessionInfo()
      store.connectWebSocket()
    })

    onUnmounted(() => {
      store.disconnectWebSocket()
    })

    return {
      store,
      stages,
      ticketsByStage,
      sessionInfo,
      activeWorkflows,
      appTitle,
      showCreateModal,
      selectedTicket,
      canDrag,
      checkMove,
      onDragChange,
      handleCreateTicket,
      selectTicket,
      getTicketsForStage
    }
  }
}
</script>

<style scoped>
.app-container {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
}

/* Header */
.app-header {
  background: var(--bg-secondary);
  padding: 1.5rem 2rem;
  border-bottom: 1px solid var(--border-color);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.app-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.active-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.75rem;
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.4);
  border-radius: 8px;
  font-size: 0.875rem;
  color: var(--success-color);
  animation: fadeIn 0.3s ease;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: var(--success-color);
  border-radius: 50%;
  animation: pulse 2s infinite;
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
}

.header-stats {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 0.875rem;
  color: var(--text-muted);
}

/* Kanban Board */
.board-container {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.board-wrapper {
  flex: 1;
  overflow-x: auto;
  padding: 1.5rem;
}

.kanban-board {
  display: flex;
  gap: 1rem;
  min-width: fit-content;
  height: 100%;
}

/* Columns */
.kanban-column {
  width: 300px;
  display: flex;
  flex-direction: column;
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border-radius: 8px 8px 0 0;
  font-weight: 600;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.column-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.column-count {
  background: rgba(0, 0, 0, 0.3);
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  opacity: 0.9;
}

.column-content {
  flex: 1;
  background: var(--bg-tertiary);
  border-radius: 0 0 8px 8px;
  padding: 0.5rem;
  overflow-y: auto;
  min-height: 200px;
  max-height: calc(100vh - 250px);
  border: 1px solid var(--border-color);
  border-top: none;
}

.draggable-list {
  min-height: 150px;
  padding: 0.5rem;
}

/* Add Ticket Button */
.add-ticket-button {
  width: 100%;
  padding: 0.75rem;
  background: var(--bg-secondary);
  border: 2px dashed var(--border-color);
  border-radius: 8px;
  color: var(--text-muted);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 0.5rem;
}

.add-ticket-button:hover {
  background: var(--bg-tertiary);
  border-color: var(--accent-color);
  color: var(--accent-color);
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.2);
}

.plus-icon {
  font-size: 1.25rem;
  font-weight: 300;
}

/* Empty State */
.empty-state {
  padding: 2rem 1rem;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.875rem;
}

/* Column States */
.column-idle .column-header {
  background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
  color: white;
}

.column-plan .column-header {
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  color: white;
}

.column-build .column-header {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  color: white;
}

.column-review .column-header {
  background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
  color: white;
}

.column-shipped .column-header {
  background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
  color: white;
}

.column-errored .column-header {
  background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
  color: white;
}

.column-archived .column-header {
  background: linear-gradient(135deg, #374151 0%, #1f2937 100%);
  color: white;
}

/* Drag States */
.drag-over {
  background: rgba(59, 130, 246, 0.1) !important;
  border-color: #3b82f6 !important;
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.3) !important;
}

/* Animations */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.2);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

/* Scrollbar Styles */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-secondary);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}

/* Responsive */
@media (max-width: 768px) {
  .kanban-column {
    width: 250px;
  }

  .app-header {
    padding: 1rem;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
}
</style>

<style>
/* CSS Custom Properties for Theme Support */
:root {
  /* Default Dark Theme Variables */
  --bg-primary: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
  --bg-secondary: #1a1a1a;
  --bg-tertiary: #2a2a2a;
  --text-primary: #e5e5e5;
  --text-secondary: #bbb;
  --text-muted: #888;
  --border-color: #333;
  --accent-color: #3b82f6;
  --success-color: #10b981;
  --error-color: #dc2626;
  --warning-color: #d97706;

  /* Golden theme colors for ticket edges */
  --golden-primary: #FFD700;
  --golden-secondary: #FFA500;
  --golden-accent: #DAA520;
  --golden-gradient: linear-gradient(45deg, #FFD700, #FFA500);

  /* Toggle-specific colors */
  --toggle-bg: rgba(255, 255, 255, 0.1);
  --toggle-bg-hover: rgba(255, 255, 255, 0.2);
  --toggle-border-hover: #3b82f6;
  --toggle-shadow: rgba(59, 130, 246, 0.3);
}

/* Light Theme Variables */
[data-theme="light"] {
  --bg-primary: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  --bg-secondary: #ffffff;
  --bg-tertiary: #f1f5f9;
  --text-primary: #1e293b;
  --text-secondary: #475569;
  --text-muted: #64748b;
  --border-color: #e2e8f0;
  --accent-color: #3b82f6;
  --success-color: #059669;
  --error-color: #dc2626;
  --warning-color: #d97706;

  /* Golden theme colors for ticket edges */
  --golden-primary: #FFD700;
  --golden-secondary: #FFA500;
  --golden-accent: #DAA520;
  --golden-gradient: linear-gradient(45deg, #FFD700, #FFA500);

  /* Toggle-specific colors for light mode */
  --toggle-bg: rgba(0, 0, 0, 0.05);
  --toggle-bg-hover: rgba(0, 0, 0, 0.1);
  --toggle-border-hover: #3b82f6;
  --toggle-shadow: rgba(59, 130, 246, 0.2);
}

/* Global styles for consistent light text theming */
div, span, p, h1, h2, h3, h4, h5, h6 {
  color: var(--text-primary);
}

/* Specific overrides for darker text where needed */
.meta-label {
  color: var(--text-secondary);
}

.meta-value {
  color: var(--text-muted);
}

.stat-label {
  color: var(--text-muted);
}

.stats-title {
  color: var(--text-secondary);
}

/* Input and form elements */
input, textarea, select {
  color: var(--text-primary);
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
}

/* Button text */
button {
  color: var(--text-primary);
}

/* Ensure certain UI elements maintain their intended colors */
.column-count,
.header-stats,
.empty-state {
  color: var(--text-muted);
}
</style>