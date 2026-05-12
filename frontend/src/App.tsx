import { ConfigProvider, theme as antdTheme } from 'antd'
import { useEffect, useState } from 'react'

import { GovChatPage } from './features/chat/gov-chat-page'

export type ThemeMode = 'dark' | 'light'

function App() {
  const [themeMode, setThemeMode] = useState<ThemeMode>('dark')

  useEffect(() => {
    document.documentElement.dataset.theme = themeMode
  }, [themeMode])

  return (
    <ConfigProvider
      theme={{
        algorithm:
          themeMode === 'dark' ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
        token: {
          borderRadius: 16,
          colorPrimary: '#10a37f',
          fontFamily:
            '"Segoe UI", "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif',
        },
      }}
    >
      <GovChatPage themeMode={themeMode} onThemeModeChange={setThemeMode} />
    </ConfigProvider>
  )
}

export default App
