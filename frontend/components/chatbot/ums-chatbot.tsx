"use client"

import * as React from "react"
import {
  ArrowUp,
  Bot,
  ExternalLink,
  Loader2,
  LockKeyhole,
  MessageCircle,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react"

import {
  sendChatbotQuestion,
  type ChatbotResponse,
  type ChatbotSource,
} from "@/lib/chatbot"

type ChatMessage = {
  id: number
  role: "assistant" | "user"
  text: string
  requiresAuth?: boolean
  scope?: string
  sources?: ChatbotSource[]
}

const STARTER_MESSAGES = [
  "Who am I?",
  "When is my next class?",
  "What is my next deadline?",
  "Latest events",
]

function sourceHref(url?: string) {
  if (!url) return ""
  if (/^https?:\/\//i.test(url)) return url
  return url.startsWith("/") ? url : `/${url}`
}

function AssistantBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user"
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[84%] rounded-lg px-3 py-2 text-sm leading-6 shadow-sm ${
          isUser
            ? "bg-primary text-primary-foreground"
            : "border border-border bg-background text-foreground"
        }`}
      >
        <p className="whitespace-pre-wrap break-words">{message.text}</p>
        {!isUser && message.requiresAuth ? (
          <div className="mt-2 flex items-center gap-1.5 text-xs font-medium text-amber-600 dark:text-amber-400">
            <LockKeyhole className="size-3.5" />
            <span>Login required</span>
          </div>
        ) : null}
        {!isUser && message.scope === "privacy" ? (
          <div className="mt-2 flex items-center gap-1.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
            <ShieldCheck className="size-3.5" />
            <span>Privacy protected</span>
          </div>
        ) : null}
        {!isUser && message.sources && message.sources.length > 0 ? (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {message.sources.slice(0, 3).map((source) => {
              const href = sourceHref(source.url)
              const label = source.title || source.type
              if (!href) {
                return (
                  <span
                    key={`${source.type}-${label}`}
                    className="rounded-md border border-border bg-muted px-2 py-1 text-[11px] font-medium text-muted-foreground"
                  >
                    {label}
                  </span>
                )
              }
              return (
                <a
                  key={`${source.type}-${label}`}
                  href={href}
                  className="inline-flex items-center gap-1 rounded-md border border-border bg-muted px-2 py-1 text-[11px] font-medium text-muted-foreground hover:text-foreground"
                  target={href.startsWith("http") ? "_blank" : undefined}
                  rel={href.startsWith("http") ? "noreferrer" : undefined}
                >
                  <span>{label}</span>
                  <ExternalLink className="size-3" />
                </a>
              )
            })}
          </div>
        ) : null}
      </div>
    </div>
  )
}

function responseToMessage(response: ChatbotResponse, id: number): ChatMessage {
  return {
    id,
    role: "assistant",
    text: response.answer,
    requiresAuth: response.requires_auth,
    scope: response.scope,
    sources: response.sources,
  }
}

export function UmsChatbot() {
  const [isOpen, setIsOpen] = React.useState(false)
  const [question, setQuestion] = React.useState("")
  const [isSending, setIsSending] = React.useState(false)
  const [messages, setMessages] = React.useState<ChatMessage[]>([
    {
      id: 1,
      role: "assistant",
      text: "How can I help?",
    },
  ])
  const messageId = React.useRef(2)
  const scrollRef = React.useRef<HTMLDivElement | null>(null)

  React.useEffect(() => {
    if (!isOpen) return
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    })
  }, [isOpen, messages])

  const submitQuestion = React.useCallback(
    async (value?: string) => {
      const nextQuestion = (value ?? question).trim()
      if (!nextQuestion || isSending) return

      setMessages((current) => [
        ...current,
        {
          id: messageId.current++,
          role: "user",
          text: nextQuestion,
        },
      ])
      setQuestion("")
      setIsSending(true)

      try {
        const response = await sendChatbotQuestion(nextQuestion)
        setMessages((current) => [
          ...current,
          responseToMessage(response, messageId.current++),
        ])
      } catch (error) {
        setMessages((current) => [
          ...current,
          {
            id: messageId.current++,
            role: "assistant",
            text:
              error instanceof Error
                ? error.message
                : "The assistant could not answer right now.",
          },
        ])
      } finally {
        setIsSending(false)
      }
    },
    [isSending, question]
  )

  return (
    <div data-ums-chatbot className="fixed bottom-4 right-4 z-50 flex max-w-[calc(100vw-1rem)] flex-col items-end sm:bottom-5 sm:right-5">
      {isOpen ? (
        <section className="mb-3 flex h-[min(620px,76vh)] w-[min(400px,calc(100vw-1rem))] flex-col overflow-hidden rounded-lg border border-border bg-popover text-popover-foreground shadow-2xl">
          <header className="flex h-14 shrink-0 items-center justify-between border-b border-border bg-card px-4">
            <div className="flex min-w-0 items-center gap-3">
              <span className="grid size-9 shrink-0 place-items-center rounded-lg border border-border bg-background text-foreground">
                <Bot className="size-5" />
              </span>
              <div className="min-w-0">
                <h2 className="truncate text-sm font-semibold text-foreground">
                  Portal Assistant
                </h2>
                <div className="mt-0.5 flex items-center gap-1.5 text-xs text-muted-foreground">
                  <span className="size-1.5 rounded-full bg-emerald-500" />
                  <span>Portal</span>
                </div>
              </div>
            </div>
            <button
              type="button"
              className="grid size-9 place-items-center rounded-md text-muted-foreground transition hover:bg-muted hover:text-foreground"
              onClick={() => setIsOpen(false)}
              aria-label="Close assistant"
            >
              <X className="size-5" />
            </button>
          </header>

          <div
            ref={scrollRef}
            className="flex-1 space-y-3 overflow-y-auto bg-muted/30 px-3 py-4"
          >
            {messages.map((message) => (
              <AssistantBubble key={message.id} message={message} />
            ))}
            {isSending ? (
              <div className="flex justify-start">
                <div className="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 text-sm text-muted-foreground shadow-sm">
                  <Loader2 className="size-4 animate-spin" />
                  <span>Thinking</span>
                </div>
              </div>
            ) : null}
          </div>

          <div className="shrink-0 border-t border-border bg-card p-3">
            <div className="mb-2 flex gap-2 overflow-x-auto pb-1">
              {STARTER_MESSAGES.map((item) => (
                <button
                  key={item}
                  type="button"
                  className="shrink-0 rounded-md border border-border bg-background px-2.5 py-1.5 text-xs font-medium text-muted-foreground transition hover:bg-muted hover:text-foreground disabled:opacity-60"
                  onClick={() => void submitQuestion(item)}
                  disabled={isSending}
                >
                  {item}
                </button>
              ))}
            </div>
            <form
              className="flex items-end gap-2"
              onSubmit={(event) => {
                event.preventDefault()
                void submitQuestion()
              }}
            >
              <label className="sr-only" htmlFor="ums-chatbot-question">
                Ask a question
              </label>
              <textarea
                id="ums-chatbot-question"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault()
                    void submitQuestion()
                  }
                }}
                rows={1}
                className="max-h-28 min-h-10 flex-1 resize-none rounded-md border border-input bg-background px-3 py-2 text-sm leading-6 text-foreground outline-none transition placeholder:text-muted-foreground focus:border-ring focus:ring-2 focus:ring-ring/25"
                placeholder="Ask a question"
              />
              <button
                type="submit"
                className="grid size-10 shrink-0 place-items-center rounded-md bg-primary text-primary-foreground transition hover:opacity-90 disabled:cursor-not-allowed disabled:bg-muted disabled:text-muted-foreground"
                disabled={isSending || question.trim().length === 0}
                aria-label="Send message"
              >
                {isSending ? (
                  <Loader2 className="size-5 animate-spin" />
                ) : (
                  <ArrowUp className="size-5" />
                )}
              </button>
            </form>
          </div>
        </section>
      ) : null}

      <button
        type="button"
        title="Open assistant"
        className="group relative grid size-14 place-items-center rounded-[1.15rem] border border-border bg-primary text-primary-foreground shadow-2xl transition hover:-translate-y-0.5 hover:opacity-95 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-background"
        onClick={() => setIsOpen((current) => !current)}
        aria-label={isOpen ? "Close assistant" : "Open assistant"}
      >
        <MessageCircle className="size-6 transition group-hover:scale-95" />
        <span className="absolute -right-1 -top-1 grid size-5 place-items-center rounded-md border border-background bg-emerald-500 text-white">
          <Sparkles className="size-3" />
        </span>
      </button>
    </div>
  )
}
