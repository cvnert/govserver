export type Citation = {
  id?: number
  title: string
  url: string
  publish_time: string
  issuer: string
  snippet?: string
}

export type AskResponse = {
  answer: string
  citations: Citation[]
}

export type ChatTurn = {
  role: 'user' | 'assistant'
  content: string
}

export type StreamEvent =
  | { type: 'delta'; content: string }
  | { type: 'citations'; citations: Citation[] }
  | { type: 'done' }
  | { type: 'error'; message: string }

export type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  pending?: boolean
  error?: boolean
}

export type ChatSession = {
  key: string
  label: string
}

export type PolicyExtraction = {
  policy_name: string
  issuer: string
  publish_time: string
  location: string
  eligible_audience: string[]
  support_items: string[]
  application_materials: string[]
  application_process: string[]
  deadlines: string[]
  contact_points: string[]
  amounts: string[]
  summary: string
  source_url: string
}

export type SourceChannelInput = {
  name: string
  url: string
  item_selector: string
  link_selector: string
  list_date_selector: string
  issuer: string
}

export type SourceCreateRequest = {
  key: string
  name: string
  base_url: string
  region: string
  enabled: boolean
  crawler: string
  channels: SourceChannelInput[]
}

export type SourcePreviewItem = {
  title: string
  url: string
  publish_time: string
}

export type SourceDiscoverResponse = {
  item_selector: string
  link_selector: string
  list_date_selector: string
  previews: SourcePreviewItem[]
}
