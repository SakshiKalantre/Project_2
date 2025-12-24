"use client"

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import LogoutButton from '@/components/LogoutButton'
import { useUser } from '@clerk/nextjs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { 
  FileText, 
  Upload, 
  Briefcase, 
  Calendar, 
  Bell, 
  Edit,
  Save,
  X
} from 'lucide-react'

type JobListing = {
  id: number
  title: string
  company: string
  location: string
  type?: string
  job_url?: string
}

type EventItem = {
  id: number
  title: string
  location: string
  status?: string
  date?: string
  time?: string
  category?: string
  form_url?: string
}

type NotificationItem = {
  id: number
  title: string
  message: string
  time: string
  read: boolean
}

export default function StudentDashboard() {
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://project-2-payz.onrender.com'
  const { user } = useUser()
  const [activeTab, setActiveTab] = useState('profile')
  const [isEditing, setIsEditing] = useState(false)
  const [userId, setUserId] = useState<number | null>(null)
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [certificateFile, setCertificateFile] = useState<File | null>(null)
  const [userFiles, setUserFiles] = useState<Array<any>>([])
  const [resumeProgress, setResumeProgress] = useState<number>(0)
  const [certProgress, setCertProgress] = useState<number>(0)
  const [profile, setProfile] = useState({
    name: '',
    email: '',
    phone: '',
    degree: '',
    year: '',
    skills: '',
    about: ''
  })
  const [jobListings, setJobListings] = useState<JobListing[]>([])
  const [events, setEvents] = useState<EventItem[]>([])
  const [notifications, setNotifications] = useState<NotificationItem[]>([])

  // Fetch data from our API
  useEffect(() => {
    const fetchData = async () => {
      try {
        let email: string | null = null
        let displayName: string | null = null
        let uidLocal: number | null = null
        if (user) {
          // Clerk user
          // @ts-ignore
          displayName = [user.firstName, user.lastName].filter(Boolean).join(' ')
          // @ts-ignore
          email = user.primaryEmailAddress?.emailAddress || user.emailAddresses?.[0]?.emailAddress || null
          if (email && typeof window !== 'undefined') {
            localStorage.setItem('currentUser', JSON.stringify({ email, role: 'STUDENT' }))
          }
        }
        const stored = typeof window !== 'undefined' ? localStorage.getItem('currentUser') : null
        const current = stored ? JSON.parse(stored) : null
        const storedId: number | null = current?.id || null
        if (!email) email = current?.email || null
        if (!email && !storedId) {
          alert('Please sign up first to access the dashboard')
          if (typeof window !== 'undefined') window.location.href = '/sign-up'
          return
        }

        let userRes: Response | null = null
        if (storedId) {
          const byId = await fetch(`${API_BASE}/api/v1/users/${storedId}?t=${Date.now()}`, { cache: 'no-store' })
          if (byId.ok) {
            const u = await byId.json()
            uidLocal = u.id
            setUserId(u.id)
            let n = (`${u.first_name || ''} ${u.last_name || ''}`.trim())
            if (!n) {
              try {
                const pendRaw = typeof window !== 'undefined' ? localStorage.getItem('pendingUser') : null
                const pend = pendRaw ? JSON.parse(pendRaw) : null
                const full = (pend?.fullName || '').trim()
                if (full) {
                  const parts = full.split(' ')
                  const first = parts[0] || null
                  const last = parts.slice(1).join(' ') || null
                  await fetch(`${API_BASE}/api/v1/users/${u.id}`, { method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ first_name: first, last_name: last }) })
                  n = full
                }
              } catch {}
            }
            setProfile(prev => ({ ...prev, name: n, email: u.email }))
            const pRes = await fetch(`${API_BASE}/api/v1/users/${u.id}/profile?t=${Date.now()}`, { cache: 'no-store' })
            if (pRes.ok) {
              const p = await pRes.json()
              setProfile(prev => ({ ...prev, phone: p.phone || '', degree: p.degree || '', year: p.year || '', skills: p.skills || '', about: p.about || '' }))
            }
            try { if (typeof window !== 'undefined') localStorage.setItem('currentUser', JSON.stringify({ email: u.email, id: u.id, role: 'STUDENT' })) } catch {}
          }
        }
        let userData: any | null = null
        if (!uidLocal && email) {
          const r = await fetch(`${API_BASE}/api/v1/users/by-email/${encodeURIComponent(email)}?t=${Date.now()}`, { cache: 'no-store' })
          if (r.ok) {
            userData = await r.json()
          }
        }
        if (!uidLocal && userData) {
          uidLocal = userData.id
          setUserId(userData.id)
          let dbName = (`${userData.first_name || ''} ${userData.last_name || ''}`.trim())
          if (!dbName) {
            try {
              const pendRaw = typeof window !== 'undefined' ? localStorage.getItem('pendingUser') : null
              const pend = pendRaw ? JSON.parse(pendRaw) : null
              const full = (pend?.fullName || '').trim()
              if (full) {
                const parts = full.split(' ')
                const first = parts[0] || null
                const last = parts.slice(1).join(' ') || null
                await fetch(`${API_BASE}/api/v1/users/${userData.id}`, { method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ first_name: first, last_name: last }) })
                dbName = full
              }
            } catch {}
          }
          setProfile(prev => ({
            ...prev,
            name: dbName,
            email: userData.email,
          }))
          try { if (typeof window !== 'undefined') localStorage.setItem('currentUser', JSON.stringify({ email: userData.email, id: userData.id, name: dbName, role: 'STUDENT' })) } catch {}
          const profileDetailsResponse = await fetch(`${API_BASE}/api/v1/users/${userData.id}/profile?t=${Date.now()}`, { cache: 'no-store' })
          if (profileDetailsResponse.ok) {
            const profileData = await profileDetailsResponse.json()
            setProfile(prev => ({
              ...prev,
              phone: profileData.phone || '',
              degree: profileData.degree || '',
              year: profileData.year || '',
              skills: profileData.skills || '',
              about: profileData.about || ''
            }))
          }
          try { if (typeof window !== 'undefined') localStorage.setItem('currentUser', JSON.stringify({ email: userData.email, id: userData.id, role: 'STUDENT' })) } catch {}
          try {
            const filesRes = await fetch(`/api/files/by-user/${userData.id}`, { cache:'no-store' })
            if (filesRes.ok) {
              const files = await filesRes.json()
              setUserFiles(files)
            }
          } catch {}
        } else if (!uidLocal) {
          alert('Your email is not registered. Please sign up to continue.')
          if (typeof window !== 'undefined') window.location.href = '/sign-up'
          return
        }

        const jobsResponse = await fetch(`${API_BASE}/api/v1/jobs`)
        if (jobsResponse.ok) {
          const jobsData = await jobsResponse.json()
          setJobListings(jobsData)
        }

        const eventsResponse = await fetch(`${API_BASE}/api/v1/events`)
        if (eventsResponse.ok) {
          const eventsData = await eventsResponse.json()
          setEvents(eventsData)
        }

        try {
          if (uidLocal) {
            const notifRes = await fetch(`/api/notifications/by-user/${uidLocal}`, { cache:'no-store' })
            if (notifRes.ok) {
              const notif = await notifRes.json()
              setNotifications(notif.map((n:any)=>({ id: n.id, title: n.title, message: n.message, time: new Date(n.created_at).toLocaleString(), read: n.is_read })))
            }
          }
        } catch {}
      } catch (error) {
        console.error('Error fetching data:', error)
      }
    }

    fetchData()
  }, [user])

  useEffect(() => {
    const refreshNotifications = async () => {
      try {
        if (activeTab === 'notifications' && userId) {
          const res = await fetch(`/api/notifications/by-user/${userId}`, { cache:'no-store' })
          if (res.ok) {
            const rows = await res.json()
            setNotifications(rows.map((n:any)=>({ id: n.id, title: n.title, message: n.message, time: new Date(n.created_at).toLocaleString(), read: n.is_read })))
          }
        }
      } catch {}
    }
    refreshNotifications()
  }, [activeTab, userId])

  useEffect(() => {
    const refreshJobs = async () => {
      try {
        if (activeTab === 'jobs') {
          const res = await fetch(`${API_BASE}/api/v1/jobs`)
          if (res.ok) {
            const rows = await res.json()
            setJobListings(rows)
          }
        }
      } catch {}
    }
    refreshJobs()
  }, [activeTab])

  useEffect(() => {
    const refreshEvents = async () => {
      try {
        if (activeTab === 'events') {
          const res = await fetch(`${API_BASE}/api/v1/events`)
          if (res.ok) {
            const rows = await res.json()
            setEvents(rows)
          }
        }
      } catch {}
    }
    refreshEvents()
  }, [activeTab])

  useEffect(() => {
    const applyRole = async () => {
      try {
        const role = 'STUDENT'
        if (user && (user.unsafeMetadata?.role !== role)) {
          await user.update({ unsafeMetadata: { role } })
        }
      } catch {}
    }
    applyRole()
  }, [user])

  const handleSaveProfile = async () => {
    try {
      if (!userId) return
      const cleanName = (profile.name || '').trim().replace(/\s+/g, ' ')
      if (!cleanName) { setIsEditing(false); return }
      const parts = cleanName.split(' ')
      const firstName = parts[0] || ''
      const lastName = parts.slice(1).join(' ')

      await fetch(`${API_BASE}/api/v1/users/${userId}/profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: profile.phone || null,
          degree: profile.degree || null,
          year: profile.year || null,
          skills: profile.skills || null,
          about: profile.about || null,
          
        })
      })
      await fetch(`${API_BASE}/api/v1/users/${userId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ first_name: firstName || null, last_name: lastName || null, phone_number: profile.phone || null })
      })
      const refreshed = await fetch(`${API_BASE}/api/v1/users/${userId}?t=${Date.now()}`, { cache: 'no-store' })
      if (refreshed.ok) {
        const u = await refreshed.json()
        const finalName = (`${u.first_name || ''} ${u.last_name || ''}`.trim()) || ''
        setProfile(prev => ({ ...prev, name: finalName, email: u.email }))
        try { if (typeof window !== 'undefined') localStorage.setItem('currentUser', JSON.stringify({ email: u.email, id: u.id, role: 'STUDENT' })) } catch {}
      }
      const refreshedProfile = await fetch(`${API_BASE}/api/v1/users/${userId}/profile?t=${Date.now()}`, { cache: 'no-store' })
      if (refreshedProfile.ok) {
        const p = await refreshedProfile.json()
        setProfile(prev => ({
          ...prev,
          phone: p.phone || '',
          degree: p.degree || '',
          year: p.year || '',
          skills: p.skills || '',
          about: p.about || ''
        }))
      }
      setIsEditing(false)
    } catch (e) {
      setIsEditing(false)
    }
  }

  const toBase64 = (file: File) => new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onprogress = (e) => {
      if (e.lengthComputable) {
        const percent = Math.round((e.loaded / e.total) * 50) // reading part contributes 50%
        setResumeProgress((prev)=> resumeFile === file ? percent : prev)
        setCertProgress((prev)=> certificateFile === file ? percent : prev)
      }
    }
    reader.onload = () => {
      const res = String(reader.result || '')
      const base64 = res.includes('base64,') ? res.split('base64,')[1] : res
      resolve(base64)
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })

  const postJSONWithProgress = (url: string, payload: any, setProgress: (n:number)=>void) => new Promise<Response>((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', url)
    xhr.setRequestHeader('Content-Type', 'application/json')
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        const percent = 50 + Math.round((e.loaded / e.total) * 50) // upload contributes remaining 50%
        setProgress(percent)
      }
    }
    xhr.onreadystatechange = () => {
      if (xhr.readyState === 4) {
        setProgress(100)
        resolve(new Response(xhr.responseText, { status: xhr.status }))
      }
    }
    xhr.onerror = () => reject(new Error('Network error'))
    xhr.send(JSON.stringify(payload))
  })

  const postFormDataWithProgress = (url: string, form: FormData, setProgress: (n:number)=>void) => new Promise<Response>((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', url)
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        const percent = Math.round((e.loaded / e.total) * 100)
        setProgress(percent)
      }
    }
    xhr.onreadystatechange = () => {
      if (xhr.readyState === 4) {
        resolve(new Response(xhr.responseText, { status: xhr.status }))
      }
    }
    xhr.onerror = () => reject(new Error('Network error'))
    xhr.send(form)
  })

  const openFile = async (fileId: number) => {
    try {
      const info = await fetch(`${API_BASE}/api/v1/files/${fileId}`)
      if (!info.ok) { alert('Unable to load file information'); return }
      const meta = await info.json()

      // Try presigned URL first
      try {
        const pres = await fetch(`${API_BASE}/api/v1/files/${fileId}/presigned`)
        if (pres.ok) {
          const { url } = await pres.json()
          const w = window.open(url, '_blank')
          if (!w) { const a=document.createElement('a'); a.href=url; a.target='_blank'; document.body.appendChild(a); a.click(); a.remove() }
          return
        }
      } catch {}

      // Fallback to canonical file_url if present
      if (meta.file_url && typeof meta.file_url === 'string') {
        const url = meta.file_url
        const w = window.open(url, '_blank')
        if (!w) { const a=document.createElement('a'); a.href=url; a.target='_blank'; document.body.appendChild(a); a.click(); a.remove() }
        return
      }

      // Final fallback: backend download route
      const url = `${API_BASE}/api/v1/files/${fileId}/download`
      const w = window.open(url, '_blank')
      if (!w) { const a=document.createElement('a'); a.href=url; a.target='_blank'; document.body.appendChild(a); a.click(); a.remove() }
    } catch (e) {
      alert('Failed to open file. Please try again.')
    }
  }

  const handleResumeUpload = async (file: File | null) => {
    try {
      if (!userId || !file) return
      const form = new FormData()
      form.append('user_id', String(userId))
      form.append('file', file)
      const res = await postFormDataWithProgress(`${API_BASE}/api/v1/files/resumes`, form, setResumeProgress)
      if (!res.ok) throw new Error('Failed to upload resume')
      try {
        if (userId) {
          const filesRes = await fetch(`/api/files/by-user/${userId}`, { cache:'no-store' })
          if (filesRes.ok) {
            const files = await filesRes.json()
            setUserFiles(files)
          }
        }
      } catch {}
      setResumeFile(null)
      setResumeProgress(0)
    } catch (e) {}
  }
  const handleCertificateUpload = async (file: File | null, title: string) => {
    try {
      if (!userId || !file) return
      const form = new FormData()
      form.append('user_id', String(userId))
      form.append('title', title)
      form.append('file', file)
      const res = await postFormDataWithProgress(`${API_BASE}/api/v1/files/certificates`, form, setCertProgress)
      if (!res.ok) throw new Error('Failed to upload certificate')
      try {
        if (userId) {
          const filesRes = await fetch(`/api/files/by-user/${userId}`, { cache:'no-store' })
          if (filesRes.ok) {
            const files = await filesRes.json()
            setUserFiles(files)
          }
        }
      } catch {}
      setCertificateFile(null)
      setCertProgress(0)
    } catch (e) {}
  }

  return (
    <div className="min-h-screen bg-cream">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <div className="bg-maroon w-10 h-10 rounded-full"></div>
            <span className="text-2xl font-bold text-maroon">PrepSphere</span>
          </div>
          
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600">Welcome, {profile.name || 'Student'}</span>
            <div className="bg-gray-200 border-2 border-dashed rounded-xl w-10 h-10" />
            <LogoutButton />
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row gap-8">
          {/* Sidebar */}
          <div className="md:w-1/4">
            <Card className="border-none shadow-md">
              <CardHeader>
                <CardTitle className="text-lg">Dashboard</CardTitle>
              </CardHeader>
              <CardContent>
                <nav className="space-y-2">
                  <Button 
                    variant={activeTab === 'profile' ? 'default' : 'ghost'} 
                    className={`w-full justify-start ${activeTab === 'profile' ? 'bg-maroon hover:bg-maroon/90' : ''}`}
                    onClick={() => setActiveTab('profile')}
                  >
                    <Edit className="mr-2 h-4 w-4" />
                    Profile
                  </Button>
                  <Button 
                    variant={activeTab === 'jobs' ? 'default' : 'ghost'} 
                    className={`w-full justify-start ${activeTab === 'jobs' ? 'bg-maroon hover:bg-maroon/90' : ''}`}
                    onClick={() => setActiveTab('jobs')}
                  >
                    <Briefcase className="mr-2 h-4 w-4" />
                    Job Listings
                  </Button>
                  <Button 
                    variant={activeTab === 'events' ? 'default' : 'ghost'} 
                    className={`w-full justify-start ${activeTab === 'events' ? 'bg-maroon hover:bg-maroon/90' : ''}`}
                    onClick={() => setActiveTab('events')}
                  >
                    <Calendar className="mr-2 h-4 w-4" />
                    Events
                  </Button>
                  <Button 
                    variant={activeTab === 'notifications' ? 'default' : 'ghost'} 
                    className={`w-full justify-start ${activeTab === 'notifications' ? 'bg-maroon hover:bg-maroon/90' : ''}`}
                    onClick={() => setActiveTab('notifications')}
                  >
                    <Bell className="mr-2 h-4 w-4" />
                    Notifications
                  </Button>
                  <Button 
                    variant={activeTab === 'ai-tools' ? 'default' : 'ghost'} 
                    className={`w-full justify-start ${activeTab === 'ai-tools' ? 'bg-maroon hover:bg-maroon/90' : ''}`}
                    onClick={() => setActiveTab('ai-tools')}
                  >
                    <Briefcase className="mr-2 h-4 w-4" />
                    AI Tools
                  </Button>
                </nav>
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="md:w-3/4">
            {activeTab === 'profile' && (
              <Card className="border-none shadow-md">
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <CardTitle>My Profile</CardTitle>
                    {isEditing ? (
                      <div className="space-x-2">
                        <Button size="sm" onClick={handleSaveProfile} className="bg-maroon hover:bg-maroon/90">
                          <Save className="mr-2 h-4 w-4" />
                          Save
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => setIsEditing(false)}>
                          <X className="mr-2 h-4 w-4" />
                          Cancel
                        </Button>
                      </div>
                    ) : (
                      <Button size="sm" onClick={() => setIsEditing(true)} className="bg-maroon hover:bg-maroon/90">
                        <Edit className="mr-2 h-4 w-4" />
                        Edit
                      </Button>
                    )}
                  </div>
                  <CardDescription>Manage your personal information</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="name">Full Name</Label>
                        {isEditing ? (
                          <Input 
                            id="name" 
                            value={profile.name} 
                            onChange={(e) => setProfile({...profile, name: e.target.value})} 
                          />
                        ) : (
                          <p className="mt-1">{profile.name || (typeof window !== 'undefined' ? ((JSON.parse(localStorage.getItem('currentUser')||'{}')?.name) || ((profile.email||'').split('@')[0]||'')) : '')}</p>
                        )}
                      </div>
                      
                      <div>
                        <Label>Registered Email</Label>
                        <p className="mt-1">{profile.email}</p>
                      </div>
                      
                      
                      <div>
                        <Label htmlFor="phone">Phone</Label>
                        {isEditing ? (
                          <Input 
                            id="phone" 
                            value={profile.phone} 
                            onChange={(e) => setProfile({...profile, phone: e.target.value})} 
                          />
                        ) : (
                          <p className="mt-1">{profile.phone || 'Not provided'}</p>
                        )}
                      </div>
                      
                      <div>
                        <Label htmlFor="degree">Degree</Label>
                        {isEditing ? (
                          <Input 
                            id="degree" 
                            value={profile.degree} 
                            onChange={(e) => setProfile({...profile, degree: e.target.value})} 
                          />
                        ) : (
                          <p className="mt-1">{profile.degree || 'Not provided'}</p>
                        )}
                      </div>
                    </div>
                    
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="year">Year</Label>
                        {isEditing ? (
                          <Input 
                            id="year" 
                            value={profile.year} 
                            onChange={(e) => setProfile({...profile, year: e.target.value})} 
                          />
                        ) : (
                          <p className="mt-1">{profile.year || 'Not provided'}</p>
                        )}
                      </div>
                      
                      <div>
                        <Label htmlFor="skills">Skills</Label>
                        {isEditing ? (
                          <Textarea 
                            id="skills" 
                            value={profile.skills} 
                            onChange={(e) => setProfile({...profile, skills: e.target.value})} 
                            rows={3}
                          />
                        ) : (
                          <p className="mt-1">{profile.skills || 'Not provided'}</p>
                        )}
                      </div>
                      
                      <div>
                        <Label htmlFor="about">About Me</Label>
                        {isEditing ? (
                          <Textarea 
                            id="about" 
                            value={profile.about} 
                            onChange={(e) => setProfile({...profile, about: e.target.value})} 
                            rows={4}
                          />
                        ) : (
                          <p className="mt-1">{profile.about || 'Not provided'}</p>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-8">
                    <h3 className="text-lg font-semibold mb-4">Documents</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <Card>
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center">
                              <FileText className="h-8 w-8 text-maroon mr-3" />
                              <div>
                                <h4 className="font-medium">Resume</h4>
                                <p className="text-sm text-gray-500">PDF, 2.4 MB</p>
                              </div>
                            </div>
                            <Button size="sm" variant="outline" onClick={()=>{
                              const latest = userFiles.find((x)=> x.file_type==='resume')
                              if (latest) {
                                openFile(latest.id)
                              } else alert('No resume uploaded yet')
                            }}>View</Button>
                          </div>
                        </CardContent>
                      </Card>
                      
                      
                    </div>
                    
                    <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="resumeUpload">Upload Resume</Label>
                        <div className="mt-2 flex items-center gap-2">
                          <input id="resumeUpload" type="file" onChange={(e)=>{
                            const f=e.target.files?.[0]||null;
                            if (!f) { setResumeFile(null); return }
                            if (f.type !== 'application/pdf') { alert('Only PDF files are accepted'); e.currentTarget.value=''; setResumeFile(null); return }
                            if (f.size > 10*1024*1024) { alert('Max file size is 10 MB'); e.currentTarget.value=''; setResumeFile(null); return }
                            setResumeFile(f)
                          }} />
                          <Button size="sm" onClick={()=>handleResumeUpload(resumeFile)} className="bg-maroon hover:bg-maroon/90">Upload</Button>
                        </div>
                        <p className="text-xs text-gray-600 mt-1">Note: Only PDF files up to 10 MB are accepted.</p>
                        {resumeProgress > 0 && (
                          <div className="mt-2 h-2 w-full bg-gray-200 rounded">
                            <div className="h-2 bg-maroon rounded" style={{ width: `${resumeProgress}%` }} />
                            <p className="text-xs text-gray-600 mt-1">{resumeProgress}%</p>
                          </div>
                        )}
                      </div>
                      
                    </div>

                    <div className="mt-6">
                      <h4 className="font-medium mb-2">Your Uploaded Files</h4>
                      <div className="space-y-2">
                        {userFiles.filter(f=>f.file_type==='resume').map((f)=> (
                          <div key={f.id} className="flex items-center justify-between text-sm">
                            <span>{f.filename || f.title} <span className="ml-2 text-gray-500">({f.file_type})</span></span>
                            <div className="flex items-center gap-2">
                              <Button size="sm" variant="outline" onClick={()=> openFile(f.id)}>View</Button>
                            </div>
                          </div>
                        ))}
                        {userFiles.filter(f=>f.file_type==='resume').length === 0 && <p className="text-gray-500 text-sm">No resumes uploaded yet</p>}
                      </div>
                      
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
            
            {activeTab === 'jobs' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold text-maroon">Job Listings</h2>
                </div>
                {jobListings.length === 0 ? (
                  <p className="text-gray-600">No job listings available. Jobs will appear here when the TPO posts them.</p>
                ) : (
                  <div className="grid grid-cols-1 gap-6">
                    {jobListings.map((job) => (
                      <Card key={job.id} className="border-none shadow-md hover:shadow-lg transition-shadow">
                        <CardContent className="p-6">
                          <div className="flex justify-between">
                            <div>
                              <h3 className="text-xl font-semibold">{job.title}</h3>
                              <p className="text-gray-600">{job.company} • {job.location}</p>
                            </div>
                            <Badge variant="secondary" className="bg-gold text-maroon">
                              {job.type}
                            </Badge>
                          </div>
                          <div className="mt-6 flex space-x-3">
                            <Button className="bg-maroon hover:bg-maroon/90" onClick={async()=>{
                              try {
                                const stored = typeof window !== 'undefined' ? localStorage.getItem('currentUser') : null
                                const current = stored ? JSON.parse(stored) : null
                                const userRes = await fetch(`${API_BASE}/api/v1/users/by-email/${encodeURIComponent(current?.email)}`)
                                if (userRes.ok) {
                                  const u = await userRes.json()
                                  await fetch(`${API_BASE}/api/v1/jobs/${job.id}/apply`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ user_id: u.id }) })
                                  alert('Applied successfully')
                                  if (job.job_url) {
                                    const w = window.open(job.job_url, '_blank')
                                    if (!w) { const a=document.createElement('a'); a.href=job.job_url; a.target='_blank'; document.body.appendChild(a); a.click(); a.remove() }
                                  }
                                }
                              } catch { alert('Failed to apply') }
                            }}>Apply Now</Button>
                            {job.job_url && (
                              <Button variant="outline" onClick={()=>{ const url = job.job_url!; const w = window.open(url, '_blank'); if (!w) { const a=document.createElement('a'); a.href=url; a.target='_blank'; document.body.appendChild(a); a.click(); a.remove() } }}>Open Job Link</Button>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            )}
            
            {activeTab === 'events' && (
              <div>
                <h2 className="text-2xl font-bold text-maroon mb-6">Events</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {events.map((event) => (
                    <Card key={event.id} className="border-none shadow-md hover:shadow-lg transition-shadow">
                      <CardContent className="p-6">
                        <div className="flex justify-between items-start">
                          <div>
                            <h3 className="text-xl font-semibold">{event.title}</h3>
                            <p className="text-gray-600 mt-2">{event.location}</p>
                          </div>
                          <Badge variant="secondary" className={
                            (event.status||'Upcoming')==='Cancelled' ? 'bg-red-100 text-red-700' :
                            (event.status||'Upcoming')==='Completed' ? 'bg-green-100 text-green-800' :
                            'bg-gold text-maroon'
                          }>
                            {event.status || 'Upcoming'}
                          </Badge>
                        </div>
                        
                        <div className="mt-4 flex flex-wrap gap-4">
                          <div className="flex items-center text-gray-600">
                            <Calendar className="mr-2 h-4 w-4" />
                            <span>{event.date}</span>
                          </div>
                          <div className="flex items-center text-gray-600">
                            <Calendar className="mr-2 h-4 w-4" />
                            <span>{event.time}</span>
                          </div>
                          {event.category && (
                            <div className="flex items-center text-gray-600">
                              <Badge className="bg-gray-100 text-gray-800">{event.category}</Badge>
                            </div>
                          )}
                          {event.form_url && (
                            <div className="flex items-center text-gray-600">
                              <a
                                className="underline text-maroon"
                                href={event.form_url}
                                target="_blank"
                                rel="noreferrer"
                                onClick={async (e)=>{
                                  try {
                                    e.preventDefault()
                                    const stored = typeof window !== 'undefined' ? localStorage.getItem('currentUser') : null
                                    const current = stored ? JSON.parse(stored) : null
                                    const userRes = await fetch(`${API_BASE}/api/v1/users/by-email/${encodeURIComponent(current?.email)}`)
                                    if (userRes.ok) {
                                      const u = await userRes.json()
                                      await fetch(`${API_BASE}/api/v1/events/${event.id}/register`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ user_id: u.id, email: current?.email, clerkUserId: (user as any)?.id || null }) })
                                    }
                                  } catch {}
                                  const url = event.form_url!
                                  const w = window.open(url, '_blank')
                                  if (!w) { const a=document.createElement('a'); a.href=url; a.target='_blank'; document.body.appendChild(a); a.click(); a.remove() }
                                }}
                              >Google Form</a>
                            </div>
                          )}
                        </div>
                        
                        <div className="mt-6">
                          <Button className="w-full bg-maroon hover:bg-maroon/90" disabled={(event.status||'Upcoming')!=='Upcoming'} onClick={async()=>{
                            try {
                              const stored = typeof window !== 'undefined' ? localStorage.getItem('currentUser') : null
                              const current = stored ? JSON.parse(stored) : null
                              const userRes = await fetch(`${API_BASE}/api/v1/users/by-email/${encodeURIComponent(current?.email)}`)
                              if (userRes.ok) {
                                const u = await userRes.json()
                                // Open form first to ensure student gets redirected
                                if (event.form_url) {
                                  const w = window.open(event.form_url, '_blank')
                                  if (!w) { const a=document.createElement('a'); a.href=event.form_url; a.target='_blank'; document.body.appendChild(a); a.click(); a.remove() }
                                }
                                const payload = { user_id: u.id, email: current?.email, clerkUserId: (user as any)?.id || null }
                                let r = await fetch(`${API_BASE}/api/v1/events/${event.id}/register`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) })
                                if (!r.ok) {
                                  // Fallback: try with email only
                                  const payload2 = { email: current?.email }
                                  r = await fetch(`${API_BASE}/api/v1/events/${event.id}/register`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload2) })
                                  if (!r.ok) {
                                    try { const t = await r.text(); console.error('Register failed:', t) } catch {}
                                  }
                                }
                              }
                            } catch { alert('Failed to register') }
                          }}>Register</Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}
            
            {activeTab === 'notifications' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold text-maroon">Notifications</h2>
                  <Button variant="outline">Mark all as read</Button>
                </div>
                
                <div className="space-y-4">
                  {notifications.map((notification) => (
                    <Card 
                      key={notification.id} 
                      className={`border-none shadow-md ${!notification.read ? 'border-l-4 border-maroon' : ''}`}
                    >
                      <CardContent className="p-6">
                        <div className="flex justify-between">
                          <div>
                            <h3 className="text-lg font-semibold">{notification.title}</h3>
                            <p className="text-gray-600 mt-1">{notification.message}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm text-gray-500">{notification.time}</p>
                            {!notification.read && (
                              <Badge variant="secondary" className="mt-2 bg-maroon text-white">
                                New
                              </Badge>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}
            
            {activeTab === 'ai-tools' && (
              <div>
                <h2 className="text-2xl font-bold text-maroon mb-6">AI Career Tools</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card className="border-none shadow-md">
                    <CardHeader>
                      <CardTitle className="flex items-center">
                        
                        Resume Scoring
                      </CardTitle>
                      <CardDescription>
                        Get instant feedback on your resume with AI-powered analysis
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <p className="mb-4">
                        Upload your resume to receive a detailed analysis of your strengths and areas for improvement.
                      </p>
                      <Button className="w-full bg-maroon hover:bg-maroon/90">
                        Launch Resume Scorer
                      </Button>
                    </CardContent>
                  </Card>
                  
                  <Card className="border-none shadow-md">
                    <CardHeader>
                      <CardTitle className="flex items-center">
                        
                        Mock Interview
                      </CardTitle>
                      <CardDescription>
                        Practice interviews with our AI-powered interviewer
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <p className="mb-4">
                        Prepare for real interviews with personalized questions and feedback.
                      </p>
                      <Button className="w-full bg-maroon hover:bg-maroon/90">
                        Start Mock Interview
                      </Button>
                    </CardContent>
                  </Card>
                </div>
                
                <div className="mt-8">
                  <Card className="border-none shadow-md">
                    <CardHeader>
                      <CardTitle>How to Use AI Tools</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ol className="list-decimal list-inside space-y-2">
                        <li>Select the tool you want to use from above</li>
                        <li>Click the "Launch" button to open the tool in a new window</li>
                        <li>Follow the on-screen instructions to complete your assessment</li>
                        <li>Review your results and recommendations</li>
                        <li>Save or download your results for future reference</li>
                      </ol>
                    </CardContent>
                  </Card>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
