import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { Film, PlusCircle, Clock } from 'lucide-react'
import NewJob from './pages/NewJob'
import JobDetail from './pages/JobDetail'
import History from './pages/History'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
        {/* Navbar */}
        <nav className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center gap-8">
          <div className="flex items-center gap-2 text-violet-400 font-bold text-lg">
            <Film size={22} />
            VideoMaker
          </div>
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-md transition-colors ${
                isActive
                  ? 'bg-violet-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`
            }
          >
            <PlusCircle size={15} />
            Nouveau job
          </NavLink>
          <NavLink
            to="/history"
            className={({ isActive }) =>
              `flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-md transition-colors ${
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

        {/* Contenu */}
        <main className="flex-1 p-6 max-w-4xl mx-auto w-full">
          <Routes>
            <Route path="/" element={<NewJob />} />
            <Route path="/jobs/:id" element={<JobDetail />} />
            <Route path="/history" element={<History />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
