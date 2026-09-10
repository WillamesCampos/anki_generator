import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";

import ErrorBoundary from "./components/ErrorBoundary";
import AppShell from "./components/layout/AppShell";
import { AuthProvider } from "./context/AuthContext";
import useAuth from "./context/useAuth";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import DeckDetailPage from "./pages/DeckDetailPage";
import DeckCardsPage from "./pages/DeckCardsPage";
import DeckListPage from "./pages/DeckListPage";
import NewDeckPage from "./pages/NewDeckPage";
import PlaceholderPage from "./pages/PlaceholderPage";
import StudySessionPage from "./pages/StudySessionPage";

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
      <Route path="/esqueci-minha-senha" element={<ForgotPasswordPage />} />
      <Route path="/redefinir-senha" element={<ResetPasswordPage />} />
      <Route element={<RequireAuth />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/decks" element={<DeckListPage />} />
        <Route path="/decks/novo" element={<NewDeckPage />} />
        <Route path="/decks/:deckId" element={<DeckDetailPage />} />
        <Route path="/decks/:deckId/cards" element={<DeckCardsPage />} />
        <Route path="/decks/:deckId/estudar" element={<StudySessionPage />} />
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
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
