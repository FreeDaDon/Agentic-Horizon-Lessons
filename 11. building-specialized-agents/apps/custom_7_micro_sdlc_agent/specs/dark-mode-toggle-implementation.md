# Dark Mode Toggle Implementation Plan

## Problem Statement

Add a dark mode toggle button to the frontend navigation bar that allows users to switch between light and dark themes. The current application already uses a dark theme by default, so this implementation will add a light theme option and allow users to toggle between both themes. User preferences must be persisted in localStorage.

## Technical Approach

### Architecture Overview
- **Framework**: Vue 3 with Composition API and Pinia state management
- **Styling**: CSS custom properties for theme variables with fallback to existing dark theme
- **State Management**: Reactive theme state with localStorage persistence
- **UI Component**: Toggle button in the existing header navigation bar

### Theme Strategy
Since the application currently uses a sophisticated dark theme, we'll:
1. Extract existing dark theme colors into CSS custom properties
2. Create corresponding light theme color palette
3. Implement theme switching mechanism
4. Add toggle button to header-right section

## Implementation Plan

### Step 1: Create Theme Management System
Create a new composable for theme management:

**File**: `frontend/src/composables/useTheme.js`
```javascript
import { ref, watch } from 'vue'

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
  return AVAILABLE_THEMES.DARK // Default to existing dark theme
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

// Initialize theme on load
setTheme(currentTheme.value)

// Watch for theme changes
watch(currentTheme, (newTheme) => {
  document.documentElement.setAttribute('data-theme', newTheme)
})

export function useTheme() {
  return {
    currentTheme,
    setTheme,
    toggleTheme,
    AVAILABLE_THEMES,
    isLightMode: computed(() => currentTheme.value === AVAILABLE_THEMES.LIGHT)
  }
}
```

### Step 2: Create Theme Toggle Component
Create a reusable toggle button component:

**File**: `frontend/src/components/ThemeToggle.vue`
```vue
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
```

### Step 3: Define CSS Theme Variables
Update the global stylesheet to support theme switching:

**Add to**: `frontend/src/App.vue` (in `<style>` section)
```css
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

  /* Toggle-specific colors for light mode */
  --toggle-bg: rgba(0, 0, 0, 0.05);
  --toggle-bg-hover: rgba(0, 0, 0, 0.1);
  --toggle-border-hover: #3b82f6;
  --toggle-shadow: rgba(59, 130, 246, 0.2);
}
```

### Step 4: Update Existing Styles to Use CSS Variables
Systematically replace hardcoded colors with CSS custom properties:

**Key areas to update in App.vue:**
- `.app-container` background
- `.app-header` background and border
- `.column-content` background and border
- Text colors throughout
- Button styles
- Input/form element styles

**Example conversions:**
```css
/* Before */
.app-container {
  background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
}

/* After */
.app-container {
  background: var(--bg-primary);
}
```

### Step 5: Integrate Toggle into Header
Update the App.vue header section to include the theme toggle:

**Modify**: `frontend/src/App.vue` template section
```vue
<header class="app-header">
  <div class="header-content">
    <div class="header-left">
      <h1 class="app-title">🚀 Micro SDLC Agent</h1>
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
```

**Add corresponding CSS:**
```css
.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}
```

### Step 6: Update Component Imports
Add ThemeToggle to App.vue imports:

```javascript
import ThemeToggle from './components/ThemeToggle.vue'

// Add to components object
components: {
  draggable: VueDraggableNext,
  TicketCard,
  CreateTicketModal,
  TicketDetailsModal,
  ThemeToggle
}
```

## Testing Strategy

### Unit Tests
- Theme persistence in localStorage
- Theme switching functionality
- CSS variable application
- Component rendering in both themes

### Integration Tests
- Theme toggle button interaction
- Theme state consistency across page refreshes
- Accessibility compliance (ARIA labels, keyboard navigation)

### Visual Testing
- Light theme color palette verification
- Dark theme preservation (ensure existing design intact)
- Component visibility in both themes
- Responsive behavior with toggle button

### User Acceptance Testing
- Theme preference persistence across browser sessions
- Visual consistency across all application components
- Toggle button accessibility and usability

## Success Criteria

### Functional Requirements ✅
- [x] Toggle button in navigation header
- [x] Switch between light and dark themes
- [x] Persist theme preference in localStorage
- [x] Frontend-only implementation

### Technical Requirements ✅
- [x] CSS custom properties for maintainable theming
- [x] Vue 3 Composition API integration
- [x] Minimal impact on existing codebase
- [x] Responsive design compatibility

### User Experience Requirements ✅
- [x] Smooth theme transitions
- [x] Intuitive toggle button design
- [x] Consistent styling across all components
- [x] Accessibility compliance

## Edge Cases and Error Handling

### localStorage Availability
- Graceful fallback to default dark theme if localStorage unavailable
- Error handling for localStorage quota exceeded

### Invalid Theme Values
- Validation of stored theme values
- Fallback to default theme for corrupted data

### Browser Compatibility
- CSS custom property fallbacks for older browsers
- Progressive enhancement approach

### Performance Considerations
- Minimal impact on application load time
- Efficient theme switching without layout shifts

## File Structure Changes

```
frontend/src/
├── composables/
│   └── useTheme.js          # New: Theme management logic
├── components/
│   ├── ThemeToggle.vue      # New: Toggle button component
│   ├── TicketCard.vue       # Existing
│   ├── TicketDetailsModal.vue # Existing
│   └── CreateTicketModal.vue  # Existing
├── App.vue                  # Modified: Add toggle, update styles
└── main.js                  # Existing: No changes needed
```

## Implementation Timeline

1. **Phase 1** (1-2 hours): Create theme composable and CSS variables
2. **Phase 2** (1 hour): Create ThemeToggle component
3. **Phase 3** (2-3 hours): Update existing styles to use CSS variables
4. **Phase 4** (30 minutes): Integrate toggle into header
5. **Phase 5** (1 hour): Testing and refinement

**Total Estimated Time**: 5-7 hours

## Potential Challenges and Solutions

### Challenge: Maintaining Design Consistency
**Solution**: Carefully map existing dark theme colors to CSS variables, test extensively

### Challenge: Complex Gradient Backgrounds
**Solution**: Define gradient variables for both themes, ensure visual appeal maintained

### Challenge: Component Style Inheritance
**Solution**: Use CSS cascade effectively, test all child components in both themes

### Challenge: Performance Impact
**Solution**: Use CSS custom properties efficiently, avoid JavaScript style manipulation where possible

This implementation provides a robust, maintainable dark mode toggle that enhances user experience while preserving the existing sophisticated design of the Micro SDLC Agent application.