import { useEffect, useRef, useState, useCallback } from 'react'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'

export function useWebSocket() {
  const wsRef = useRef(null)
  const [connected, setConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState(null)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws
    ws.onopen  = () => { setConnected(true); console.log('[WS] Connected') }
    ws.onmessage = (evt) => {
      try { setLastMessage(JSON.parse(evt.data)) } catch(e) {}
    }
    ws.onclose = () => { setConnected(false); setTimeout(connect, 3000) }
    ws.onerror = (err) => console.error('[WS] Error', err)
  }, [])

  useEffect(() => {
    connect()
    return () => wsRef.current?.close()
  }, [connect])

  return { connected, lastMessage }
}
