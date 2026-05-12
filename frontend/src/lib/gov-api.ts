import type {
  AskResponse,
  ChatTurn,
  PolicyExtraction,
  SourceCreateRequest,
  SourceDiscoverResponse,
  StreamEvent,
} from '../types/gov'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8081'
const resolvedApiBase =
  API_BASE === 'http://127.0.0.1:8081' && typeof window !== 'undefined'
    ? `${window.location.origin}/api`
    : API_BASE

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}

export async function askGovernmentKnowledge(question: string, history: ChatTurn[] = []): Promise<AskResponse> {
  const response = await fetch(`${resolvedApiBase}/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question,
      top_k: 5,
      history,
    }),
  })

  return parseJson<AskResponse>(response)
}

export async function streamGovernmentKnowledge(
  question: string,
  history: ChatTurn[],
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const response = await fetch(`${resolvedApiBase}/ask/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify({
      question,
      top_k: 5,
      history,
    }),
  })

  if (!response.ok || !response.body) {
    throw new Error(`Request failed: ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done })
    buffer = buffer.replace(/\r\n/g, '\n')

    let boundary = buffer.indexOf('\n\n')
    while (boundary !== -1) {
      const chunk = buffer.slice(0, boundary)
      buffer = buffer.slice(boundary + 2)
      const parsed = parseSseChunk(chunk)
      if (parsed) {
        onEvent(parsed)
      }
      boundary = buffer.indexOf('\n\n')
    }

    if (done) {
      break
    }
  }
}

function parseSseChunk(chunk: string): StreamEvent | null {
  const lines = chunk.split(/\r?\n/)
  const eventLine = lines.find((line) => line.startsWith('event:'))
  const dataLine = lines.find((line) => line.startsWith('data:'))
  if (!eventLine || !dataLine) {
    return null
  }

  const eventName = eventLine.slice(6).trim()
  const data = JSON.parse(dataLine.slice(5).trim()) as {
    content?: string
    citations?: AskResponse['citations']
    message?: string
  }

  if (eventName === 'delta') {
    return { type: 'delta', content: data.content ?? '' }
  }
  if (eventName === 'citations') {
    return { type: 'citations', citations: data.citations ?? [] }
  }
  if (eventName === 'error') {
    return { type: 'error', message: data.message ?? 'Unknown stream error' }
  }
  if (eventName === 'done') {
    return { type: 'done' }
  }

  return null
}

export async function pingHealth(): Promise<boolean> {
  const response = await fetch(`${resolvedApiBase}/health`)
  if (!response.ok) {
    return false
  }
  return true
}

export async function fetchPolicyExtraction(documentId: number): Promise<PolicyExtraction> {
  const response = await fetch(`${resolvedApiBase}/documents/${documentId}/extract`)
  return parseJson<PolicyExtraction>(response)
}

export async function createSource(request: SourceCreateRequest): Promise<void> {
  const response = await fetch(`${resolvedApiBase}/sources`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `Request failed: ${response.status}`)
  }
}

export async function discoverSource(url: string): Promise<SourceDiscoverResponse> {
  const response = await fetch(`${resolvedApiBase}/sources/discover`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ url }),
  })
  return parseJson<SourceDiscoverResponse>(response)
}
