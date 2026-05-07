import { useState, useCallback } from 'react'

export function useStream() {
  const [streaming, setStreaming] = useState(false)

  const streamQuestion = useCallback(async (
    question,
    onToken,
    onDone,
    onError
  ) => {
    setStreaming(true)

    const apiKey = localStorage.getItem('api_key')
    const sessionId = localStorage.getItem('session_id')

    try {
      const response = await fetch('/api/ask/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey || '',
          'X-Session-Id': sessionId || ''
        },
        body: JSON.stringify({ question })
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Stream request failed')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        // Decode chunk and add to buffer
        buffer += decoder.decode(value, { stream: true })

        // Process all complete lines in buffer
        const lines = buffer.split('\n')

        // Keep last incomplete line in buffer
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trim()

          // Skip empty lines
          if (!trimmed) continue

          // Must start with "data: "
          if (!trimmed.startsWith('data: ')) continue

          const jsonStr = trimmed.slice(6) // remove "data: "

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
          } catch (parseErr) {
            // Skip malformed JSON lines
            console.warn('Failed to parse SSE line:', jsonStr)
          }
        }
      }

    } catch (err) {
      console.error('Stream error:', err)
      onError(err.message || 'Something went wrong')
    } finally {
      setStreaming(false)
    }
  }, [])

  return { streaming, streamQuestion }
}