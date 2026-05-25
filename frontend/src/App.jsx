import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Orders from './pages/Orders'
import Tasks from './pages/Tasks'
import WarehouseRaw from './pages/WarehouseRaw'
import WarehousePackaging from './pages/WarehousePackaging'
import WarehouseProducts from './pages/WarehouseProducts'
import Assembly from './pages/Assembly'
import Deliveries from './pages/Deliveries'
import References from './pages/References'
import Settings from './pages/Settings'
import Users from './pages/Users'

function PrivateRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  return user ? children : <Navigate to="/login" replace />
}

function AppRoutes() {
  const { user } = useAuth()
  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/orders" replace /> : <Login />} />
      <Route
        path="/*"
        element={
          <PrivateRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Navigate to="/orders" replace />} />
                <Route path="/orders" element={<Orders />} />
                <Route path="/tasks" element={<Tasks />} />
                <Route path="/warehouse" element={<Navigate to="/warehouse/raw" replace />} />
                <Route path="/warehouse/raw" element={<WarehouseRaw />} />
                <Route path="/warehouse/packaging" element={<WarehousePackaging />} />
                <Route path="/warehouse/products" element={<WarehouseProducts />} />
                <Route path="/assembly" element={<Assembly />} />
                <Route path="/deliveries" element={<Deliveries />} />
                <Route path="/references" element={<References />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/users" element={<Users />} />
              </Routes>
            </Layout>
          </PrivateRoute>
        }
      />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
