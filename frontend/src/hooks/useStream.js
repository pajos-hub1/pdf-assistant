import { useState, useCallback } from 'react'

export function useStream() {
  const [streaming, setStreaming] = useState(false)

  const streamQuestion = useCallback(async (
    question,
    onToken,
    onDone,
    onError,
    onSuggestions
  ) => {
    setStreaming(true)

    const accessToken = localStorage.getItem('access_token')
    const sessionId = localStorage.getItem('session_id')

    try {
      const response = await fetch('/api/ask/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken || ''}`,
          'X-Session-Id': sessionId || ''
        },
        body: JSON.stringify({ question })
      })

      if (!response.ok) {
        let errorMsg = 'Stream request failed'
        try {
          const err = await response.json()
          errorMsg = err.detail || errorMsg
        } catch {
          errorMsg = `HTTP ${response.status}`
        }
        throw new Error(errorMsg)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let buffer = ''

      const processLine = (line) => {
        const trimmed = line.trim()
        if (!trimmed || !trimmed.startsWith('data: ')) return

        const jsonStr = trimmed.slice(6).trim()
        if (!jsonStr) return

        try {
          const data = JSON.parse(jsonStr)

          if (data.token !== undefined && data.token !== null) {
            onToken(data.token)
          }

          if (data.done === true) {
            onDone({
              confidence: data.confidence || '0%',
              sources: data.sources || [],
              suggestions: data.suggestions || [],
              language: data.language || 'English'
            })
          }

          // Late suggestions event
          if (data.suggestions && !data.done && onSuggestions) {
            onSuggestions(data.suggestions)
          }

          if (data.error) {
            onError(data.error)
          }

        } catch (parseErr) {
          // Skip malformed lines silently
        }
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        const events = buffer.split('\n\n')
        buffer = events.pop() || ''

        for (const event of events) {
          const lines = event.split('\n')
          for (const line of lines) {
            processLine(line)
          }
        }
      }

      // Process any remaining buffer
      if (buffer.trim()) {
        const lines = buffer.split('\n')
        for (const line of lines) {
          processLine(line)
        }
      }

    } catch (err) {
      onError(err.message || 'Something went wrong. Please try again.')
    } finally {
      setStreaming(false)
    }
  }, [])

  return { streaming, streamQuestion }
}