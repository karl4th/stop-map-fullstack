"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { api, getRole } from "@/lib/api";
import { useState } from "react";

const FactoryIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 20a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8l-7 5V8l-7 5V4a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/>
    <path d="M17 18h1"/><path d="M12 18h1"/><path d="M7 18h1"/>
  </svg>
);

const UsersIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
    <circle cx="9" cy="7" r="4"/>
    <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>
  </svg>
);

const ShieldAlertIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
    <line x1="12" y1="8" x2="12" y2="12"/>
    <line x1="12" y1="16" x2="12.01" y2="16"/>
  </svg>
);

const LogOutIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
    <polyline points="16 17 21 12 16 7"/>
    <line x1="21" y1="12" x2="9" y2="12"/>
  </svg>
);

const adminNav = [
  { href: "/sections", label: "Участки", Icon: FactoryIcon },
  { href: "/users", label: "Пользователи", Icon: UsersIcon },
  { href: "/stop-cards", label: "Стоп-карты", Icon: ShieldAlertIcon },
];

const managerNav = [
  { href: "/users", label: "Пользователи", Icon: UsersIcon },
  { href: "/stop-cards", label: "Стоп-карты", Icon: ShieldAlertIcon },
];

const safetyEngineerNav = [
  { href: "/stop-cards", label: "Стоп-карты", Icon: ShieldAlertIcon },
];

const ROLE_LABELS: Record<string, string> = {
  admin: "Администратор",
  manager: "Менеджер",
  safety_engineer: "Инженер ОТ и ТБ",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [role] = useState<string | null>(() => getRole());

  const nav =
    role === "admin" ? adminNav :
    role === "safety_engineer" ? safetyEngineerNav :
    managerNav;

  const roleLabel = ROLE_LABELS[role ?? ""] ?? "Пользователь";

  function logout() {
    void api.post("/admin/auth/logout", {}).catch(() => {});
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    router.push("/login");
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      {/* Sidebar */}
      <aside style={{
        width: 252,
        flexShrink: 0,
        background: "#0d1117",
        display: "flex",
        flexDirection: "column",
        position: "fixed",
        top: 0,
        left: 0,
        height: "100vh",
        zIndex: 40,
        borderRight: "1px solid rgba(255,255,255,0.05)",
      }}>
        {/* Logo */}
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: "20px 18px",
          borderBottom: "1px solid rgba(255,255,255,0.05)",
        }}>
          <div style={{
            width: 36,
            height: 36,
            borderRadius: 10,
            background: "linear-gradient(135deg, #f97316 0%, #dc2626 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            boxShadow: "0 4px 14px rgba(249,115,22,0.4)",
          }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.25" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
          </div>
          <div style={{ lineHeight: 1.2 }}>
            <p style={{ fontSize: 15, fontWeight: 700, color: "#f1f5f9", letterSpacing: "-0.3px", margin: 0 }}>StopMap</p>
            <p style={{ fontSize: 11, color: "#475569", margin: 0 }}>Панель управления</p>
          </div>
        </div>

        {/* Navigation */}
        <nav style={{ flex: 1, padding: "12px 10px" }}>
          <p style={{
            fontSize: 10,
            fontWeight: 600,
            color: "#334155",
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            padding: "6px 10px 8px",
            margin: 0,
          }}>
            Навигация
          </p>
          {nav.map((item) => {
            const active = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "9px 10px 9px 12px",
                  borderRadius: 8,
                  fontSize: 13.5,
                  fontWeight: active ? 600 : 500,
                  color: active ? "#f1f5f9" : "#64748b",
                  background: active ? "rgba(249,115,22,0.1)" : "transparent",
                  borderLeft: `2px solid ${active ? "#f97316" : "transparent"}`,
                  textDecoration: "none",
                  marginBottom: 2,
                  transition: "all 0.12s ease",
                }}
              >
                <span style={{ color: active ? "#f97316" : "#475569", flexShrink: 0 }}>
                  <item.Icon />
                </span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div style={{ padding: "12px 14px 18px", borderTop: "1px solid rgba(255,255,255,0.05)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "6px 4px 10px" }}>
            <div style={{
              width: 30,
              height: 30,
              borderRadius: "50%",
              background: "linear-gradient(135deg, #1e3a5f 0%, #1e293b 100%)",
              border: "1.5px solid #334155",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 12,
              fontWeight: 700,
              color: "#64748b",
              flexShrink: 0,
            }}>
              {roleLabel.charAt(0)}
            </div>
            <div>
              <p style={{ fontSize: 12.5, fontWeight: 600, color: "#94a3b8", margin: 0 }}>{roleLabel}</p>
            </div>
          </div>
          <button
            onClick={logout}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              width: "100%",
              padding: "8px 10px",
              borderRadius: 7,
              fontSize: 13,
              fontWeight: 500,
              color: "#475569",
              background: "transparent",
              border: "none",
              cursor: "pointer",
              transition: "all 0.12s ease",
            }}
            onMouseEnter={e => {
              e.currentTarget.style.color = "#ef4444";
              e.currentTarget.style.background = "rgba(239,68,68,0.08)";
            }}
            onMouseLeave={e => {
              e.currentTarget.style.color = "#475569";
              e.currentTarget.style.background = "transparent";
            }}
          >
            <LogOutIcon />
            Выйти из системы
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main style={{
        flex: 1,
        marginLeft: 252,
        background: "#f8fafc",
        minHeight: "100vh",
      }}>
        <div style={{ maxWidth: 960, margin: "0 auto", padding: "32px 36px" }}>
          {children}
        </div>
      </main>
    </div>
  );
}
