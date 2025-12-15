import { NextRequest, NextResponse } from 'next/server'
export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest) {
  try {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://project-2-payz.onrender.com'
    const email = req.nextUrl.searchParams.get('email')
    if (!email) return NextResponse.json({ error: 'email required' }, { status: 400 })
    const res = await fetch(`${API_BASE}/api/v1/users/by-email/${encodeURIComponent(email)}`, { cache: 'no-store' })
    const text = await res.text()
    return new NextResponse(text, { status: res.status, headers: { 'Content-Type': res.headers.get('Content-Type') || 'application/json' } })
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || 'Proxy error' }, { status: 502 })
  }
}
