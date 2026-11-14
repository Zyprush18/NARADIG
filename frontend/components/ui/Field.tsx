'use client'
import type { ReactNode } from 'react'

/** Label + kontrol. Nilai selalu dari state pemanggil (bukan DOM, F4). */
export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label>
      {label}
      {children}
    </label>
  )
}