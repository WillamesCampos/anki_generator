import Sidebar from "./Sidebar";
import "./AppShell.css";

export default function AppShell({ children }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="app-shell__content">{children}</main>
    </div>
  );
}
