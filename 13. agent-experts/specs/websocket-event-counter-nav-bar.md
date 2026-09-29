# Plan: WebSocket Event Counter in Nav Bar

## Task Description
Add a session-based counter to the application nav bar (header) that displays the total number of WebSocket events received during the current session. The counter should:
- Track ALL WebSocket messages received from the backend (every message type)
- Display prominently in the header stats section alongside existing metrics (Active, Running, Logs, Cost)
- Reset to 0 when the WebSocket connection is established or re-established
- Reset to 0 when the page is reloaded (new session)
- Update in real-time as events are received

## Objective
Provide visibility into WebSocket activity by displaying a live counter of all events received during the current session. This helps users understand the volume of real-time communication and provides insight into system activity levels.

## Problem Statement
Currently, users have no way to see how many WebSocket events have been received during their session. While the "Logs" counter shows event stream entries (`eventStreamEntries.length`), it doesn't reflect ALL WebSocket messages. Some WebSocket events like `connection_established`, `chat_typing`, and `heartbeat` don't create event stream entries. A dedicated WebSocket event counter provides transparency into the real-time communication layer and helps with debugging connection issues or understanding system activity.

## Solution Approach
Implement a counter at the WebSocket message reception layer that increments for every message received, regardless of type. The architecture will:

1. **Add Callback to chatService**: Extend the `WebSocketCallbacks` interface with an `onMessageReceived` callback that fires for EVERY message before routing
2. **Store Counter in Pinia Store**: Add a reactive `websocketEventCount` ref to `orchestratorStore.ts` that initializes at 0
3. **Increment via Callback**: Pass an increment callback from the store to chatService that fires on every message
4. **Reset on Connect/Disconnect**: Clear the counter when WebSocket connects (new session) or disconnects
5. **Expose via Composable**: Add the counter to `useHeaderBar.ts` for easy access by the header component
6. **Display in Header**: Add a new stat pill in `AppHeader.vue` next to the existing stats

