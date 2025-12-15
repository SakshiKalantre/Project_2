import { NextRequest, NextResponse } from 'next/server'
export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function POST(req: NextRequest) {
  try {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://project-2-payz.onrender.com'
    const body = await req.json()
    const userId = body?.user_id
    if (!userId) return NextResponse.json({ error: 'user_id required' }, { status: 400 })
    const payload = { phone: body?.phone || null, degree: body?.degree || null, year: body?.year || null, skills: body?.skills || null, about: body?.about || null, alternate_email: body?.alternate_email || null }
    const res = await fetch(`${API_BASE}/api/v1/users/${userId}/profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      cache: 'no-store',
      body: JSON.stringify(payload)
    })
    const text = await res.text()
    return new NextResponse(text, { status: res.status, headers: { 'Content-Type': res.headers.get('Content-Type') || 'application/json' } })
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || 'Proxy error' }, { status: 502 })
  }
}
