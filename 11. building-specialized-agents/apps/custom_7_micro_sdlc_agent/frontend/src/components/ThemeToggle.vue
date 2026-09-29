<template>
  <button
    @click="toggleTheme"
    class="theme-toggle"
    :title="isLightMode ? 'Switch to Dark Mode' : 'Switch to Light Mode'"
    aria-label="Toggle theme"
  >
    <span class="toggle-icon">
      {{ isLightMode ? '🌙' : '☀️' }}
    </span>
  </button>
</template>

<script>
import { useTheme } from '../composables/useTheme'

export default {
  name: 'ThemeToggle',
  setup() {
    const { toggleTheme, isLightMode } = useTheme()

    return {
      toggleTheme,
      isLightMode
    }
  }
}
</script>

<style scoped>
.theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--toggle-bg);
  cursor: pointer;
  transition: all 0.3s ease;
  padding: 0;
}

.theme-toggle:hover {
  background: var(--toggle-bg-hover);
  border-color: var(--toggle-border-hover);
  box-shadow: 0 2px 8px var(--toggle-shadow);
}

.toggle-icon {
  font-size: 18px;
  transition: transform 0.3s ease;
}

.theme-toggle:hover .toggle-icon {
  transform: scale(1.1);
}
</style>