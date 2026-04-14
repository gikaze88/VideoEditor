import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom'
import { Film, PlusCircle, Clock, Clapperboard } from 'lucide-react'
import { useEffect, useState } from 'react'
import NewJob from './pages/NewJob'
import JobDetail from './pages/JobDetail'
import History from './pages/History'
import Editor from './pages/Editor'
import { editorClipCount } from './editorStore'

function Navbar() {
  const location = useLocation()
  const [clipCount, setClipCount] = useState(editorClipCount())

  // Rafraîchir le badge à chaque changement de route
  useEffect(() => { setClipCount(editorClipCount()) }, [location])

  return (
    <nav className="bg-gray-900 border-b border-gray-800 px-4 sm:px-6 py-3 flex items-center gap-2 sm:gap-6 overflow-x-auto">
      <div className="flex items-center gap-2 text-violet-400 font-bold text-base sm:text-lg shrink-0 mr-2 sm:mr-0">
        <Film size={20} />
        <span className="hidden xs:inline sm:inline">VideoMaker</span>
      </div>
      <NavLink
        to="/"
        end
        className={({ isActive }) =>
          `flex items-center gap-1.5 text-sm px-3 py-2 rounded-md transition-colors shrink-0 ${
            isActive
              ? 'bg-violet-600 text-white'
              : 'text-gray-400 hover:text-white hover:bg-gray-800'
          }`
        }
      >
        <PlusCircle size={15} />
        <span className="hidden sm:inline">Nouveau job</span>
        <span className="sm:hidden">Nouveau</span>
      </NavLink>
      <NavLink
        to="/editor"
        className={({ isActive }) =>
          `flex items-center gap-1.5 text-sm px-3 py-2 rounded-md transition-colors shrink-0 ${
            isActive
              ? 'bg-violet-600 text-white'
              : 'text-gray-400 hover:text-white hover:bg-gray-800'
          }`
        }
      >
        <Clapperboard size={15} />
        Éditeur
        {clipCount > 0 && (
          <span className="bg-violet-500 text-white text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center leading-none">
            {clipCount}
          </span>
        )}
      </NavLink>
      <NavLink
        to="/history"
        className={({ isActive }) =>
          `flex items-center gap-1.5 text-sm px-3 py-2 rounded-md transition-colors shrink-0 ${
            isActive
              ? 'bg-violet-600 text-white'
              : 'text-gray-400 hover:text-white hover:bg-gray-800'
          }`
        }
      >
        <Clock size={15} />
        Historique
      </NavLink>
    </nav>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
        <Navbar />

        {/* Contenu */}
        <main className="flex-1 px-4 py-4 sm:px-6 sm:py-6 max-w-7xl mx-auto w-full">
          <Routes>
            <Route path="/"        element={<NewJob />} />
            <Route path="/editor"  element={<Editor />} />
            <Route path="/jobs/:id" element={<JobDetail />} />
            <Route path="/history" element={<History />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
