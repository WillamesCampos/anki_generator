import { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";

import { logout } from "../../api/auth";
import useAuth from "../../context/useAuth";
import "./Sidebar.css";

const NAV_ITEMS = [
  { to: "/", label: "Home", end: true },
  { to: "/decks", label: "Decks" },
  { to: "/categorias", label: "Categorias" },
  { to: "/relatorios", label: "Relatórios" },
  { to: "/chat-ia", label: "Chat com IA" },
];

const COLLAPSED_KEY = "anki_generator_sidebar_collapsed";
const TABLET_MEDIA_QUERY = "(max-width: 1024px)";

function getInitialCollapsed() {
  const savedPreference = localStorage.getItem(COLLAPSED_KEY);
  if (savedPreference !== null) return savedPreference === "true";

  return window.matchMedia(TABLET_MEDIA_QUERY).matches;
}

export default function Sidebar() {
  const navigate = useNavigate();
  const { markLoggedOut } = useAuth();
  const [collapsed, setCollapsed] = useState(getInitialCollapsed);

  useEffect(() => {
    const tabletMedia = window.matchMedia(TABLET_MEDIA_QUERY);

    function handleViewportChange(event) {
      if (localStorage.getItem(COLLAPSED_KEY) === null) {
        setCollapsed(event.matches);
      }
    }

    tabletMedia.addEventListener("change", handleViewportChange);
    return () => tabletMedia.removeEventListener("change", handleViewportChange);
  }, []);

  function toggleCollapsed() {
    setCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem(COLLAPSED_KEY, String(next));
      return next;
    });
  }

  async function handleLogout() {
    await logout().catch(() => {
      // logout() já limpa os tokens locais mesmo se a chamada ao backend
      // falhar (ex.: já expirado) — ver api/auth.js
    });
    markLoggedOut();
    navigate("/login", { replace: true });
  }

  return (
    <nav aria-label="Navegação principal" className={`sidebar${collapsed ? " sidebar--collapsed" : ""}`}>
      <div className="sidebar__header">
        <div className="sidebar__brand">
          {collapsed ? (
            "AG"
          ) : (
            <>
              <span>Anki</span>
              <span>Generator</span>
            </>
          )}
        </div>
        <button
          type="button"
          className="sidebar__toggle"
          onClick={toggleCollapsed}
          aria-label={collapsed ? "Expandir menu" : "Recolher menu"}
          title={collapsed ? "Expandir menu" : "Recolher menu"}
        >
          {collapsed ? "»" : "«"}
        </button>
      </div>
      <ul className="sidebar__list">
        {NAV_ITEMS.map((item) => (
          <li key={item.to}>
            <NavLink
              to={item.to}
              end={item.end}
              title={collapsed ? item.label : undefined}
              className={({ isActive }) => `sidebar__link${isActive ? " sidebar__link--active" : ""}`}
            >
              {collapsed ? item.label[0] : item.label}
            </NavLink>
          </li>
        ))}
        <li>
          <button
            type="button"
            className="sidebar__link sidebar__logout"
            onClick={handleLogout}
            title={collapsed ? "Sair" : undefined}
          >
            {collapsed ? "S" : "Sair"}
          </button>
        </li>
      </ul>
    </nav>
  );
}
