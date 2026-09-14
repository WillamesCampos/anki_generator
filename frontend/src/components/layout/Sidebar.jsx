import { useEffect, useState } from "react";
import {
  Bot,
  ChartColumn,
  ChevronsLeft,
  ChevronsRight,
  House,
  Layers3,
  LogOut,
  Tags,
} from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";

import { logout } from "../../api/auth";
import useAuth from "../../context/useAuth";
import "./Sidebar.css";

const NAV_ITEMS = [
  { to: "/", label: "Home", icon: House, end: true },
  { to: "/decks", label: "Decks", icon: Layers3 },
  { to: "/categorias", label: "Categorias", icon: Tags },
  { to: "/relatorios", label: "Relatórios", icon: ChartColumn },
  { to: "/chat-ia", label: "Chat com IA", icon: Bot },
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
  const ToggleIcon = collapsed ? ChevronsRight : ChevronsLeft;

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
          aria-expanded={!collapsed}
          aria-controls="sidebar-navigation-list"
          title={collapsed ? "Expandir menu" : "Recolher menu"}
        >
          <ToggleIcon
            className="sidebar__toggle-icon"
            size={22}
            strokeWidth={2.5}
            aria-hidden="true"
            focusable="false"
          />
        </button>
      </div>
      <ul id="sidebar-navigation-list" className="sidebar__list">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;

          return (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.end}
                aria-label={collapsed ? item.label : undefined}
                className={({ isActive }) => `sidebar__link${isActive ? " sidebar__link--active" : ""}`}
              >
                <Icon
                  className="sidebar__item-icon"
                  size={20}
                  strokeWidth={2}
                  aria-hidden="true"
                  focusable="false"
                />
                <span className="sidebar__link-label">{item.label}</span>
                <span className="sidebar__tooltip" aria-hidden="true">{item.label}</span>
              </NavLink>
            </li>
          );
        })}
        <li>
          <button
            type="button"
            className="sidebar__link sidebar__logout"
            onClick={handleLogout}
            aria-label={collapsed ? "Sair" : undefined}
          >
            <LogOut
              className="sidebar__item-icon"
              size={20}
              strokeWidth={2}
              aria-hidden="true"
              focusable="false"
            />
            <span className="sidebar__link-label">Sair</span>
            <span className="sidebar__tooltip" aria-hidden="true">Sair</span>
          </button>
        </li>
      </ul>
    </nav>
  );
}
