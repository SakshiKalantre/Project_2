"use client"

import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'

const banks: Record<string, string[]> = {
  "Software Engineer": [
    "Explain a recent project where you improved performance.",
    "How do you design scalable APIs?",
    "Describe a time you resolved a production incident.",
    "What are your favorite testing strategies?",
    "Walk through code you’re proud of and why."
  ],
  "Data Analyst": [
    "Share a dataset you analyzed and key insights.",
    "How do you handle missing or noisy data?",
    "Describe a dashboard you built and decisions it enabled.",
    "Which statistical tests do you commonly use and when?",
    "Tell me about a time you automated reporting."
  ]
}

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
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState<string[]>(Array(5).fill(''))
  const questions = banks[role]
  const [feedback, setFeedback] = useState<{ scores:number[]; tips:string[] } | null>(null)

  const onSubmit = () => {
    const scores: number[] = []
    const tips: string[] = []
    answers.forEach(a=>{ const r = evaluate(a); scores.push(r.score); tips.push(...r.tips) })
    setFeedback({ scores, tips })
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
              <select className="border rounded px-2 py-1" value={role} onChange={(e)=>{ setRole(e.target.value); setStep(0); setAnswers(Array(5).fill('')); setFeedback(null) }}>
                {Object.keys(banks).map(r=> (<option key={r} value={r}>{r}</option>))}
              </select>
            </div>
          </CardContent>
        </Card>

        <Card className="border-none shadow-md mt-6">
          <CardHeader>
            <CardTitle>Question {step+1} / {questions.length}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-3 font-medium">{questions[step]}</p>
            <Textarea rows={8} placeholder="Type your answer here..." value={answers[step]} onChange={(e)=>{
              const copy = answers.slice(); copy[step] = e.target.value; setAnswers(copy)
            }} />
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
              <p className="text-lg">Average Score: <span className="font-semibold">{Math.round(feedback.scores.reduce((a,b)=>a+b,0)/feedback.scores.length)}/100</span></p>
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
