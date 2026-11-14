'use client'
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
  type SyntheticEvent,
} from 'react'
import { useRouter } from 'next/navigation'
import { loginRequest } from '../../lib/hooks/useSession'

const EVENT = 'naradig:login'
const DEMO = [
  ['Admin', 'admin@naradig.local'],
  ['Analyst', 'analyst@naradig.local'],
  ['Reviewer', 'reviewer@naradig.local'],
  ['Viewer', 'viewer@naradig.local'],
] as const

/** Pemicu modal login. Anchor (bukan <button>) agar tidak kena aturan global `nav button`. */
export function LoginTrigger({ className, children }: { className?: string; children: ReactNode }) {
  const open = (e: SyntheticEvent) => {
    e.preventDefault()
    window.dispatchEvent(new Event(EVENT))
  }
  return (
    <a
      href="#"
      role="button"
      className={className}
      onClick={open}
      onKeyDown={(e) => {
        if (e.key === ' ') open(e)
      }}
    >
      {children}
    </a>
  )
}

export function LoginModal() {
  const [open, setOpen] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const router = useRouter()
  const cardRef = useRef<HTMLDivElement>(null)
  const emailRef = useRef<HTMLInputElement>(null)
  const openerRef = useRef<HTMLElement | null>(null)

  const close = useCallback(() => {
    setOpen(false)
    setErr('')
    openerRef.current?.focus?.()
  }, [])

  useEffect(() => {
    const onOpen = () => {
      openerRef.current = document.activeElement as HTMLElement | null
      setErr('')
      setOpen(true)
    }
    window.addEventListener(EVENT, onOpen)
    return () => window.removeEventListener(EVENT, onOpen)
  }, [])

  useEffect(() => {
    if (!open) return
    const focus = setTimeout(() => emailRef.current?.focus(), 60)
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        close()
        return
      }
      if (e.key !== 'Tab') return
      const nodes = cardRef.current?.querySelectorAll<HTMLElement>('button,input,a[role="button"]')
      if (!nodes?.length) return
      const f = Array.from(nodes).filter((n) => n.offsetParent !== null)
      if (!f.length) return
      const first = f[0]
      const last = f[f.length - 1]
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault()
        last.focus()
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault()
        first.focus()
      }
    }
    document.addEventListener('keydown', onKey)
    return () => {
      clearTimeout(focus)
      document.removeEventListener('keydown', onKey)
    }
  }, [open, close])

  const submit = async (e: SyntheticEvent) => {
    e.preventDefault()
    if (busy) return
    const em = email.trim().toLowerCase()
    if (!em || !password) return setErr('Isi email dan kata sandi.')
    if (!/^\S+@\S+\.\S+$/.test(em)) return setErr('Format email tidak valid.')
    setBusy(true)
    setErr('')
    try {
      await loginRequest(em, password)
      setOpen(false)
      router.push('/app')
    } catch (x) {
      setErr((x as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div
      className={'l-md' + (open ? ' open' : '')}
      aria-hidden={!open}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) close()
      }}
    >
      <div className="l-mc" role="dialog" aria-modal="true" aria-labelledby="l-mt" ref={cardRef}>
        <button className="l-mx" type="button" aria-label="Tutup" onClick={close}>
          ×
        </button>
        <div className="l-logo" style={{ marginBottom: 4 }}>
          <b />
          NARADIG
        </div>
        <h2 id="l-mt">Masuk</h2>
        <p className="l-sm">Gunakan akun yang diberikan admin Anda.</p>
        {err && (
          <div className="l-merr" role="alert">
            {err}
          </div>
        )}
        <form onSubmit={submit} noValidate style={{ display: 'grid', gap: 15 }}>
          <label className="l-f">
            Email
            <input
              className="l-i"
              ref={emailRef}
              type="email"
              autoComplete="username"
              placeholder="nama@naradig.local"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <label className="l-f">
            Kata sandi
            <span className="l-pw">
              <input
                className="l-i"
                type={showPw ? 'text' : 'password'}
                autoComplete="current-password"
                placeholder="Kata sandi"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button type="button" onClick={() => setShowPw((v) => !v)}>
                {showPw ? 'Sembunyikan' : 'Tampilkan'}
              </button>
            </span>
          </label>
          <button className="l-btn" type="submit" disabled={busy}>
            {busy ? 'Memproses…' : 'Masuk'}
          </button>
        </form>
        <div>
          <p className="l-sm" style={{ margin: '2px 0 8px' }}>
            Akun demo (kata sandi naradig123):
          </p>
          <div className="l-acc">
            {DEMO.map(([label, mail]) => (
              <button
                key={mail}
                type="button"
                onClick={() => {
                  setEmail(mail)
                  setPassword('naradig123')
                  setErr('')
                }}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
        <p className="l-sm">Mode demo: akun hanya untuk percobaan.</p>
      </div>
    </div>
  )
}