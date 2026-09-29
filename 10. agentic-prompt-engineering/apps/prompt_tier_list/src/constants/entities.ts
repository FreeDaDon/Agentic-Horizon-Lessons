export const GRADABLE_ENTITIES = [
  '# Title',
  '## High Level Prompt',
  '## Metadata',
  '## Purpose',
  '## Variables',
  '## Instructions',
  '## Relevant Files',
  '## Codebase Structure',
  '## Workflow',
  '## Expertise',
  '## Template',
  '## Examples',
  '## Report',
  'high_level_prompt.md',
  'workflow_prompt.md',
  'higher_order_prompt.md',
  'control_flow_prompt.md',
  'delegate_prompt.md',
  'template_metaprompt.md',
  'self_improving_prompt.md'
] as const;

export type GradableEntity = typeof GRADABLE_ENTITIES[number];