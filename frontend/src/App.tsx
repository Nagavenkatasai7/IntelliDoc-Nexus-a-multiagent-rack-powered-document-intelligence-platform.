import { useState, useEffect } from 'react'
import { useThemeStore } from '@/stores/themeStore'
import Sidebar from '@/components/Sidebar'
import Header from '@/components/Header'
import ChatInterface from '@/components/ChatInterface'
import SearchPanel from '@/components/SearchPanel'

export default function App() {
  const { theme } = useThemeStore()
  const [activeTab, setActiveTab] = useState<'chat' | 'search'>('chat')

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header activeTab={activeTab} onTabChange={setActiveTab} />
        <main className="flex-1 overflow-hidden">
          {activeTab === 'chat' ? <ChatInterface /> : <SearchPanel />}
        </main>
      </div>
    </div>
  )
}
