import React from 'react'

interface MarkdownViewProps {
  content: string
  className?: string
}

export const MarkdownView: React.FC<MarkdownViewProps> = ({ content, className = '' }) => {
  const lines = content.split('\n')

  return (
    <div className={`space-y-3 text-slate-300 leading-relaxed text-sm ${className}`}>
      {lines.map((line, idx) => {
        const trimmed = line.trim()

        if (!trimmed) {
          return <div key={idx} className="h-2" />
        }

        // H1 Heading
        if (trimmed.startsWith('# ')) {
          return (
            <h1
              key={idx}
              className="text-xl md:text-2xl font-black tracking-tight text-white pt-2 pb-1.5 border-b border-[#182752] flex items-center gap-2.5 text-pink-300"
            >
              <span className="w-1.5 h-5 bg-gradient-to-b from-pink-500 to-rose-600 rounded-full inline-block" />
              {parseInline(trimmed.substring(2))}
            </h1>
          )
        }

        // H2 Heading
        if (trimmed.startsWith('## ')) {
          return (
            <h2
              key={idx}
              className="text-base md:text-lg font-bold text-slate-100 pt-3 pb-1 border-b border-[#182752]/70 flex items-center gap-2 text-blue-300"
            >
              <span className="w-1.5 h-4 bg-blue-500 rounded-full inline-block" />
              {parseInline(trimmed.substring(3))}
            </h2>
          )
        }

        // H3 Heading
        if (trimmed.startsWith('### ')) {
          return (
            <h3 key={idx} className="text-sm font-bold text-amber-300 pt-2 flex items-center gap-1.5">
              <span className="w-1 h-3 bg-amber-400 rounded-full inline-block" />
              {parseInline(trimmed.substring(4))}
            </h3>
          )
        }

        // Bullet point
        if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
          return (
            <div key={idx} className="flex items-start gap-2.5 pl-2">
              <span className="w-1.5 h-1.5 rounded-full bg-pink-400 mt-2 flex-shrink-0 shadow-xs shadow-pink-500/50" />
              <div className="flex-1">{parseInline(trimmed.substring(2))}</div>
            </div>
          )
        }

        // Blockquote
        if (trimmed.startsWith('> ')) {
          return (
            <div
              key={idx}
              className="border-l-3 border-pink-500 bg-pink-950/20 pl-3.5 py-2 rounded-r text-pink-200/90 italic my-1.5"
            >
              {parseInline(trimmed.substring(2))}
            </div>
          )
        }

        // Regular paragraph
        return (
          <p key={idx} className="text-slate-300">
            {parseInline(trimmed)}
          </p>
        )
      })}
    </div>
  )
}

function parseInline(text: string): React.ReactNode {
  const parts: React.ReactNode[] = []
  let remaining = text
  let keyIdx = 0

  while (remaining.length > 0) {
    const boldMatch = remaining.match(/^(.*?)\*\*(.+?)\*\*(.*)$/)
    const codeMatch = remaining.match(/^(.*?)`(.+?)`(.*)$/)

    if (boldMatch && (!codeMatch || boldMatch[1].length <= codeMatch[1].length)) {
      if (boldMatch[1]) {
        parts.push(boldMatch[1])
      }
      parts.push(
        <strong key={keyIdx++} className="font-semibold text-white">
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
          className="font-mono text-xs px-1.5 py-0.5 rounded bg-[#101b3b] text-pink-300 border border-[#1e2f5f]"
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
