import { Component } from 'react'

import Button from './ui/Button'
import Card from './ui/Card'
import './ErrorBoundary.css'

export default class ErrorBoundary extends Component {
  state = { hasError: false }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    console.error('Erro não tratado na interface:', error, errorInfo)
  }

  handleReload = () => {
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="error-boundary" role="alert">
          <Card title="Não foi possível carregar a aplicação">
            <p className="error-boundary__message">
              Ocorreu um erro inesperado. Recarregue a página para tentar novamente.
            </p>
            <Button onClick={this.handleReload}>Recarregar página</Button>
          </Card>
        </main>
      )
    }

    return this.props.children
  }
}
