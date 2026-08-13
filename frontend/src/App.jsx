import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";

import AppShell from "./components/layout/AppShell";
import { AuthProvider, useAuth } from "./context/AuthContext";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import PlaceholderPage from "./pages/PlaceholderPage";

function RequireAuth() {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  return (
    <AppShell>
      <Outlet />
    </AppShell>
  );
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<RequireAuth />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/decks" element={<PlaceholderPage title="Decks" />} />
        <Route path="/categorias" element={<PlaceholderPage title="Categorias" />} />
        <Route path="/relatorios" element={<PlaceholderPage title="Relatórios" />} />
        {/* Chat IA é só placeholder visual — sem chamada de API (Sprint 6 tem o agente de verdade) */}
        <Route path="/chat-ia" element={<PlaceholderPage title="Chat com IA" />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
