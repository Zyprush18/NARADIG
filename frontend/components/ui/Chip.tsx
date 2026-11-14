'use client'

const toneOf = (s: string) =>
  /succeeded|active|Aktif|^ok$/i.test(s)
    ? 'ok'
    : /failed|rate_limited|expired|gagal/i.test(s)
      ? 'e'
      : /partial|paused/i.test(s)
        ? 'w'
        : ''

export function Chip({ s, tone }: { s: string; tone?: string }) {
  return <span className={'chip ' + (tone ?? toneOf(s))}>{s}</span>
}

/** Asal data: feed nyata vs korpus demo. */
export function Origin({ origin }: { origin?: string }) {
  const mock = origin === 'mock'
  return <span className={'chip ' + (mock ? 'w' : 'ok')}>{mock ? 'Korpus demo' : 'Feed nyata'}</span>
}