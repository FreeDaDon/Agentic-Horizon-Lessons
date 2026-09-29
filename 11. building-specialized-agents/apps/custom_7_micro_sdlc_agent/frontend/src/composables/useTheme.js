import { ref, watch, computed } from 'vue'

const THEME_STORAGE_KEY = 'micro-sdlc-theme'
const AVAILABLE_THEMES = {
  DARK: 'dark',
  LIGHT: 'light'
}

const currentTheme = ref(getInitialTheme())

function getInitialTheme() {
  const stored = localStorage.getItem(THEME_STORAGE_KEY)
  if (stored && Object.values(AVAILABLE_THEMES).includes(stored)) {
    return stored
  }
  return AVAILABLE_THEMES.DARK // Default to dark theme
}

function setTheme(theme) {
  if (!Object.values(AVAILABLE_THEMES).includes(theme)) {
    console.warn(`Invalid theme: ${theme}`)
    return
  }

  currentTheme.value = theme
  document.documentElement.setAttribute('data-theme', theme)
  localStorage.setItem(THEME_STORAGE_KEY, theme)
}

function toggleTheme() {
  const newTheme = currentTheme.value === AVAILABLE_THEMES.DARK
    ? AVAILABLE_THEMES.LIGHT
    : AVAILABLE_THEMES.DARK
  setTheme(newTheme)
}

// Watch for theme changes
watch(currentTheme, (newTheme) => {
  document.documentElement.setAttribute('data-theme', newTheme)
})

// Initialize theme when DOM is ready
function initializeTheme() {
  setTheme(currentTheme.value)
}

// Auto-initialize if DOM is ready
if (typeof document !== 'undefined' && document.documentElement) {
  initializeTheme()
}

export function useTheme() {
  return {
    currentTheme,
    setTheme,
    toggleTheme,
    initializeTheme,
    AVAILABLE_THEMES,
    isLightMode: computed(() => currentTheme.value === AVAILABLE_THEMES.LIGHT)
  }
}