import { useEffect, useRef } from "react"
import { AssistantMarkdown, MeasurementCard, SpecCard, type Message } from "@nurb/ui"

function Payload({ message }: { message: Message }) {
  const payload = message.payload
  if (!payload) return null
  // Tool calls and the builds they ran are how the part got made; the part on the
  // stage is the result, so they stay off the page.
  switch (payload.type) {
    case "spec":
      return <SpecCard spec={payload.spec} model={payload.model} effort={payload.effort} />
    case "measurement":
      return <MeasurementCard measurement={payload.measurement} />
  }
}

export default function Transcript({ messages }: { messages: Message[] }) {
  const scroller = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = scroller.current
    if (!el) return
    // On a fresh load the cards get their height after the fonts land, so the bottom is only real a frame later.
    const frame = requestAnimationFrame(() => {
      el.scrollTop = el.scrollHeight
    })
    return () => cancelAnimationFrame(frame)
  }, [messages.length])

  return (
    <div ref={scroller} className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto p-4">
      {messages.length === 0 ? (
        <p className="mono-caption text-muted">Nothing here yet. Ask your agent to build a part.</p>
      ) : null}
      {messages.filter((m) => m.content || (m.payload?.type !== "step" && m.payload?.type !== "build")).map((message) => (
        <div key={message.id} className="flex flex-col gap-3">
          {message.content ? (
            message.role === "user" ? (
              <p className="text-chat ml-8 rounded-content bg-raised px-3 py-2 text-ink">{message.content}</p>
            ) : (
              <div className="text-chat text-ink-soft">
                <AssistantMarkdown content={message.content} />
              </div>
            )
          ) : null}
          <Payload message={message} />
        </div>
      ))}
    </div>
  )
}