This approach follows WebSocket best practices:
- Single source of truth (chatService.ts onmessage handler)
- Decoupled design (chatService doesn't need to know about store internals)
- Follows existing callback pattern (matches onChatStream, onTyping, etc.)
- Session-based (resets on connect, not persisted)

## Relevant Files

### Files to Modify
- **apps/orchestrator_3_stream/frontend/src/services/chatService.ts** (189 lines)
  - Add `onMessageReceived` callback to `WebSocketCallbacks` interface (line 53)
  - Invoke callback in `ws.onmessage` handler before message parsing (line 87)
  - This ensures ALL messages are counted at the source

- **apps/orchestrator_3_stream/frontend/src/stores/orchestratorStore.ts** (1117 lines)
  - Add `websocketEventCount` ref to state section (around line 74)
  - Create `incrementWebSocketEventCount()` action function
  - Reset counter in `connectWebSocket()` on successful connection (line 376)
  - Reset counter in `disconnectWebSocket()` (line 390)
  - Pass `onMessageReceived` callback when calling `chatService.connectWebSocket()` (line 329)
  - Export counter in return statement (line 1047)

- **apps/orchestrator_3_stream/frontend/src/composables/useHeaderBar.ts** (217 lines)
  - Add computed property `websocketEventCount` that returns `store.websocketEventCount`
  - Export in return statement (line 185)

- **apps/orchestrator_3_stream/frontend/src/components/AppHeader.vue** (256 lines)
  - Add new stat pill after "Logs" stat (around line 30)
  - Display WebSocket event count using `headerBar.websocketEventCount`

## Implementation Phases

### Phase 1: Foundation (Service Layer)
Extend the chatService WebSocket callbacks to support message counting at the source. This establishes the data capture point.

### Phase 2: Core Implementation (State Management)
Add counter state to the store and wire up the increment/reset logic through the callback mechanism.

### Phase 3: Integration & Polish (UI Display)
Expose the counter through the composable and display it in the header component with consistent styling.

## Step by Step Tasks

### 1. Add Message Received Callback to WebSocket Interface
- Open `apps/orchestrator_3_stream/frontend/src/services/chatService.ts`
- Find the `WebSocketCallbacks` interface (line 53)
- Add new optional callback as the FIRST property:
  ```typescript
  export interface WebSocketCallbacks {
    /** Called for every WebSocket message received (before routing) */
    onMessageReceived?: () => void
    onChatStream: (chunk: string, isComplete: boolean) => void
    // ... rest of callbacks
  }
  ```

### 2. Invoke Counter Callback in WebSocket Handler
- In `chatService.ts`, find the `ws.onmessage` handler (line 87)
- Add callback invocation as the FIRST operation (before try block):
  ```typescript
  ws.onmessage = (event) => {
    // Increment WebSocket event counter for ALL messages (before any processing)
    callbacks.onMessageReceived?.()

    try {
      const message = JSON.parse(event.data)
      // ... existing routing code
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error)
    }
  }
  ```
- This placement ensures we count ALL messages, even if JSON parsing fails

### 3. Add Counter State to Orchestrator Store
- Open `apps/orchestrator_3_stream/frontend/src/stores/orchestratorStore.ts`
- In the STATE section (line 74, near `isConnected`), add a new ref:
  ```typescript
  // WebSocket
  const isConnected = ref(false)
  let wsConnection: WebSocket | null = null

  // WebSocket session event counter
  const websocketEventCount = ref<number>(0)
  ```

### 4. Create Counter Increment Action
- In `orchestratorStore.ts`, in the ACTIONS - WEBSOCKET section (after line 310), add:
  ```typescript
  function incrementWebSocketEventCount() {
    websocketEventCount.value += 1
  }
  ```

### 5. Reset Counter on WebSocket Connect
- In `orchestratorStore.ts`, find the `connectWebSocket()` function (line 313)
- In the `onConnected` callback (line 376), reset the counter:
  ```typescript
  onConnected: () => {
    isConnected.value = true
    websocketEventCount.value = 0  // Reset counter for new session
    console.log('WebSocket connected - event counter reset')
  },
  ```

### 6. Reset Counter on WebSocket Disconnect
- In `orchestratorStore.ts`, find the `disconnectWebSocket()` function (line 390)
- Add reset after setting `isConnected.value = false`:
  ```typescript
  function disconnectWebSocket() {
    if (wsConnection) {
      chatService.disconnect(wsConnection)
      wsConnection = null
      isConnected.value = false
    }

    // Reset counter on disconnect
    websocketEventCount.value = 0

    // CRITICAL: Cleanup pulse animations to prevent memory leaks
    agentPulse.clearAllPulses()
    // ... rest of cleanup
  }
  ```

### 7. Pass Counter Callback in WebSocket Setup
- In `orchestratorStore.ts`, find where `chatService.connectWebSocket()` is called (line 329)
- Add the `onMessageReceived` callback as the FIRST callback:
  ```typescript
  wsConnection = chatService.connectWebSocket(wsUrl, {
    onMessageReceived: () => {
      incrementWebSocketEventCount()
    },
    onChatStream: handleChatStream,
    onTyping: handleTyping,
    // ... rest of callbacks
  })
  ```

### 8. Export Counter in Store API
- In `orchestratorStore.ts`, find the return statement (line 1047)
- Add `websocketEventCount` to the State section:
  ```typescript
  return {
    // State
    agents,
    selectedAgentId,
    orchestratorAgentId,
    orchestratorAgent,
    eventStreamEntries,
    eventStreamFilter,
    autoScroll,
    fileTrackingEvents,
    chatMessages,
    chatWidth,
    isTyping,
    isConnected,
    commandInputVisible,
    autocompleteItems,
    autocompleteLoading,
    autocompleteError,
    websocketEventCount,  // ADD THIS LINE
    // ... rest of exports
  ```

### 9. Add Counter to Header Bar Composable
- Open `apps/orchestrator_3_stream/frontend/src/composables/useHeaderBar.ts`
- After the `logCount` computed property (around line 98), add:
  ```typescript
  /**
   * Total number of WebSocket events received in current session
   * Counts ALL WebSocket messages, not just event stream entries
   */
  const websocketEventCount = computed(() => {
    return store.websocketEventCount
  })
  ```

### 10. Export Counter in Composable
- In `useHeaderBar.ts`, find the return statement (line 185)
- Add `websocketEventCount` after `logCount`:
  ```typescript
  return {
    // Raw computed values
    orchestratorCost,
    totalAgentCost,
    totalCombinedCost,
    activeAgentCount,
    runningAgentCount,
    logCount,
    websocketEventCount,  // ADD THIS LINE
    // ... rest of exports
  ```

### 11. Add Counter Display to Header Component
- Open `apps/orchestrator_3_stream/frontend/src/components/AppHeader.vue`
- Find the `.header-stats` section in the template (line 17)
- After the "Logs" stat pill (line 26-29), add:
  ```vue
  <div class="stat-item stat-pill">
    <span class="stat-label">WS Events:</span>
    <span class="stat-value">{{ headerBar.websocketEventCount }}</span>
  </div>
  ```
- The complete stats section will be:
  ```vue
  <div class="header-stats">
    <div class="stat-item stat-pill">
      <span class="stat-label">Active:</span>
      <span class="stat-value">{{ headerBar.activeAgentCount }}</span>
    </div>
    <div class="stat-item stat-pill">
      <span class="stat-label">Running:</span>
      <span class="stat-value">{{ headerBar.runningAgentCount }}</span>
    </div>
    <div class="stat-item stat-pill">
      <span class="stat-label">Logs:</span>
      <span class="stat-value">{{ headerBar.logCount }}</span>
    </div>
    <div class="stat-item stat-pill">
      <span class="stat-label">WS Events:</span>
      <span class="stat-value">{{ headerBar.websocketEventCount }}</span>
    </div>
    <div class="stat-item stat-pill">
      <span class="stat-label">Cost:</span>
      <span class="stat-value">${{ headerBar.formattedCost }}</span>
    </div>
  </div>
  ```

### 12. Test Counter Implementation
- Start the backend server: `cd apps/orchestrator_3_stream && ./start_be.sh`
- Start the frontend dev server: `cd apps/orchestrator_3_stream && ./start_fe.sh`
- Open the application in a browser with DevTools open
- **Test Initial State**: Verify counter shows 0 after page load (it will increment to 1 after `connection_established` event)
- **Test Increment**: Send a chat message and observe counter incrementing for each WebSocket event (typing indicator, stream chunks, completion, etc.)
- **Test Reset**: Refresh the page and verify counter resets to 0
- **Test Comparison**: Note that "WS Events" will be higher than "Logs" because it counts ALL messages
- **Test Console**: Check for any errors in browser console

### 13. Verify WebSocket Event Types Captured
According to the WebSocket expertise file, these event types should ALL increment the counter:
- `connection_established` - Initial connection confirmation
- `chat_stream` - Streaming chat chunks
- `chat_typing` - Typing indicator updates
- `orchestrator_chat` - Complete chat messages
- `thinking_block` - AI thinking process streams
- `tool_use_block` - Tool usage events
- `agent_log` - Agent activity logs
- `agent_created`, `agent_updated`, `agent_deleted` - Agent lifecycle events
- `agent_status_changed` - Agent status updates
- `agent_summary_update` - Agent summary refreshes
- `orchestrator_updated` - Orchestrator state updates (cost, tokens)
- `autocomplete_started`, `autocomplete_completed` - Autocomplete events
- `error` - Error notifications
- `system_log` - System logging
- `heartbeat` - Keep-alive signals (if implemented)

Test by triggering different actions and verifying the counter increments for each event type.

### 14. Validate Responsive Layout
- Test the header at different viewport widths (1400px, 1200px, 1024px, 650px)
- Verify the new stat pill doesn't cause overflow or layout issues
- The existing responsive CSS should handle the new stat pill automatically
- If issues arise, consider hiding less critical stats on smaller screens using existing media queries

## Testing Strategy

### Manual Testing
1. **Initialization Test**
   - Load the application
   - Verify "WS Events: 0" appears (will become "WS Events: 1" after connection)
   - Check that counter is visible and styled correctly

2. **Increment Test**
   - Send a chat message
   - Observe counter incrementing for multiple events (typing indicator, stream chunks, completion)
   - Verify increment happens immediately (no lag)

3. **Reset Test**
   - Note the current counter value
   - Refresh the browser page
   - Verify counter resets to 0

4. **Comparison Test**
   - Compare "WS Events" vs "Logs" counter
   - "WS Events" should be higher because it counts ALL messages including typing indicators, connection events, etc.
   - "Logs" only counts actual event stream entries

5. **Multiple Event Types Test**
   - Create an agent (should trigger multiple events)
   - Check agent logs, thinking blocks, tool usage
   - Verify all events increment the counter

### Console Verification
- Open browser DevTools Console
- Monitor for any errors related to WebSocket or counter
- Optionally add `console.log` in `incrementWebSocketEventCount()` to verify it's being called

### Network Tab Verification
- Open browser DevTools Network tab
- Filter by WS (WebSocket)
- Manually count the number of messages in the WebSocket connection
- Compare to the "WS Events" counter - they should match

### Edge Cases
- **Rapid Events**: Send multiple messages quickly, verify counter keeps up
- **Connection Errors**: Test with backend offline, verify no counter-related errors
- **Long Sessions**: Let application run with many events, verify counter doesn't overflow
- **Multiple Tabs**: Open multiple tabs, each should have independent counters

## Acceptance Criteria

1. ✅ A new "WS Events" stat pill appears in the header between "Logs" and "Cost"
2. ✅ The counter displays 0 when the application first loads
3. ✅ The counter increments by 1 for every WebSocket message received (visible in Network tab)
4. ✅ The counter includes ALL message types (connection_established, chat_stream, agent_log, thinking_block, tool_use_block, typing indicators, etc.)
5. ✅ The counter resets to 0 when the WebSocket connection is established (new session)
6. ✅ The counter resets to 0 when the page is refreshed
7. ✅ The counter resets to 0 when WebSocket disconnects
8. ✅ The stat pill styling matches existing stat pills (flat gray badge style with hover effect)
9. ✅ The counter updates in real-time without lag or flicker
10. ✅ No console errors related to the counter implementation
11. ✅ The header layout remains responsive on smaller screens (650px, 1024px, 1200px)
12. ✅ The counter shows a higher number than "Logs" (because it counts more events)

## Validation Commands

Execute these commands to validate the task is complete:

```bash
# Type check TypeScript code
cd apps/orchestrator_3_stream/frontend && npm run type-check

# Build the application
cd apps/orchestrator_3_stream/frontend && npm run build

# Start dev server for manual testing
cd apps/orchestrator_3_stream/frontend && npm run dev

# Start backend server (in another terminal)
cd apps/orchestrator_3_stream && ./start_be.sh
```

### Manual Validation Checklist
- [ ] Open application in browser
- [ ] Verify "WS Events" stat pill is visible in header
- [ ] Send a chat message
- [ ] Verify counter increments multiple times (for typing, stream, completion events)
- [ ] Open DevTools Network tab, filter by WS
- [ ] Compare message count in Network tab to "WS Events" counter
- [ ] Refresh page and verify counter resets to 0
- [ ] Check browser console for any errors
- [ ] Test responsive layout at 1400px, 1024px, 650px widths

## Notes

### Design Considerations
- **Label Choice**: "WS Events:" is concise and fits the existing stat pill pattern. Alternative labels: "Events:", "Messages:", "WS Msgs:", "Received:"
- **Placement**: Counter is placed after "Logs" to maintain logical grouping (agent stats → event metrics → cost)
- **Color Scheme**: Uses existing stat pill styling (no custom colors needed)

### WebSocket Architecture Context
Based on the WebSocket expertise file (`.claude/commands/experts/websocket/expertise.yaml`):
- **Centralized Management**: WebSocket is managed by `WebSocketManager` class in `websocket_manager.py`
- **Single Endpoint**: All events flow through `/ws` endpoint
- **Event Bus Pattern**: WebSocket serves as a centralized event bus for real-time communication
- **Deep Integration**: Hooks into Claude SDK execution events (PreToolUse, PostToolUse, Stop, etc.)
- **Write-Through Pattern**: Events are persisted to database before broadcast

### Why This is Useful
- **Debugging**: Quickly see if WebSocket messages are being sent but not processed
- **Performance Monitoring**: Understand the volume of real-time activity
- **Connection Health**: A frozen counter indicates connection issues
- **Comparison Insight**: Comparing "WS Events" vs "Logs" reveals how many messages don't create log entries

### Implementation Details
- **Callback Pattern**: Follows the existing WebSocket callback architecture used by other handlers
- **Decoupled Design**: chatService.ts doesn't need to import or know about the store
- **Single Source of Truth**: Counter increments in ONE place (onmessage handler) before any routing
- **Session-Only**: Counter lives in Vue ref (not persisted), automatically resets on page reload
- **Zero Backend Changes**: Purely frontend feature, no backend modifications required
- **Negligible Performance Impact**: Simple integer increment has no measurable overhead

### Event Type Breakdown
The counter will increment for these WebSocket event types (from expertise.yaml):
- **Connection**: connection_established
- **Chat**: chat_stream, chat_typing, orchestrator_chat
- **Agent Management**: agent_created, agent_updated, agent_deleted, agent_status_changed
- **Agent Activity**: agent_log, agent_summary_update
- **Analysis Blocks**: thinking_block, tool_use_block
- **Orchestrator**: orchestrator_updated
- **System**: system_log, error, heartbeat
- **Autocomplete**: autocomplete_started, autocomplete_completed

### Future Enhancements (Out of Scope)
- Add tooltip showing event breakdown by type (e.g., "45 chat, 23 logs, 12 thinking")
- Add color coding based on event rate (green: healthy, yellow: high, red: connection issues)
- Add sparkline graph showing event rate over time
- Add ability to click counter to view detailed event log
- Track events per minute or average event rate
- Add manual reset button
- Persist counter to localStorage for cross-refresh persistence (if desired)
- Add filters to count only specific event types
