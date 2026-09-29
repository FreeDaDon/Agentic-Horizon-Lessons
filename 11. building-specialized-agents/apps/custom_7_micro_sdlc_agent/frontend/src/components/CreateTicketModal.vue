<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h2>Create New Ticket</h2>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>

      <form @submit.prevent="handleSubmit" class="ticket-form">
        <div class="form-group">
          <label for="title">Title</label>
          <input
            id="title"
            v-model="formData.title"
            type="text"
            placeholder="Brief description of the task"
            required
          />
        </div>

        <div class="form-group">
          <label for="model">Model</label>
          <select id="model" v-model="formData.model" required>
            <option value="claude-sonnet-4-20250514">Sonnet (Faster)</option>
            <option value="claude-opus-4-1-20250805">Opus (Smarter)</option>
          </select>
        </div>

        <div class="form-group">
          <label for="codebase">Codebase Path</label>
          <div class="codebase-input-group">
            <input
              id="codebase"
              v-model="formData.parent_codebase_path"
              type="text"
              placeholder="Enter path or select..."
            />
            <select
              v-model="formData.parent_codebase_path"
              class="codebase-select"
            >
              <option value=".">. (current)</option>
              <option value="./apps">./apps</option>
              <option value="./backend">./backend</option>
              <option value="./frontend">./frontend</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label for="prompt">User Request Prompt</label>
          <textarea
            id="prompt"
            v-model="formData.content_user_request_prompt"
            rows="8"
            placeholder="Describe what you want the agents to plan, build, and review..."
            required
          ></textarea>
        </div>

        <div class="form-actions">
          <button type="button" class="btn-cancel" @click="$emit('close')">
            Cancel
          </button>
          <button type="submit" class="btn-submit" :disabled="isSubmitting">
            {{ isSubmitting ? 'Creating...' : 'Create Ticket' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'CreateTicketModal',
  props: {
    sessionInfo: {
      type: Object,
      default: null
    }
  },
  emits: ['close', 'create'],
  setup(props, { emit }) {
    const isSubmitting = ref(false)

    const formData = ref({
      title: '',
      model: 'claude-sonnet-4-20250514',
      parent_codebase_path: '.',
      content_user_request_prompt: ''
    })

    const handleSubmit = async () => {
      if (isSubmitting.value) return

      isSubmitting.value = true

      try {
        await emit('create', { ...formData.value })
        // Reset form
        formData.value = {
          title: '',
          model: 'claude-sonnet-4-20250514',
          parent_codebase_path: '.',
          content_user_request_prompt: ''
        }
      } finally {
        isSubmitting.value = false
      }
    }

    return {
      formData,
      isSubmitting,
      handleSubmit
    }
  }
}
</script>

<style scoped>
* {
  box-sizing: border-box;
}

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
  overflow-y: auto;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #333;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #fff;
}

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

.ticket-form {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #a0a0a0;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 8px;
  font-size: 0.875rem;
  color: #e0e0e0;
  transition: all 0.2s;
  box-sizing: border-box; /* Ensure padding is included in width calculation */
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #3b82f6;
  background: #333;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-group input::placeholder,
.form-group textarea::placeholder {
  color: #666;
}

.form-group select {
  cursor: pointer;
}

.form-group select option {
  background: #2a2a2a;
  color: #e0e0e0;
}

.form-group textarea {
  resize: vertical;
  font-family: inherit;
  line-height: 1.5;
  min-height: 150px;
}

.codebase-input-group {
  display: flex;
  gap: 0.75rem;
}

.codebase-input-group input {
  flex: 2;
  min-width: 0; /* Prevent overflow */
}

.codebase-select {
  flex: 1;
  min-width: 150px;
  cursor: pointer;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  padding-top: 1rem;
  border-top: 1px solid #333;
}

.btn-cancel,
.btn-submit {
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: #2a2a2a;
  color: #888;
  border: 1px solid #444;
}

.btn-cancel:hover {
  background: #333;
  color: #e0e0e0;
  border-color: #555;
}

.btn-submit {
  background: #3b82f6;
  color: white;
  border: none;
}

.btn-submit:hover:not(:disabled) {
  background: #2563eb;
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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