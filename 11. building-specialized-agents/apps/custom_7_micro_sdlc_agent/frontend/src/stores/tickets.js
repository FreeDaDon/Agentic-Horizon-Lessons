import { defineStore } from 'pinia'
import axios from 'axios'

const API_URL = 'http://127.0.0.1:8001'
const WS_URL = 'ws://127.0.0.1:8001/ws'

export const useTicketsStore = defineStore('tickets', {
  state: () => ({
    tickets: [],
    sessionInfo: null,
    wsConnection: null,
    isConnected: false,
    messageQueue: [],
    processingMessages: false,
    wsHealthCheck: null,
    lastMessageTime: null
  }),

  getters: {
    ticketsByStage: (state) => {
      const stages = ['idle', 'plan', 'build', 'review', 'shipped', 'errored', 'archived']
      const grouped = {}

      stages.forEach(stage => {
        grouped[stage] = state.tickets.filter(t => t.stage === stage)
      })

      return grouped
    },

    getTicketById: (state) => (id) => {
      return state.tickets.find(t => t.id === id)
    }
  },

  actions: {
    async fetchTickets() {
      try {
        const response = await axios.get(`${API_URL}/tickets`)
        this.tickets = response.data
      } catch (error) {
        console.error('Failed to fetch tickets:', error)
      }
    },

    async fetchSpecificTicket(ticketId) {
      try {
        const response = await axios.get(`${API_URL}/tickets/${ticketId}`)
        const updatedTicket = response.data

        // Update or add the ticket in local state
        const existingIndex = this.tickets.findIndex(t => t.id === ticketId)
        if (existingIndex >= 0) {
          this.tickets[existingIndex] = updatedTicket
        } else {
          this.tickets.push(updatedTicket)
        }
      } catch (error) {
        console.error(`Failed to fetch ticket ${ticketId}:`, error)
      }
    },

    async fetchSessionInfo() {
      try {
        const response = await axios.get(`${API_URL}/session`)
        this.sessionInfo = response.data
      } catch (error) {
        console.error('Failed to fetch session info:', error)
      }
    },

    async validateStateConsistency() {
      try {
        const response = await axios.get(`${API_URL}/tickets`)
        const serverTickets = response.data

        // Check for missing or outdated tickets
        const inconsistencies = []

        for (const serverTicket of serverTickets) {
          const localTicket = this.tickets.find(t => t.id === serverTicket.id)

          if (!localTicket) {
            inconsistencies.push({ type: 'missing', ticket: serverTicket })
          } else if (localTicket.stage !== serverTicket.stage) {
            inconsistencies.push({
              type: 'stage_mismatch',
              local: localTicket,
              server: serverTicket
            })
          }
        }

        if (inconsistencies.length > 0) {
          console.warn('State inconsistencies detected:', inconsistencies)
          // Resolve by using server state as source of truth
          this.tickets = serverTickets
        }
      } catch (error) {
        console.error('Failed to validate state consistency:', error)
      }
    },

    async createTicket(ticketData) {
      try {
        const response = await axios.post(`${API_URL}/tickets`, ticketData)
        // Don't push here - let WebSocket handle it to avoid duplicates
        // The WebSocket message will arrive with the ticket_created event
        return response.data
      } catch (error) {
        console.error('Failed to create ticket:', error)
        throw error
      }
    },

    async updateTicketStage(ticketId, newStage) {
      try {
        await axios.put(`${API_URL}/tickets/${ticketId}/stage`, { stage: newStage })

        // Update local state
        const ticket = this.tickets.find(t => t.id === ticketId)
        if (ticket) {
          ticket.stage = newStage
        }
      } catch (error) {
        console.error('Failed to update ticket stage:', error)
        throw error
      }
    },

    connectWebSocket() {
      if (this.wsConnection) {
        return
      }

      this.wsConnection = new WebSocket(WS_URL)

      this.wsConnection.onopen = () => {
        console.log('WebSocket connected')
        this.isConnected = true
        this.startHealthCheck()
      }

      this.wsConnection.onmessage = (event) => {
        this.lastMessageTime = Date.now()
        const data = JSON.parse(event.data)
        this.handleWebSocketMessage(data)
      }

      this.wsConnection.onclose = () => {
        console.log('WebSocket disconnected')
        this.isConnected = false
        this.wsConnection = null

        if (this.wsHealthCheck) {
          clearInterval(this.wsHealthCheck)
          this.wsHealthCheck = null
        }

        // Reconnect after 3 seconds
        setTimeout(() => this.connectWebSocket(), 3000)
      }

      this.wsConnection.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    },

    startHealthCheck() {
      // Check WebSocket health every 30 seconds
      this.wsHealthCheck = setInterval(() => {
        const now = Date.now()
        const timeSinceLastMessage = now - (this.lastMessageTime || now)

        // If no message in 60 seconds, validate state
        if (timeSinceLastMessage > 60000) {
          console.log('WebSocket appears stale, validating state...')
          this.validateStateConsistency()
        }
      }, 30000)
    },

    async handleWebSocketMessage(data) {
      // Queue messages to prevent race conditions
      this.messageQueue.push(data)

      if (!this.processingMessages) {
        await this.processMessageQueue()
      }
    },

    async processMessageQueue() {
      this.processingMessages = true

      while (this.messageQueue.length > 0) {
        const message = this.messageQueue.shift()
        await this.processIndividualMessage(message)

        // Small delay to prevent overwhelming the UI
        await new Promise(resolve => setTimeout(resolve, 10))
      }

      this.processingMessages = false
    },

    async processIndividualMessage(data) {
      switch (data.type) {
        case 'ticket_created':
          // Check if ticket already exists to prevent duplicates
          const existingTicket = this.tickets.find(t => t.id === data.ticket.id)
          if (!existingTicket) {
            this.tickets.push(data.ticket)
          }
          break

        case 'stage_updated':
          const ticket = this.tickets.find(t => t.id === data.ticket_id)
          if (ticket) {
            // Update stage immediately for real-time UI response
            ticket.stage = data.new_stage

            // Log transition for debugging
            console.log(`Ticket ${data.ticket_id}: ${data.old_stage} → ${data.new_stage}`)
          } else {
            // If ticket not found locally, fetch it specifically
            console.warn(`Ticket ${data.ticket_id} not found locally, fetching...`)
            await this.fetchSpecificTicket(data.ticket_id)
          }
          break

        case 'agent_message':
          const msgTicket = this.tickets.find(t => t.id === data.ticket_id)
          if (msgTicket) {
            if (!msgTicket.agent_messages) {
              msgTicket.agent_messages = []
            }
            msgTicket.agent_messages.push(data.message)

            // Update counts for real-time display
            if (data.counts) {
              Object.assign(msgTicket, data.counts)
            }
          }
          break

        case 'workflow_started':
          // Optional: Add workflow start tracking
          const startTicket = this.tickets.find(t => t.id === data.ticket_id)
          if (startTicket) {
            startTicket.workflow_active = true
          }
          break

        case 'workflow_completed':
        case 'workflow_error':
          // REMOVE the fetchTickets() call - rely on stage_updated messages instead
          const completedTicket = this.tickets.find(t => t.id === data.ticket_id)
          if (completedTicket) {
            completedTicket.workflow_active = false
            // Stage should already be updated via stage_updated message
          }

          // Only fetch if we suspect data inconsistency
          if (!completedTicket) {
            console.warn(`Completed workflow ticket ${data.ticket_id} not found, fetching all tickets`)
            await this.fetchTickets()
          }
          break
      }
    },

    disconnectWebSocket() {
      if (this.wsHealthCheck) {
        clearInterval(this.wsHealthCheck)
        this.wsHealthCheck = null
      }

      if (this.wsConnection) {
        this.wsConnection.close()
        this.wsConnection = null
        this.isConnected = false
      }
    }
  }
})