import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from './context/AuthContext'
import { WebSocketProvider } from './context/WebSocketContext'
import './index.css'
import App from './App.tsx'
import { config } from './config'

// Wake the deployed backend on every full frontend load without delaying UI render.
void fetch(`${config.API_BASE_URL}/health`, { cache: 'no-store' }).catch(() => undefined)

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <WebSocketProvider>
          <App />
        </WebSocketProvider>
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>,
)
