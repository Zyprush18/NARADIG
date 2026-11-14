'use client'
import { Component, type ReactNode } from 'react'

interface State {
  error: Error | null
}

/** Satu field undefined tidak boleh membuat seluruh app blank (F9). */
export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  render() {
    if (!this.state.error) return this.props.children
    return (
      <div className="login">
        <div className="logo">
          <i>N</i>NARADIG
        </div>
        <div className="flash err" role="alert">
          Terjadi kesalahan pada tampilan: {this.state.error.message}
        </div>
        <button className="btn" onClick={() => this.setState({ error: null })}>
          Muat ulang tampilan
        </button>
      </div>
    )
  }
}