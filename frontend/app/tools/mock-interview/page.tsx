"use client"

import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

type Question = { type: 'open' | 'mcq'; text: string; options?: string[]; correct?: number }
const banks: Record<string, Question[]> = {
  "Software Engineer": [
    { type:'open', text:"Explain a recent project where you improved performance." },
    { type:'open', text:"How do you design scalable APIs?" },
    { type:'open', text:"Describe a time you resolved a production incident." },
    { type:'open', text:"What are your favorite testing strategies?" },
    { type:'open', text:"Walk through code you’re proud of and why." }
  ],
  "Backend Developer": [
    { type:'open', text:"Design a rate limiting strategy for a public API." },
    { type:'open', text:"Compare SQL vs NoSQL for a high-write workload." },
    { type:'open', text:"How would you implement idempotent operations?" },
    { type:'open', text:"Explain securing sensitive configuration secrets." },
    { type:'open', text:"Describe your approach to database migrations." }
  ],
  "Web Developer": [
    { type:'open', text:"How do you optimize web performance on slow networks?" },
    { type:'open', text:"Explain accessibility checks you include by default." },
    { type:'open', text:"Discuss your CSS architecture and naming approach." },
    { type:'open', text:"How do you prevent layout shifts and jank?" },
    { type:'open', text:"Describe a complex UI state you managed cleanly." }
  ],
  "Data Analyst": [
    { type:'open', text:"Share a dataset you analyzed and key insights." },
    { type:'open', text:"How do you handle missing or noisy data?" },
    { type:'open', text:"Describe a dashboard you built and decisions it enabled." },
    { type:'open', text:"Which statistical tests do you commonly use and when?" },
    { type:'open', text:"Tell me about a time you automated reporting." }
  ],
  "ML Engineer": [
    { type:'open', text:"Describe model selection tradeoffs for a classification task." },
    { type:'open', text:"How do you monitor model drift in production?" },
    { type:'open', text:"Explain feature engineering for tabular data." },
    { type:'open', text:"Compare offline vs online evaluation approaches." },
    { type:'open', text:"Discuss responsible AI considerations you apply." }
  ],
  "QA Engineer": [
    { type:'open', text:"How do you design test cases for edge scenarios?" },
    { type:'open', text:"Explain balancing automation vs manual testing." },
    { type:'open', text:"Describe your bug triage and prioritization method." },
    { type:'open', text:"How do you measure test coverage meaningfully?" },
    { type:'open', text:"Share an example of improving release quality." }
  ],
  "DevOps/SRE": [
    { type:'open', text:"Walk through incident response and postmortem practices." },
    { type:'open', text:"Explain capacity planning and autoscaling signals." },
    { type:'open', text:"Discuss observability pillars you implement." },
    { type:'open', text:"How do you design for high availability?" },
    { type:'open', text:"Share an example of reliability improvements you delivered." }
  ],
  "Cybersecurity": [
    { type:'open', text:"Explain a threat model you created and mitigations." },
    { type:'open', text:"How do you manage secrets and key rotation?" },
    { type:'open', text:"Describe secure coding practices you enforce." },
    { type:'open', text:"Discuss detection and response strategy for breaches." },
    { type:'open', text:"Explain risk assessment and prioritization." }
  ],
  "Product Manager": [
    { type:'open', text:"Describe prioritization framework for roadmap decisions." },
    { type:'open', text:"How do you translate user research into requirements?" },
    { type:'open', text:"Explain defining success metrics for a feature." },
    { type:'open', text:"Share a time you aligned stakeholders with conflicting goals." },
    { type:'open', text:"Discuss tradeoffs you made on scope, timeline, quality." }
  ],
  "UI/UX Designer": [
    { type:'open', text:"Explain your approach to accessible design." },
    { type:'open', text:"Discuss user testing methods and insights." },
    { type:'open', text:"How do you document design systems for scale?" },
    { type:'open', text:"Share a case of improving task success rate." },
    { type:'open', text:"Describe collaboration with engineering teams." }
  ]
}
const behavioral: Question[] = [
  { type:'open', text:"Tell me about a time you handled conflicting priorities." },
  { type:'open', text:"Describe a failure and what you changed afterward." },
  { type:'open', text:"How do you give and receive feedback effectively?" },
  { type:'open', text:"Share a situation where you influenced without authority." },
  { type:'open', text:"Discuss how you plan and communicate deadlines." }
]
const aptitude: Question[] = [
  { type:'mcq', text:"What is the next number in the sequence 2, 6, 12, 20, ?", options:["30","28","26","24"], correct:1 },
  { type:'mcq', text:"A fair coin is flipped 3 times. Probability of exactly 2 heads?", options:["3/8","1/2","1/4","5/8"], correct:0 },
  { type:'mcq', text:"If A works in 6 days and B in 8 days, together time?", options:["3.4","3.2","3.0","2.9"], correct:1 },
  { type:'mcq', text:"Simplify: log10(1000)", options:["2","3","10","1"], correct:1 },
  { type:'mcq', text:"Speed 60 km/h for 2h then 40 km/h for 1h, average?", options:["50","53.3","60","45"], correct:1 }
]

