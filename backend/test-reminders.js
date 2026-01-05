const { Client } = require('pg')
const fetch = global.fetch || ((...args)=>import('node-fetch').then(({default: f})=>f(...args)))

async function run() {
  const api = process.env.API_URL || 'http://localhost:8001'
  const connectionString = process.env.DATABASE_URL || 'postgresql://user:Swapnil%402102@localhost:5432/Project_2'
  const db = new Client({ connectionString })
  await db.connect()
  try {
    const u1 = await db.query("INSERT INTO users (email, role, created_at) VALUES ('test1@example.com','STUDENT',NOW()) RETURNING id")
    const u2 = await db.query("INSERT INTO users (email, role, created_at) VALUES ('test2@example.com','STUDENT',NOW()) RETURNING id")
    const e = await db.query("INSERT INTO events (title, location, date, event_time, status, created_at, updated_at) VALUES ('Test Event','Hall', NOW()::date, '10:00', 'Upcoming', NOW(), NOW()) RETURNING id")
    const eventId = e.rows[0].id
    await db.query('INSERT INTO event_registrations (event_id, user_id, registered_at) VALUES ($1,$2,NOW()), ($1,$3,NOW())', [eventId, u1.rows[0].id, u2.rows[0].id])

    const r = await fetch(`${api}/api/v1/tpo/events/${eventId}/reminders`, { method: 'POST' })
    const rj = await r.json()
    console.log('Reminder response:', r.status, rj)

    const logs = await db.query('SELECT channel, status, COUNT(*)::int AS c FROM reminder_logs WHERE event_id = $1 GROUP BY channel, status', [eventId])
    console.log('Reminder logs:', logs.rows)

    const m = await fetch(`${api}/api/v1/tpo/events/${eventId}`, { method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ status:'Completed' }) })
    const mj = await m.json()
    console.log('Mark complete response:', m.status, mj.status)

    const audits = await db.query('SELECT old_status, new_status FROM event_audit_logs WHERE event_id = $1 ORDER BY changed_at DESC', [eventId])
    console.log('Audit logs:', audits.rows)
  } catch (e) {
    console.error('Test failed:', e && e.message || e)
    process.exitCode = 1
  } finally {
    await db.end()
  }
}

run()
