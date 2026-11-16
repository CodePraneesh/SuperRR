import React from 'react'

interface MarkdownViewProps {
  content: string
  className?: string
  dark?: boolean
}

export const MarkdownView: React.FC<MarkdownViewProps> = ({ content, className = '', dark = false }) => {
  const lines = content.split('\n')

  const baseText = dark ? 'text-slate-200' : 'text-[#475569]'
  const h1Class = dark
    ? 'text-xl md:text-2xl font-black tracking-tight text-pink-300 pt-2 pb-1.5 border-b border-[#182752] flex items-center gap-2.5'
    : 'text-xl md:text-2xl font-black tracking-tight text-[#0F172A] pt-2 pb-1.5 border-b border-slate-200 flex items-center gap-2.5'
  const h2Class = dark
    ? 'text-base md:text-lg font-bold text-blue-300 pt-3 pb-1 border-b border-[#182752]/70 flex items-center gap-2'
    : 'text-base md:text-lg font-bold text-[#0F172A] pt-3 pb-1 border-b border-slate-200 flex items-center gap-2'
  const h3Class = dark
    ? 'text-sm font-bold text-amber-300 pt-2 flex items-center gap-1.5'
    : 'text-sm font-bold text-amber-800 pt-2 flex items-center gap-1.5'
  const bulletText = dark ? 'text-slate-200' : 'text-[#475569]'
  const blockquoteClass = dark
    ? 'border-l-3 border-pink-500 bg-pink-950/20 pl-3.5 py-2 rounded-r text-pink-200/90 italic my-1.5'
    : 'border-l-3 border-[#EC008C] bg-pink-50/70 pl-3.5 py-2 rounded-r text-[#334155] italic my-1.5'
  const pClass = dark ? 'text-slate-300' : 'text-[#475569]'

  return (
    <div className={`space-y-3 ${baseText} leading-relaxed text-sm ${className}`}>
      {lines.map((line, idx) => {
        const trimmed = line.trim()

        if (!trimmed) {
          return <div key={idx} className="h-2" />
        }

        // H1 Heading
        if (trimmed.startsWith('# ')) {
          return (
            <h1 key={idx} className={h1Class}>
              <span className="w-1.5 h-5 bg-gradient-to-b from-pink-500 to-rose-600 rounded-full inline-block" />
              {parseInline(trimmed.substring(2), dark)}
            </h1>
          )
        }

        // H2 Heading
        if (trimmed.startsWith('## ')) {
          return (
            <h2 key={idx} className={h2Class}>
              <span className="w-1.5 h-4 bg-blue-500 rounded-full inline-block" />
              {parseInline(trimmed.substring(3), dark)}
            </h2>
          )
        }

        // H3 Heading
        if (trimmed.startsWith('### ')) {
          return (
            <h3 key={idx} className={h3Class}>
              <span className="w-1 h-3 bg-amber-500 rounded-full inline-block" />
              {parseInline(trimmed.substring(4), dark)}
            </h3>
          )
        }

        // Bullet point
        if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
          return (
            <div key={idx} className="flex items-start gap-2.5 pl-2">
              <span className="w-1.5 h-1.5 rounded-full bg-pink-500 mt-2 flex-shrink-0" />
              <div className={`flex-1 ${bulletText}`}>{parseInline(trimmed.substring(2), dark)}</div>
            </div>
          )
        }

        // Blockquote
        if (trimmed.startsWith('> ')) {
          return (
            <div key={idx} className={blockquoteClass}>
              {parseInline(trimmed.substring(2), dark)}
            </div>
          )
        }

        // Regular paragraph
        return (
          <p key={idx} className={pClass}>
            {parseInline(trimmed, dark)}
          </p>
        )
      })}
    </div>
  )
}

function parseInline(text: string, dark = false): React.ReactNode {
  const parts: React.ReactNode[] = []
  let remaining = text
  let keyIdx = 0

  const strongClass = dark ? 'font-semibold text-white' : 'font-semibold text-[#0F172A]'
  const codeClass = dark
    ? 'font-mono text-xs px-1.5 py-0.5 rounded bg-[#101b3b] text-pink-300 border border-[#1e2f5f]'
    : 'font-mono text-xs px-1.5 py-0.5 rounded bg-slate-100 text-[#0F172A] border border-slate-200'

  while (remaining.length > 0) {
    const boldMatch = remaining.match(/^(.*?)\*\*(.+?)\*\*(.*)$/)
    const codeMatch = remaining.match(/^(.*?)`(.+?)`(.*)$/)

    if (boldMatch && (!codeMatch || boldMatch[1].length <= codeMatch[1].length)) {
      if (boldMatch[1]) {
        parts.push(boldMatch[1])
      }
      parts.push(
        <strong key={keyIdx++} className={strongClass}>
          {boldMatch[2]}
        </strong>
      )
      remaining = boldMatch[3]
    } else if (codeMatch) {
      if (codeMatch[1]) {
        parts.push(codeMatch[1])
      }
      parts.push(
        <code
          key={keyIdx++}
          className={codeClass}
        >
          {codeMatch[2]}
        </code>
      )
      remaining = codeMatch[3]
    } else {
      parts.push(remaining)
      break
    }
  }

  return parts
}
