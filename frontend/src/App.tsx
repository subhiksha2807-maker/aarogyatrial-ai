import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth'
import { Layout, Loading, RoleGate } from './components'
import Audit from './pages/Audit'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import ReportEvent from './pages/ReportEvent'
import Review from './pages/Review'
import Risks from './pages/Risks'
import { Studies, StudyDetails } from './pages/Studies'
function Router() { const { loading } = useAuth(); if (loading) return <Loading />; return <Routes><Route path="/login" element={<Login />} /><Route element={<Layout />}><Route index element={<Dashboard />} /><Route path="studies" element={<Studies />} /><Route path="studies/:id" element={<StudyDetails />} /><Route path="report-event" element={<RoleGate roles={['coordinator']}><ReportEvent /></RoleGate>} /><Route path="review" element={<RoleGate roles={['pi']}><Review /></RoleGate>} /><Route path="risks" element={<Risks />} /><Route path="audit" element={<Audit />} /></Route><Route path="*" element={<Navigate to="/" replace />} /></Routes> }
export default function App() { return <BrowserRouter><AuthProvider><Router /></AuthProvider></BrowserRouter> }
