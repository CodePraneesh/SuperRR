import React, { useState, useRef, useEffect } from 'react'
import {
  Bot,
  Send,
  User,
  Sparkles,
  Trash2,
  AlertCircle,
  HelpCircle,
  ShieldCheck,
  CheckCircle2,
  Crown,
} from 'lucide-react'
import { askAnalyticsQuestion } from '../api/scoutingApi'
import type { AnalyticsQueryResponse } from '../types/scouting'
import type { Scope } from '../types/common'
import { Card } from '../components/common/Card'
import { Badge } from '../components/common/Badge'
import { MarkdownView } from '../components/common/MarkdownView'
import { getErrorMessage } from '../api/client'

interface ChatMessage {
  id: string
  sender: 'user' | 'assistant'
  content: string
  timestamp: string
  meta?: {
    tier_used?: string
    verified?: boolean
    model_name?: string
  }
}

export const ScoutingAssistantPage: React.FC = () => {
  const [scope, setScope] = useState<Scope>('IPL')
  const [inputQuery, setInputQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      content:
        '# SupeRR AI Scouting Assistant Online\n\nWelcome to the **SupeRR Intelligence AI Terminal**. I can answer tactical cricket questions, compare players under pressure, explain clutch ratings, and provide evidence-grounded scouting insights strictly derived from frozen **CPRI v1.0.0** data.\n\nAsk a natural-language query below, or choose one of the suggested prompts to get started.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      meta: {
        tier_used: 'Tier 3: Deterministic Fallback Engine',
        verified: true,
      },
    },
  ])

  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  const suggestedQuestions = [
    'Why is Rinku Singh ranked highly under IPL pressure?',
    'Compare Rinku Singh and Suryakumar Yadav under match pressure.',
    'What makes Matheesha Pathirana effective in death overs?',
    'Explain the CPRI component weights and pressure threshold.',
  ]

  const handleSendMessage = async (queryText?: string) => {
    const query = queryText || inputQuery
    if (!query.trim() || loading) return

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      content: query.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages((prev) => [...prev, userMsg])
    if (!queryText) setInputQuery('')
    setLoading(true)

    try {
      const res = await askAnalyticsQuestion({
        query: query.trim(),
        scope,
      })

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        sender: 'assistant',
        content: res.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        meta: {
          tier_used: res.tier_used,
          verified: res.verified,
          model_name: res.model_name,
        },
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch (err) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'assistant',
        content: `**Error communicating with scouting engine**: ${getErrorMessage(err)}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setLoading(false)
    }
  }

  const handleClearHistory = () => {
    setMessages([
      {
        id: 'welcome-cleared',
        sender: 'assistant',
        content: 'Conversation cleared. Ask any cricket analytics or scouting question.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ])
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto flex flex-col h-[calc(100vh-8rem)]">
      {/* Header Bar */}
      <div className="flex items-center justify-between pb-3 border-b border-[#182752]">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono font-medium text-pink-400 mb-0.5">
            <Crown className="w-4 h-4 text-amber-400" />
            <span>AI Scouting Terminal</span>
          </div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Natural-Language</span>
            <span className="text-pink-500 font-black">Cricket QA</span>
          </h1>
        </div>

        <div className="flex items-center gap-3">
          {/* Scope Selector */}
          <div className="inline-flex rounded-lg p-1 bg-[#0c132c] border border-[#182752] text-xs font-semibold">
            <button
              onClick={() => setScope('IPL')}
              className={`px-3 py-1 rounded-md transition-all ${
                scope === 'IPL'
                  ? 'bg-gradient-to-r from-blue-700 to-indigo-700 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              IPL Scope
            </button>
            <button
              onClick={() => setScope('T20I')}
              className={`px-3 py-1 rounded-md transition-all ${
                scope === 'T20I'
                  ? 'bg-gradient-to-r from-blue-700 to-indigo-700 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              T20I Scope
            </button>
          </div>

          <button
            onClick={handleClearHistory}
            className="p-2 rounded-lg bg-[#0c132c] hover:bg-[#182752] border border-[#182752] text-slate-400 hover:text-rose-400 transition-colors"
            title="Clear Chat History"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Suggested Prompt Chips */}
      <div className="flex flex-wrap gap-2">
        <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1 self-center mr-1">
          <Sparkles className="w-3 h-3 text-pink-400" />
          Try asking:
        </span>
        {suggestedQuestions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSendMessage(q)}
            disabled={loading}
            className="text-xs px-2.5 py-1 rounded-lg bg-[#0c132c] hover:bg-[#182752] border border-[#182752] hover:border-pink-500/40 text-slate-300 hover:text-pink-200 transition-colors text-left"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Message History Container */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2 rounded-2xl bg-[#070b18]/80 border border-[#182752] p-4 md:p-6">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start gap-3 ${
              msg.sender === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {msg.sender === 'assistant' && (
              <div className="w-8 h-8 rounded-xl bg-pink-600/20 border border-pink-500/40 flex items-center justify-center text-pink-400 flex-shrink-0 mt-1 shadow-sm shadow-pink-500/10">
                <Crown className="w-4 h-4 text-amber-400" />
              </div>
            )}

            <div
              className={`max-w-[85%] rounded-2xl p-4 md:p-5 ${
                msg.sender === 'user'
                  ? 'bg-gradient-to-r from-pink-600 to-rose-600 text-white rounded-br-xs shadow-md shadow-pink-600/20'
                  : 'bg-[#0c132c] border border-[#182752] text-slate-200 rounded-bl-xs shadow-md'
              }`}
            >
              <div className="flex items-center justify-between gap-4 mb-2 pb-1.5 border-b border-[#182752]/80 text-[10px] font-mono opacity-80">
                <span className="font-semibold uppercase tracking-wider">
                  {msg.sender === 'user' ? 'You' : 'SupeRR Intelligence Engine'}
                </span>
                <span>{msg.timestamp}</span>
              </div>

              {msg.sender === 'assistant' ? (
                <MarkdownView content={msg.content} />
              ) : (
                <p className="text-sm leading-relaxed">{msg.content}</p>
              )}

              {msg.meta && (
                <div className="mt-3 pt-2 border-t border-[#182752]/80 flex items-center justify-between text-[10px] font-mono text-slate-400">
                  <span className="flex items-center gap-1 text-emerald-400">
                    <CheckCircle2 className="w-3 h-3" />
                    Audited by Response Verifier
                  </span>
                  <span className="text-pink-300 font-semibold">{msg.meta.tier_used}</span>
                </div>
              )}
            </div>

            {msg.sender === 'user' && (
              <div className="w-8 h-8 rounded-xl bg-[#0c132c] border border-pink-500/30 flex items-center justify-center text-pink-300 flex-shrink-0 mt-1">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-xl bg-pink-600/20 border border-pink-500/30 flex items-center justify-center text-pink-400 flex-shrink-0 mt-1">
              <Bot className="w-4 h-4 animate-pulse text-pink-400" />
            </div>
            <div className="bg-[#0c132c] border border-[#182752] rounded-2xl p-4 text-xs font-mono text-slate-400 flex items-center gap-3">
              <span className="w-2 h-2 rounded-full bg-pink-400 animate-ping" />
              Grounded statistical reasoning in progress...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault()
          handleSendMessage()
        }}
        className="flex items-center gap-2"
      >
        <input
          type="text"
          placeholder="Ask about CPRI rankings, player clutch stats, or tactical matchups..."
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          disabled={loading}
          className="flex-1 px-4 py-3 rounded-xl bg-[#0c132c] border border-[#182752] text-sm text-white placeholder-slate-500 focus:outline-none focus:border-pink-500 transition-colors"
        />
        <button
          type="submit"
          disabled={loading || !inputQuery.trim()}
          className="px-5 py-3 rounded-xl bg-gradient-to-r from-pink-600 to-rose-600 hover:from-pink-500 hover:to-rose-500 text-white font-bold transition-all disabled:opacity-40 flex items-center gap-2 shadow-md shadow-pink-600/20"
        >
          <Send className="w-4 h-4" />
          <span className="hidden sm:inline text-xs">Send</span>
        </button>
      </form>
    </div>
  )
}
