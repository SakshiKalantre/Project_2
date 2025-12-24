import { NextResponse } from 'next/server'
export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const { user_id, title, message } = body || {}
    if (!user_id || !title || !message) {
      return NextResponse.json({ error: 'Missing user_id, title or message' }, { status: 400 })
    }
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://project-2-payz.onrender.com'
    let res = await fetch(`${API_BASE}/api/v1/users/${encodeURIComponent(user_id)}/notifications`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, message })
    })
    if (!res.ok) {
      // Fallback to FastAPI notifications create
      res = await fetch(`${API_BASE}/api/v1/notifications`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id, title, message, notification_type: 'system' })
      })
    }
    const text = await res.text()
    return new NextResponse(text, { status: res.status, headers: { 'Content-Type': res.headers.get('Content-Type') || 'application/json' } })
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || 'Proxy error' }, { status: 502 })
  }
}
