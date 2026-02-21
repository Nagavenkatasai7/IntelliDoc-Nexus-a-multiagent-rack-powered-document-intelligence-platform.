import { Search, MessageSquare, Sun, Moon } from 'lucide-react'
import { useThemeStore } from '@/stores/themeStore'
import ConversationExport from './ConversationExport'

interface Props {
  activeTab: 'chat' | 'search'
  onTabChange: (tab: 'chat' | 'search') => void
}

export default function Header({ activeTab, onTabChange }: Props) {
  const { theme, toggleTheme } = useThemeStore()

  return (
    <header className="h-14 border-b flex items-center justify-between px-4 bg-card">
      <div className="flex items-center gap-1">
        <button
          onClick={() => onTabChange('chat')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'chat'
              ? 'bg-primary text-primary-foreground'
              : 'text-muted-foreground hover:text-foreground hover:bg-secondary'
          }`}
        >
          <MessageSquare className="h-4 w-4" />
          Chat
        </button>
        <button
          onClick={() => onTabChange('search')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'search'
              ? 'bg-primary text-primary-foreground'
              : 'text-muted-foreground hover:text-foreground hover:bg-secondary'
          }`}
        >
          <Search className="h-4 w-4" />
          Search
        </button>
      </div>

      <div className="flex items-center gap-2">
        <ConversationExport />
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg hover:bg-secondary transition-colors text-muted-foreground hover:text-foreground"
        >
          {theme === 'light' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        </button>
      </div>
    </header>
  )
}
