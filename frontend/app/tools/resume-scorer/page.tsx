"use client"

import { useEffect, useState } from 'react'
import { useUser } from '@clerk/nextjs'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://project-2-payz.onrender.com'

function scoreText(text: string, role: string) {
  const lower = text.toLowerCase()
  const banks: Record<string,string[]> = {
    'Software Engineer': ['javascript','typescript','react','next','node','express','rest','graphql','docker','kubernetes','aws','git','ci/cd','unit test','integration test','microservices'],
    'Data Analyst': ['sql','excel','tableau','power bi','analytics','dashboards','pandas','numpy','statistics','hypothesis','regression','visualization','etl'],
    'Web Developer': ['html','css','sass','tailwind','responsive','accessibility','seo','webpack','vite','cross-browser','performance'],
    'Backend Developer': ['api','rest','graphql','database','postgres','mysql','mongodb','redis','rabbitmq','scalability','security','authentication'],
    'Cloud/DevOps': ['docker','kubernetes','terraform','aws','gcp','azure','ci/cd','monitoring','prometheus','grafana','logging']
  }
  const commonSoft = ['communication','lead','team','collaborat','ownership','problem','critical','stakeholder']
  const actionVerbs = ['led','built','created','designed','implemented','optimized','automated','developed','delivered','deployed','refactored','improved']
  const metricsRegex = /\b\d+%|\b\d{2,}\b/g
  const sections = {
    experience: /(experience|work|employment)/i.test(text),
    education: /(education|degree|b\.?tech|b\.?ca|b\.?sc|m\.?tech|bachelor|master)/i.test(text),
    projects: /(project|capstone|case study)/i.test(text),
    skills: /(skills|technologies|tech stack)/i.test(text)
  }
  const contact = {
    email: /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i.test(text),
    phone: /\b\d{10}\b/.test(text.replace(/[^\d]/g,'')),
    github: /(github\.com|gitlab\.com)/i.test(text),
    linkedin: /(linkedin\.com)/i.test(text)
  }
  const roleKeys = banks[role] || []
  const softHits = commonSoft.filter(k=> lower.includes(k))
  const roleHits = roleKeys.filter(k=> lower.includes(k))
  const missingKeywords = roleKeys.filter(k=> !lower.includes(k)).slice(0,8)
  const actionCount = actionVerbs.reduce((acc, v)=> acc + (lower.includes(v) ? 1 : 0), 0)
  const metricsCount = (text.match(metricsRegex) || []).length
  const lengthWords = text.split(/\s+/).filter(Boolean).length
  const keywordCoverage = Math.round((roleHits.length / Math.max(roleKeys.length,1)) * 100)
  let score = 50
  score += Math.min(keywordCoverage, 40) * 0.6
  score += Math.min(actionCount*5, 20)
  score += Math.min(metricsCount*6, 24)
  score += Math.min(Math.max(lengthWords/350,0),1) * 6
  score = Math.min(100, Math.round(score))
  const suggestions: string[] = []
  if (!sections.experience) suggestions.push('Add an Experience section with 3–5 impact-focused bullet points per role.')
  if (!sections.projects) suggestions.push('Include 2–3 projects highlighting tech stack and quantified outcomes.')
  if (!sections.skills) suggestions.push('Add a Skills section grouped by Languages, Frameworks, Tools.')
  if (!sections.education) suggestions.push('Add an Education section with degree, institution, and year.')
  if (!contact.github) suggestions.push('Add your GitHub/portfolio link to showcase work.')
  if (!contact.linkedin) suggestions.push('Add your LinkedIn profile link for recruiter screening.')
  if (actionCount < 4) suggestions.push('Start bullets with strong action verbs (Built, Led, Optimized, Automated).')
  if (metricsCount < 3) suggestions.push('Quantify results with metrics (% improvement, time saved, revenue impact).')
  if (keywordCoverage < 60) suggestions.push(`Add role-specific keywords: ${missingKeywords.join(', ')}.`)
  if (lengthWords < 250) suggestions.push('Expand bullets with context, action, and measurable result (STAR).')
  if (/\bI\b|\bmy\b/i.test(text)) suggestions.push('Avoid first-person pronouns; use concise bullet statements.')
  return { score, suggestions, missingKeywords, coverage: keywordCoverage, metricsCount, actionVerbCount: actionCount, sections, contact }
}

export default function ResumeScorer() {
  const { user } = useUser()
  const [userId, setUserId] = useState<number | null>(null)
  const [files, setFiles] = useState<any[]>([])
  const [resumeText, setResumeText] = useState('')
  const [targetRole, setTargetRole] = useState('Software Engineer')
  const [result, setResult] = useState<any>(null)

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
              <div className="mb-3">
                <label className="text-sm mr-2">Target Role</label>
                <select className="border rounded px-2 py-1" value={targetRole} onChange={(e)=> setTargetRole(e.target.value)}>
                  <option>Software Engineer</option>
                  <option>Backend Developer</option>
                  <option>Web Developer</option>
                  <option>Data Analyst</option>
                  <option>Cloud/DevOps</option>
                </select>
              </div>
              <Textarea rows={12} placeholder="Paste your resume text here..." value={resumeText} onChange={(e)=>setResumeText(e.target.value)} />
              <Button className="mt-4 bg-maroon hover:bg-maroon/90" onClick={()=> setResult(scoreText(resumeText, targetRole))}>Score</Button>
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
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <p className="text-lg">Score: <span className="font-semibold">{result.score}/100</span></p>
                  <p className="text-sm text-gray-700">Keyword Coverage: {result.coverage}%</p>
                  <p className="text-sm text-gray-700">Action Verbs: {result.actionVerbCount}</p>
                  <p className="text-sm text-gray-700">Metrics Used: {result.metricsCount}</p>
                </div>
                <div>
                  <p className="font-medium">Detected Sections</p>
                  <p className="text-sm text-gray-700">Experience: {result.sections.experience ? 'Yes' : 'No'}</p>
                  <p className="text-sm text-gray-700">Projects: {result.sections.projects ? 'Yes' : 'No'}</p>
                  <p className="text-sm text-gray-700">Skills: {result.sections.skills ? 'Yes' : 'No'}</p>
                  <p className="text-sm text-gray-700">Education: {result.sections.education ? 'Yes' : 'No'}</p>
                </div>
                <div>
                  <p className="font-medium">Contact Presence</p>
                  <p className="text-sm text-gray-700">Email: {result.contact.email ? 'Yes' : 'No'}</p>
                  <p className="text-sm text-gray-700">Phone: {result.contact.phone ? 'Yes' : 'No'}</p>
                  <p className="text-sm text-gray-700">GitHub: {result.contact.github ? 'Yes' : 'No'}</p>
                  <p className="text-sm text-gray-700">LinkedIn: {result.contact.linkedin ? 'Yes' : 'No'}</p>
                </div>
              </div>
              <div className="mt-4">
                <p className="font-medium">Top Missing Keywords</p>
                <div className="flex flex-wrap gap-2 mt-2">
                  {result.missingKeywords.map((k:string,i:number)=> (
                    <span key={i} className="px-2 py-1 text-xs bg-gold text-maroon rounded">{k}</span>
                  ))}
                  {result.missingKeywords.length===0 && <p className="text-sm text-gray-700">All key terms present</p>}
                </div>
              </div>
              <div className="mt-4">
                <p className="font-medium">Suggestions</p>
                <ul className="list-disc list-inside mt-2 text-gray-700">
                  {result.suggestions.map((s:string, i:number)=> (<li key={i}>{s}</li>))}
                </ul>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
