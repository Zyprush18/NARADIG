'use client'
import type { Connector } from '../../lib/types'

/** Konektor yang boleh dipilih sebagai sumber. */
export const availableSources = (list?: Connector[] | null) =>
  (list ?? []).filter((c) => c.available && c.enabled).map((c) => c.id)

export function SourcePicker({
  list,
  value,
  onChange,
}: {
  list?: Connector[] | null
  value: string[]
  onChange: (v: string[]) => void
}) {
  return (
    <div className="row" style={{ margin: '12px 0' }}>
      {(list ?? [])
        .filter((c) => c.available && c.enabled)
        .map((c) => (
          <label
            key={c.id}
            style={{ flexDirection: 'row', alignItems: 'center', display: 'flex', gap: 6 }}
          >
            <input
              type="checkbox"
              style={{ width: 'auto' }}
              checked={value.includes(c.id)}
              onChange={(e) =>
                onChange(
                  e.target.checked ? [...value, c.id] : value.filter((x) => x !== c.id),
                )
              }
            />
            {c.name}
          </label>
        ))}
    </div>
  )
}