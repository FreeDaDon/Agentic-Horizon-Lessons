# Sync Header Title with HTML Title Block

## Problem Statement

Currently, the application has a mismatch between the header title displayed in the Vue.js component and the HTML `<title>` tag in the document head. The header shows "🚀 Plan, Build, Review and Ship Agents" while the HTML title is "Micro SDLC - Plan, Build, Review". This inconsistency creates confusion for users and affects SEO/browser tab display.

**Current State:**
- HTML title: `Micro SDLC - Plan, Build, Review` (frontend/index.html:7)
- Header title: `🚀 Plan, Build, Review and Ship Agents` (frontend/src/App.vue:6)

## Codebase Analysis

### Current Architecture
- **Vue.js 3** with Composition API
- **Single Page Application** structure
- **Pinia** for state management
- **Vite** build system
- **No Vue Router** - appears to be a single-page dashboard

### Key Files Identified
1. **frontend/index.html** - Contains the HTML `<title>` tag
2. **frontend/src/App.vue** - Contains the header with `.app-title` class
3. **frontend/src/main.js** - Application entry point

### Current Title Implementations
- **Static HTML Title**: Set in `index.html` at line 7
- **Header Title**: Hardcoded in App.vue template at line 6 in `.app-title` h1 element
- **No Dynamic Title Management**: No existing `document.title` manipulation found

### Styling Context
The header title uses these CSS classes:
- `.app-title` - Main styling with font-size: 1.5rem, font-weight: 600
- Color managed through CSS custom properties (`--text-primary`)
- Responsive design considerations for mobile devices

## Technical Approach

### Solution Strategy
Implement a **single source of truth** approach where:
1. Define the application title in one centralized location
2. Use this title for both the HTML `<title>` and header display
3. Support dynamic title updates if needed in the future

### Implementation Options

#### Option 1: Reactive Title Management (Recommended)
Create a composable that manages both HTML title and header title synchronization:

```javascript
// composables/useAppTitle.js
import { ref, watch } from 'vue'

const appTitle = ref('Micro SDLC - Plan, Build, Review and Ship Agents')

export function useAppTitle() {
  // Update document title when appTitle changes
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
```

#### Option 2: Simple Static Synchronization
Direct alignment of both titles without reactive management.

## Implementation Guide

### Step 1: Create Title Composable
Create `frontend/src/composables/useAppTitle.js`:

```javascript
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
```

### Step 2: Update App.vue
Modify `frontend/src/App.vue` to use the composable:

```vue
<template>
  <div class="app-container">
    <header class="app-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="app-title">{{ appTitle }}</h1>
          <!-- ... rest of header content ... -->
        </div>
        <!-- ... rest of header ... -->
      </div>
    </header>
    <!-- ... rest of template ... -->
  </div>
</template>

<script>
import { useAppTitle } from './composables/useAppTitle'
// ... other imports ...

export default {
  name: 'App',
  setup() {
    const { appTitle } = useAppTitle()

    // ... existing setup code ...

    return {
      appTitle,
      // ... existing returns ...
    }
  }
}
</script>
```

### Step 3: Update HTML Title
Update `frontend/index.html` to match the application title:

```html
<title>Micro SDLC - Plan, Build, Review and Ship Agents</title>
```

### Step 4: Initialize Title on App Mount
Ensure the title is set when the application loads by calling the composable in the setup lifecycle.

## Testing Strategy

### Manual Testing
1. **Browser Tab Title**: Verify the browser tab shows the correct title
2. **Header Display**: Confirm the header shows the same title
3. **Page Refresh**: Ensure title persistence across page reloads
4. **Theme Changes**: Verify title styling works with dark/light themes

### Test Cases
- ✅ HTML title matches header title exactly
- ✅ Title displays correctly on initial load
- ✅ Title updates synchronously if changed dynamically
- ✅ Mobile responsive layout maintains title visibility
- ✅ Theme switching preserves title styling

### Browser Compatibility
- Modern browsers support `document.title` manipulation
- Vue 3 reactivity system ensures cross-browser compatibility
- No additional dependencies required

## Edge Cases & Considerations

### Potential Issues
1. **SEO Impact**: Changing title affects search engine indexing
2. **Character Encoding**: Emoji in title may affect some older browsers
3. **Length Limits**: Browser tabs truncate long titles

### Future Enhancements
1. **Dynamic Titles**: Support for page-specific titles if routing is added
2. **Title Templates**: Template-based title generation (e.g., "Page Name - App Name")
3. **Internationalization**: Multi-language title support

### Rollback Plan
If issues arise:
1. Revert `App.vue` to hardcoded title
2. Keep HTML title as original
3. Remove composable file

## Success Criteria

### Primary Goals
- ✅ Header title and HTML title are identical
- ✅ Single source of truth for application title
- ✅ No visual or functional regressions

### Technical Requirements
- ✅ Composable follows Vue 3 best practices
- ✅ Reactivity system properly implemented
- ✅ No performance impact on application
- ✅ Maintains existing styling and responsive behavior

### User Experience
- ✅ Consistent branding across browser tab and application header
- ✅ Professional appearance maintained
- ✅ No breaking changes to existing functionality

## Implementation Notes

### Code Quality
- Use TypeScript-style JSDoc comments for better development experience
- Follow existing Vue 3 Composition API patterns
- Maintain consistency with existing composables structure

### Performance
- Minimal overhead from reactive title management
- No additional API calls or external dependencies
- Efficient DOM updates through Vue's reactivity system

### Maintainability
- Centralized title management makes future updates simple
- Clear separation of concerns with composable pattern
- Easy to extend for future requirements