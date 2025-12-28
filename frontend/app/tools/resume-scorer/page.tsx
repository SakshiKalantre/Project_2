"use client"

import { useEffect, useState } from 'react'
import { useUser } from '@clerk/nextjs'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://project-2-payz.onrender.com'

function scoreText(text: string) {
  const areas = {
    programming: ['javascript','typescript','python','java','c++','node','react','next','go','rust'],
    data: ['sql','excel','tableau','power bi','machine learning','data analysis','pandas','numpy'],
    web: ['html','css','sass','tailwind','responsive','accessibility','seo'],
    soft: ['team','lead','communication','collaborat','problem','critical','ownership']
  }
  const lower = text.toLowerCase()
  let points = 0, max = 0
  Object.values(areas).forEach(list => { list.forEach(k => { max += 1; if (lower.includes(k)) points += 1 }) })
  const lengthBonus = Math.min(Math.max(text.split(/\s+/).length / 300, 0), 1) * 10
  const score = Math.round(((points / Math.max(max,1)) * 90) + lengthBonus)
  const suggestions: string[] = []
  if (!lower.includes('project')) suggestions.push('Add 2–3 strong project bullets with outcomes.')
  if (!lower.includes('impact') && !lower.match(/\b\d+%|\b\d{2,}\b/)) suggestions.push('Quantify impact with metrics (% improvement, time saved).')
  if (!lower.includes('intern')) suggestions.push('Include internships or relevant experience.')
  if (!lower.includes('github')) suggestions.push('Add portfolio/GitHub links for credibility.')
  return { score, suggestions }
}

export default function ResumeScorer() {
  const { user } = useUser()
  const [userId, setUserId] = useState<number | null>(null)
  const [files, setFiles] = useState<any[]>([])
  const [resumeText, setResumeText] = useState('')
  const [result, setResult] = useState<{ score:number; suggestions:string[] } | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        let email: string | null = null
        if (user) {
          // @ts-ignore
          email = user.primaryEmailAddress?.emailAddress || user.emailAddresses?.[0]?.emailAddress || null
        }
        if (!email) {
          const stored = typeof window !== 'undefined' ? localStorage.getItem('currentUser') : null
          const current = stored ? JSON.parse(stored) : null
          email = current?.email || null
        }
        if (!email) return
        const u = await fetch(`${API_BASE}/api/v1/users/by-email/${encodeURIComponent(email)}`)
        if (u.ok) { const uj = await u.json(); setUserId(uj.id) }
        if (userId) {
          const res = await fetch(`${API_BASE}/api/v1/files/by-user/${userId}?t=${Date.now()}`, { cache:'no-store' })
          if (res.ok) setFiles(await res.json())
        }
      } catch {}
    }
    load()
  }, [user, userId])

  return (
    <div className="min-h-screen bg-cream">
      <div className="container mx-auto p-6">
        <h1 className="text-3xl font-bold text-maroon mb-6">Resume Scoring</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="border-none shadow-md">
            <CardHeader>
              <CardTitle>Paste Resume Text</CardTitle>
            </CardHeader>
            <CardContent>
              <Textarea rows={12} placeholder="Paste your resume text here..." value={resumeText} onChange={(e)=>setResumeText(e.target.value)} />
              <Button className="mt-4 bg-maroon hover:bg-maroon/90" onClick={()=> setResult(scoreText(resumeText))}>Score</Button>
            </CardContent>
          </Card>
          <Card className="border-none shadow-md">
            <CardHeader>
              <CardTitle>Your Uploaded Resumes</CardTitle>
            </CardHeader>
            <CardContent>
              {files.filter(f=>f.file_type==='resume').map(f=> (
                <div key={f.id} className="flex items-center justify-between py-2 text-sm">
                  <span>{f.filename}</span>
                  <div className="flex gap-2">
                    <Button variant="outline" onClick={async()=>{
                      try {
                        const meta = await fetch(`${API_BASE}/api/v1/files/${f.id}`)
                        if (meta.ok) {
                          const mj = await meta.json()
                          const url = mj.file_url
                          const w = window.open(url, '_blank'); if (!w) { const a=document.createElement('a'); a.href=url; a.target='_blank'; document.body.appendChild(a); a.click(); a.remove() }
                        }
                      } catch {}
                    }}>Open</Button>
                  </div>
                </div>
              ))}
              {files.filter(f=>f.file_type==='resume').length===0 && <p className="text-gray-600">No resumes found. Paste your resume text to score.</p>}
            </CardContent>
          </Card>
        </div>
        {result && (
          <Card className="border-none shadow-md mt-6">
            <CardHeader>
              <CardTitle>Results</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-lg">Score: <span className="font-semibold">{result.score}/100</span></p>
              <ul className="list-disc list-inside mt-2 text-gray-700">
                {result.suggestions.map((s, i)=> (<li key={i}>{s}</li>))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
