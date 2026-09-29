# Plan: Fix TypeError in Timer Panel Composition

## Task Description
Fix the TypeError occurring at line 149 in `apps/pomodoro_timer/timer.py` where `progress.__rich__()` returns a Group object that cannot be concatenated with a string. The error message is: `TypeError: can only concatenate str (not 'Group') to str`.

The issue occurs in the `_create_timer_panel()` method when attempting to combine timer status text with a Rich Progress widget using string concatenation, which is not supported for Rich renderable objects.

## Objective
Properly compose the Rich Panel containing timer information and the Progress widget by using Rich's Group class to combine multiple renderables instead of string concatenation. This will resolve the TypeError and ensure the timer display works correctly with both text content and the progress bar.

## Problem Statement
The current implementation at timer.py:149 attempts to concatenate a string with a Rich renderable object:

```python
return Panel(content + "\n" + progress.__rich__(), expand=True)
```

This fails because:
1. `content` is a string with Rich markup
2. `progress.__rich__()` returns a Rich Group object (renderable)
3. Python's `+` operator cannot concatenate string and Group types
4. Rich Panel can accept either a string or a renderable, but the concatenation happens before Panel receives the content

## Solution Approach
Use Rich's `Group` class to compose multiple renderables together. The Group class is specifically designed to stack multiple Rich renderables vertically. We will:

1. Import the `Group` class from `rich.console`
2. Convert the text content to a Rich `Text` object (or keep as string, as Group accepts both)
3. Create a Group containing the text content and the progress bar renderable
4. Pass the Group object to the Panel

This approach is the standard pattern for composing multiple Rich elements and aligns with Rich library best practices.

## Relevant Files
Use these files to complete the task:

- **timer.py** (line 149) - Contains the `_create_timer_panel()` method that needs to be fixed
  - Import statement needs to be updated to include `Group`
  - The `_create_timer_panel()` method needs to be modified to use Group instead of string concatenation

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update Import Statement
- Add `Group` to the imports from `rich.console`
- Verify the import is on line 7 where other Rich console imports are located
- The import line should change from:
  ```python
  from rich.console import Console
  ```
  to:
  ```python
  from rich.console import Console, Group
  ```

### 2. Modify `_create_timer_panel()` Method
- Locate the `_create_timer_panel()` method (currently at line 129)
- Replace the return statement at line 149
- Current code:
  ```python
  return Panel(content + "\n" + progress.__rich__(), expand=True)
  ```
- New code using Group:
  ```python
  return Panel(Group(content, progress), expand=True)
  ```
- Note: Group will automatically add proper spacing between elements
- The `content` string will be automatically rendered by Rich
- The `progress` object's `__rich__()` method will be called automatically by Rich when rendering

### 3. Test the Fix
- Run the timer application to verify the panel renders correctly
- Confirm that:
  - The timer information displays properly
  - The progress bar renders below the timer text
  - No TypeError is raised
  - The panel expands correctly with `expand=True`
  - The pause/resume status changes are reflected correctly

### 4. Verify Code Compilation
- Ensure the Python file compiles without syntax errors
- Run static type checking if available
- Confirm all imports are correctly structured

## Testing Strategy
1. **Manual Testing**
   - Run `uv run python -m main start 1` to start a 1-minute timer
   - Observe that the timer panel displays without errors
   - Verify that the progress bar updates smoothly
   - Confirm that the timer completes successfully

2. **Edge Cases**
   - Test with different duration values (1, 5, 25 minutes)
   - Verify pause status display (if pause functionality is implemented)
   - Ensure cancelled sessions also display correctly before cancellation

## Acceptance Criteria
- [ ] No TypeError occurs when the timer runs
- [ ] The timer panel displays with proper formatting
- [ ] Timer information text appears at the top of the panel
- [ ] Progress bar appears below the timer information
- [ ] The panel expands to full width as expected
- [ ] The code compiles without syntax errors
- [ ] Rich library renderables are properly composed using Group

## Validation Commands
Execute these commands to validate the task is complete:

- `uv run python -m py_compile timer.py` - Verify the file compiles without syntax errors
- `uv run python -m main start 1` - Start a 1-minute timer and verify no TypeError occurs
- `grep -n "from rich.console import" timer.py` - Verify Group is imported
- `grep -n "Panel(Group" timer.py` - Verify Group is used in Panel creation

## Notes
- The Rich library's `Group` class automatically handles vertical stacking of renderables
- No need to manually add newlines between Group elements; Rich handles spacing
- The `progress` parameter should be passed directly to Group, not `progress.__rich__()`
- Group accepts both strings with Rich markup and Rich renderable objects
- This pattern is recommended in the Rich documentation for composing multiple renderables
- No additional dependencies are required; Group is part of the core Rich library
