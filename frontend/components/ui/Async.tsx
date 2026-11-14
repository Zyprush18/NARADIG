'use client'
import type { ReactNode } from 'react'
import { Card } from './Card'

export const TableWrap = ({ children }: { children: ReactNode }) => (
  <div className="tw">{children}</div>
)

export function Loading({ t = 'Memuat…' }: { t?: string }) {
  return <Card>{t}</Card>
}

export function ErrorBox({ error, retry }: { error: Error; retry?: () => void }) {
  return (
    <Card t="Gagal memuat data">
      <p className="mut">{error.message}</p>
      {retry && (
        <button className="btn sm g" onClick={retry}>
          Coba lagi
        </button>
      )}
    </Card>
  )
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="note">{children}</div>
}