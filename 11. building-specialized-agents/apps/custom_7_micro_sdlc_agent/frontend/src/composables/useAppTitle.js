import { ref, watch, readonly } from 'vue'

const appTitle = ref('Micro SDLC - Plan, Build, Review and Ship Agents')

export function useAppTitle() {
  // Sync document.title with appTitle
  watch(appTitle, (newTitle) => {
    document.title = newTitle
  }, { immediate: true })

  const setTitle = (newTitle) => {
    appTitle.value = newTitle
  }

  return {
    appTitle: readonly(appTitle),
    setTitle
  }
}