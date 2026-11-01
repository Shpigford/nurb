import Markdown, { type Components } from "react-markdown"
import clsx from "clsx"
import { ASSISTANT_MARKDOWN_DISALLOWED_ELEMENTS } from "./assistantMarkdownPolicy"

// Assistant replies are markdown (the intake model bolds its questions and
// numbers them). react-markdown escapes raw HTML by default, so model output
// cannot inject markup; skipHtml drops it entirely instead of showing tags.
// `streaming` draws the caret after the last rendered node (see .md-streaming
// in tokens.css); a sibling span would land below the paragraph or list that
// markdown closes.
// Built once: a components map rebuilt on every render makes react-markdown
// replace its nodes, which detaches text a test or a screen reader is holding.
const COMPONENTS: Components = {
  p: ({ node: _node, ...props }) => <p className="text-pretty [&:not(:first-child)]:mt-2" {...props} />,
  ol: ({ node: _node, ...props }) => (
    <ol className="mt-2 list-decimal space-y-2 pl-7 marker:font-mono marker:text-[11px] marker:text-accent-ink" {...props} />
  ),
  ul: ({ node: _node, ...props }) => <ul className="mt-2 list-disc space-y-2 pl-7 marker:text-faint" {...props} />,
  strong: ({ node: _node, ...props }) => <strong className="font-semibold text-ink" {...props} />,
  // A fenced block is a <pre> around a <code>; the pre resets the pill so the
  // block reads as one surface. The className merge keeps react-markdown's
  // language-* class, which it sets on fenced code only.
  pre: ({ node: _node, ...props }) => (
    <pre className="mt-2 overflow-x-auto rounded-[6px] bg-raised px-2.5 py-2 font-mono text-[11.5px] leading-[17px] text-ink-soft [&_code]:rounded-none [&_code]:bg-transparent [&_code]:px-0 [&_code]:text-[inherit]" {...props} />
  ),
  code: ({ node: _node, className, ...props }) => (
    <code className={clsx("rounded-[3px] bg-raised px-1 font-mono text-[0.85em] text-ink", className)} {...props} />
  ),
  a: ({ node: _node, ...props }) => <a className="underline decoration-1 underline-offset-[3px] hover:text-accent-ink" target="_blank" rel="noreferrer" {...props} />,
}

export default function AssistantMarkdown({ content, streaming = false }: { content: string; streaming?: boolean }) {
  return (
    <div className={clsx(streaming && "md-streaming")}>
      <Markdown
        skipHtml
        disallowedElements={ASSISTANT_MARKDOWN_DISALLOWED_ELEMENTS}
        components={COMPONENTS}
      >
        {content}
      </Markdown>
    </div>
  )
}