function evaluate(answer: string) {
  const len = answer.trim().split(/\s+/).length
  const hasMetric = /\b\d+%|\b\d{2,}\b/.test(answer)
  const hasStructure = /(problem|solution|result|impact)/i.test(answer)
  let score = 50
  if (len > 80) score += 15
  if (hasMetric) score += 20
  if (hasStructure) score += 15
  const tips: string[] = []
  if (!hasStructure) tips.push('Use the STAR method (Situation, Task, Action, Result).')
  if (!hasMetric) tips.push('Quantify impact with metrics (% improvement, time saved).')
  if (len < 80) tips.push('Add more detail on actions and outcomes.')
  return { score, tips }
}

export default function MockInterview() {
  const [role, setRole] = useState('Software Engineer')
  const [resumeHint, setResumeHint] = useState('')
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState<any[]>(Array(15).fill(''))
  const personalized: Question[] = resumeHint.trim() ? [
    { type:'open', text:`Tell me about your experience with ${(resumeHint.match(/\b[A-Za-z\-\+\.]{3,}\b/g)||[])[0] || 'a key technology'} and impact.` },
    { type:'open', text:"Which project best demonstrates your strengths and why?" }
  ] : []
  const questions: Question[] = [ ...banks[role], ...behavioral.slice(0,3), ...aptitude.slice(0,2), ...personalized ].slice(0,10)
  const [feedback, setFeedback] = useState<{ scores:number[]; tips:string[]; correct:number } | null>(null)

  const onSubmit = () => {
    const scores: number[] = []
    const tips: string[] = []
    let correct = 0
    questions.forEach((q, i)=>{
      if (q.type==='open') { const r = evaluate(String(answers[i]||'')); scores.push(r.score); tips.push(...r.tips) }
      else { const sel = Number(answers[i]); if (!Number.isNaN(sel)) { correct += sel===q.correct ? 1 : 0 } }
    })
    setFeedback({ scores, tips, correct })
  }

  return (
    <div className="min-h-screen bg-cream">
      <div className="container mx-auto p-6">
        <h1 className="text-3xl font-bold text-maroon mb-6">Mock Interview</h1>
        <Card className="border-none shadow-md">
          <CardHeader>
            <CardTitle>Setup</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4 items-center">
              <label className="text-sm">Role</label>
              <select className="border rounded px-2 py-1" value={role} onChange={(e)=>{ setRole(e.target.value); setStep(0); setAnswers(Array(15).fill('')); setFeedback(null) }}>
                {Object.keys(banks).map(r=> (<option key={r} value={r}>{r}</option>))}
              </select>
            </div>
            <div className="mt-3">
              <label className="text-sm">Resume keywords or summary (optional)</label>
              <Textarea rows={3} placeholder="e.g. React, Node, AWS; led project on analytics" value={resumeHint} onChange={(e)=>{ setResumeHint(e.target.value); setStep(0); setFeedback(null) }} />
            </div>
          </CardContent>
        </Card>

        <Card className="border-none shadow-md mt-6">
          <CardHeader>
            <CardTitle>Question {step+1} / {questions.length}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-3 font-medium">{questions[step].text}</p>
            {questions[step].type==='open' ? (
              <Textarea rows={8} placeholder="Type your answer here..." value={String(answers[step]||'')} onChange={(e)=>{
                const copy = answers.slice(); copy[step] = e.target.value; setAnswers(copy)
              }} />
            ) : (
              <div className="space-y-2">
                {questions[step].options?.map((opt, idx)=> (
                  <label key={idx} className="flex items-center gap-2">
                    <input type="radio" name={`q${step}`} checked={Number(answers[step])===idx} onChange={()=>{
                      const copy = answers.slice(); copy[step] = idx; setAnswers(copy)
                    }} />
                    <span>{opt}</span>
                  </label>
                ))}
              </div>
            )}
            <div className="mt-4 flex gap-2">
              <Button variant="outline" onClick={()=> setStep(Math.max(0, step-1))}>Prev</Button>
              {step < questions.length - 1 ? (
                <Button className="bg-maroon hover:bg-maroon/90" onClick={()=> setStep(step+1)}>Next</Button>
              ) : (
                <Button className="bg-maroon hover:bg-maroon/90" onClick={onSubmit}>Finish</Button>
              )}
            </div>
          </CardContent>
        </Card>

        {feedback && (
          <Card className="border-none shadow-md mt-6">
            <CardHeader>
              <CardTitle>Feedback</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-lg">Average Open-Ended Score: <span className="font-semibold">{Math.round(feedback.scores.reduce((a,b)=>a+b,0)/Math.max(feedback.scores.length,1))}/100</span></p>
              <p className="text-sm text-gray-700">Aptitude Correct: {feedback.correct} / {questions.filter(q=> q.type==='mcq').length}</p>
              <ul className="list-disc list-inside mt-2 text-gray-700">
                {feedback.tips.map((t,i)=> (<li key={i}>{t}</li>))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
