import { ref, computed } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import DOMPurify from 'dompurify'

const defaultMarkdown = `# Welcome to Markdown Preview

This is a **live preview** of your markdown content.

## Features

- Real-time preview
- Syntax highlighting for code
- Copy HTML to clipboard
- Resizable split pane

## Code Examples

\`\`\`typescript
function greet(name: string): string {
  return \`Hello, \${name}!\`
}

console.log(greet('World'))
\`\`\`

\`\`\`python
def greet(name: str) -> str:
    return f"Hello, {name}!"

print(greet("World"))
\`\`\`

## Tables

| Feature | Status |
|---------|--------|
| Live Preview | Done |
| Syntax Highlighting | Done |
| Copy HTML | Done |

## Links and Images

[Visit GitHub](https://github.com)

---

> Blockquotes are supported too!

Happy writing! 🚀
`

export function useMarkdown() {
  const markdown = ref(defaultMarkdown)

  // Configure marked with syntax highlighting
  marked.setOptions({
    gfm: true,
    breaks: true
  })

  // Custom renderer for syntax highlighting
  const renderer = new marked.Renderer()
  renderer.code = ({ text, lang }: { text: string; lang?: string }) => {
    const language = lang && hljs.getLanguage(lang) ? lang : 'plaintext'
    const highlighted = hljs.highlight(text, { language }).value
    return `<pre><code class="hljs language-${language}">${highlighted}</code></pre>`
  }

  marked.use({ renderer })

  const renderedHtml = computed(() => {
    const raw = marked.parse(markdown.value) as string
    return DOMPurify.sanitize(raw)
  })

  const setMarkdown = (value: string) => {
    markdown.value = value
  }

  return {
    markdown,
    renderedHtml,
    setMarkdown
  }
}
