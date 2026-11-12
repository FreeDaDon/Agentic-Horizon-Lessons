// Markdown to sanitized HTML, safe to bind with v-html.
import { marked } from 'marked';
import DOMPurify from 'dompurify';

export function renderMarkdown(markdown: string): string {
  if (!markdown) return '';
  const rawHtml = marked.parse(markdown, { async: false, breaks: true, gfm: true });
  return DOMPurify.sanitize(rawHtml);
}
