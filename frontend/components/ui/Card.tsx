'use client'
import type { ReactNode } from 'react'

export function Card({
  t,
  children,
  dark,
}: {
  t?: string
  children?: ReactNode
  dark?: boolean
}) {
  return (
    <section className={'card ' + (dark ? 'dark' : '')}>
      {t && <h2>{t}</h2>}
      {children}
    </section>
  )
}