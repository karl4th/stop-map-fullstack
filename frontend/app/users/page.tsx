"use client";
import { useCallback, useEffect, useState } from "react";
import Layout from "@/components/Layout";
import { api, isAdmin } from "@/lib/api";

type User = {
  id: number;
  full_name: string;
  phone: string | null;
  telegram_id: number | null;
  role: string;
  status: string;
  section_id: number | null;
};

type Section = { id: number; name: string };

const STATUS_LABELS: Record<string, string> = {
  pending: "Ожидает", active: "Активен", blocked: "Заблокирован",
};
const ROLE_LABELS: Record<string, string> = {
  worker: "Работник", manager: "Менеджер", safety_engineer: "Инженер ОТ и ТБ", admin: "Админ",
};
const STATUS_STYLE: Record<string, { bg: string; color: string; dot: string }> = {
  pending:  { bg: "#fefce8", color: "#a16207", dot: "#eab308" },
  active:   { bg: "#f0fdf4", color: "#15803d", dot: "#22c55e" },
  blocked:  { bg: "#fef2f2", color: "#dc2626", dot: "#ef4444" },
};
const ROLE_STYLE: Record<string, { bg: string; color: string }> = {
  worker:           { bg: "#f1f5f9", color: "#475569" },
  manager:          { bg: "#eff6ff", color: "#1d4ed8" },
  safety_engineer:  { bg: "#f0fdf4", color: "#15803d" },
  admin:            { bg: "#fdf4ff", color: "#7e22ce" },
};

const AVATAR_COLORS = [
  { bg: "#dbeafe", text: "#1d4ed8" },
  { bg: "#dcfce7", text: "#15803d" },
  { bg: "#fef3c7", text: "#b45309" },
  { bg: "#fce7f3", text: "#be185d" },
  { bg: "#ede9fe", text: "#6d28d9" },
  { bg: "#fff7ed", text: "#c2410c" },
  { bg: "#e0f2fe", text: "#0369a1" },
  { bg: "#f0fdf4", text: "#166534" },
];

function getAvatarColor(name: string) {
  return AVATAR_COLORS[name.charCodeAt(0) % AVATAR_COLORS.length];
}

const CheckIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
);
const BlockIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
  </svg>
);
const ShieldIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
  </svg>
);
const XIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
);
const SearchIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
);

const selectStyle: React.CSSProperties = {
  padding: "8px 12px", borderRadius: 8, fontSize: 12.5, fontWeight: 500,
  border: "1px solid #e2e8f0", background: "#fff", color: "#334155",
  cursor: "pointer", outline: "none",
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [sections, setSections] = useState<Section[]>([]);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [filterRole, setFilterRole] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterSection, setFilterSection] = useState("all");
  const [error, setError] = useState("");
  const [roleModal, setRoleModal] = useState<{ userId: number; role: string; section_id: string } | null>(null);
  const [password, setPassword] = useState("");
  const [admin] = useState(() => isAdmin());

  useEffect(() => {
    api.get<Section[]>("/admin/sections").then(setSections).catch(() => {});
  }, []);

  const prefix = admin ? "/admin" : "/manager";

  const load = useCallback(async () => {
    try {
      let path = `${prefix}/users`;
      if (admin) {
        const params = new URLSearchParams();
        if (filterRole !== "all") params.set("role", filterRole);
        if (filterStatus !== "all") params.set("status", filterStatus);
        if (filterSection !== "all") params.set("section_id", filterSection);
        if (debouncedSearch.trim()) params.set("search", debouncedSearch.trim());
        if (params.toString()) path += `?${params}`;
      } else if (filterStatus === "pending") {
        path = `${prefix}/users/pending`;
      }
      setUsers(await api.get<User[]>(path));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Ошибка");
    }
  }, [admin, debouncedSearch, filterRole, filterSection, filterStatus, prefix]);

  useEffect(() => { void load(); }, [load]);

  // Debounce search
  useEffect(() => {
    if (!admin) return;
    const t = setTimeout(() => { setDebouncedSearch(search); }, 300);
    return () => clearTimeout(t);
  }, [admin, search]);

  async function approve(id: number) {
    try { await api.patch(`${prefix}/users/${id}/approve`); void load(); }
    catch (e: unknown) { setError(e instanceof Error ? e.message : "Ошибка"); }
  }

  async function reject(id: number) {
    try { await api.delete(`/admin/users/${id}/reject`); void load(); }
    catch (e: unknown) { setError(e instanceof Error ? e.message : "Ошибка"); }
  }

  async function block(id: number) {
    try { await api.patch(`${prefix}/users/${id}/block`); void load(); }
    catch (e: unknown) { setError(e instanceof Error ? e.message : "Ошибка"); }
  }

  async function assignRole() {
    if (!roleModal) return;
    try {
      await api.patch(`/admin/users/${roleModal.userId}/role`, {
        role: roleModal.role,
        password: password || undefined,
        section_id: roleModal.section_id ? parseInt(roleModal.section_id) : undefined,
      });
      setRoleModal(null);
      setPassword("");
      void load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Ошибка");
    }
  }

  const pendingCount = users.filter(u => u.status === "pending").length;

  const inputStyle: React.CSSProperties = {
    width: "100%", padding: "10px 14px", borderRadius: 9,
    border: "1px solid #e2e8f0", background: "#f8fafc",
    color: "#0f172a", fontSize: 13.5, outline: "none",
    transition: "border-color 0.12s, box-shadow 0.12s",
  };

  const sectionName = (id: number | null) => {
    if (!id) return null;
    return sections.find(s => s.id === id)?.name ?? `#${id}`;
  };

  return (
    <Layout>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: "#0f172a", letterSpacing: "-0.4px", margin: 0 }}>
            Пользователи
          </h1>
          <span style={{ padding: "2px 9px", borderRadius: 20, fontSize: 12, fontWeight: 600, background: "#f1f5f9", color: "#475569", border: "1px solid #e2e8f0" }}>
            {users.length}
          </span>
          {pendingCount > 0 && (
            <span style={{ padding: "2px 9px", borderRadius: 20, fontSize: 12, fontWeight: 600, background: "#fefce8", color: "#a16207", border: "1px solid #fef08a" }}>
              {pendingCount} ожидают
            </span>
          )}
        </div>
        <p style={{ fontSize: 13.5, color: "#64748b", margin: 0 }}>Управление пользователями системы</p>
      </div>

      {error && (
        <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 10, padding: "10px 14px", marginBottom: 16, fontSize: 13, color: "#dc2626" }}>
          {error}
        </div>
      )}

      {/* Filters row */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 16, alignItems: "center" }}>
        {/* Search */}
        {admin && (
          <div style={{ position: "relative", flex: "1 1 200px", minWidth: 180 }}>
            <span style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "#94a3b8" }}>
              <SearchIcon />
            </span>
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Поиск по имени или телефону..."
              style={{
                ...selectStyle, paddingLeft: 32, width: "100%", boxSizing: "border-box",
                fontSize: 13,
              }}
            />
          </div>
        )}

        {/* Role filter */}
        {admin && (
          <select value={filterRole} onChange={e => setFilterRole(e.target.value)} style={selectStyle}>
            <option value="all">Все роли</option>
            <option value="worker">Работники</option>
            <option value="manager">Менеджеры</option>
            <option value="safety_engineer">Инженеры ОТ и ТБ</option>
            <option value="admin">Администраторы</option>
          </select>
        )}

        {/* Status filter */}
        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} style={selectStyle}>
          <option value="all">Все статусы</option>
          <option value="pending">Ожидают</option>
          <option value="active">Активные</option>
          <option value="blocked">Заблокированные</option>
        </select>

        {/* Section filter (admin only) */}
        {admin && sections.length > 0 && (
          <select value={filterSection} onChange={e => setFilterSection(e.target.value)} style={selectStyle}>
            <option value="all">Все участки</option>
            {sections.map(s => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        )}

        <button onClick={load}
          style={{ padding: "8px 16px", borderRadius: 8, fontSize: 12.5, fontWeight: 600, background: "#0f172a", color: "#fff", border: "none", cursor: "pointer" }}>
          Обновить
        </button>
      </div>

      {/* List */}
      <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 14, overflow: "hidden", boxShadow: "0 1px 4px rgba(0,0,0,0.04)" }}>
        {users.length === 0 ? (
          <div style={{ padding: "56px 24px", textAlign: "center" }}>
            <div style={{ width: 52, height: 52, borderRadius: 13, background: "#f1f5f9", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 14px" }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
                <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
            </div>
            <p style={{ fontSize: 14, fontWeight: 600, color: "#64748b", margin: "0 0 4px" }}>Пользователей не найдено</p>
            <p style={{ fontSize: 13, color: "#94a3b8", margin: 0 }}>
              {search ? `По запросу «${search}» ничего не найдено` : "Попробуйте изменить фильтры"}
            </p>
          </div>
        ) : (
          users.map((u, i) => {
            const ss = STATUS_STYLE[u.status] ?? { bg: "#f1f5f9", color: "#475569", dot: "#94a3b8" };
            const rs = ROLE_STYLE[u.role] ?? { bg: "#f1f5f9", color: "#475569" };
            const av = getAvatarColor(u.full_name);
            const secName = sectionName(u.section_id);
            return (
              <div key={u.id}
                style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  padding: "13px 18px",
                  borderBottom: i < users.length - 1 ? "1px solid #f1f5f9" : "none",
                  transition: "background 0.1s",
                }}
                onMouseEnter={e => (e.currentTarget.style.background = "#fafafa")}
                onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <div style={{
                    width: 38, height: 38, borderRadius: "50%",
                    background: av.bg, border: `1.5px solid ${av.text}33`,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 14, fontWeight: 700, color: av.text, flexShrink: 0,
                  }}>
                    {u.full_name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <p style={{ fontSize: 13.5, fontWeight: 600, color: "#0f172a", margin: "0 0 2px" }}>{u.full_name}</p>
                    <p style={{ fontSize: 11.5, color: "#94a3b8", margin: 0 }}>
                      {u.phone ?? "—"}
                      {u.telegram_id ? ` · TG: ${u.telegram_id}` : ""}
                      {secName ? ` · ${secName}` : ""}
                    </p>
                  </div>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0, flexWrap: "wrap", justifyContent: "flex-end" }}>
                  <span style={{ padding: "4px 10px", borderRadius: 20, fontSize: 11.5, fontWeight: 600, background: rs.bg, color: rs.color }}>
                    {ROLE_LABELS[u.role] ?? u.role}
                  </span>
                  <span style={{
                    display: "flex", alignItems: "center", gap: 5,
                    padding: "4px 10px", borderRadius: 20, fontSize: 11.5, fontWeight: 600,
                    background: ss.bg, color: ss.color,
                  }}>
                    <span style={{ width: 6, height: 6, borderRadius: "50%", background: ss.dot, flexShrink: 0 }} />
                    {STATUS_LABELS[u.status]}
                  </span>

                  {u.status === "pending" && (
                    <>
                      <button onClick={() => approve(u.id)}
                        style={{ display: "flex", alignItems: "center", gap: 5, padding: "6px 12px", borderRadius: 7, background: "#22c55e", color: "white", border: "none", cursor: "pointer", fontSize: 12.5, fontWeight: 600 }}
                        onMouseEnter={e => (e.currentTarget.style.background = "#16a34a")}
                        onMouseLeave={e => (e.currentTarget.style.background = "#22c55e")}>
                        <CheckIcon /> Принять
                      </button>
                      <button onClick={() => reject(u.id)}
                        style={{ display: "flex", alignItems: "center", gap: 5, padding: "6px 12px", borderRadius: 7, background: "#fef2f2", color: "#dc2626", border: "none", cursor: "pointer", fontSize: 12.5, fontWeight: 600 }}
                        onMouseEnter={e => (e.currentTarget.style.background = "#fee2e2")}
                        onMouseLeave={e => (e.currentTarget.style.background = "#fef2f2")}>
                        <XIcon /> Отклонить
                      </button>
                    </>
                  )}
                  {u.status === "active" && (
                    <button onClick={() => block(u.id)}
                      style={{ display: "flex", alignItems: "center", gap: 5, padding: "6px 12px", borderRadius: 7, background: "#fef2f2", color: "#dc2626", border: "none", cursor: "pointer", fontSize: 12.5, fontWeight: 600 }}
                      onMouseEnter={e => (e.currentTarget.style.background = "#fee2e2")}
                      onMouseLeave={e => (e.currentTarget.style.background = "#fef2f2")}>
                      <BlockIcon /> Блокировать
                    </button>
                  )}
                  {admin && (
                    <button onClick={() => setRoleModal({ userId: u.id, role: u.role, section_id: u.section_id?.toString() ?? "" })}
                      style={{ display: "flex", alignItems: "center", gap: 5, padding: "6px 12px", borderRadius: 7, background: "#f1f5f9", color: "#475569", border: "none", cursor: "pointer", fontSize: 12.5, fontWeight: 600 }}
                      onMouseEnter={e => (e.currentTarget.style.background = "#e2e8f0")}
                      onMouseLeave={e => (e.currentTarget.style.background = "#f1f5f9")}>
                      <ShieldIcon /> Роль
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Role modal */}
      {roleModal && (
        <div
          style={{ position: "fixed", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50, background: "rgba(0,0,0,0.55)", backdropFilter: "blur(4px)" }}
          onClick={() => setRoleModal(null)}
        >
          <div
            className="animate-modal"
            style={{ background: "#fff", borderRadius: 16, padding: "24px", width: 380, boxShadow: "0 24px 60px rgba(0,0,0,0.2)", border: "1px solid #e2e8f0" }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
              <h2 style={{ fontSize: 16, fontWeight: 700, color: "#0f172a", margin: 0 }}>Назначить роль</h2>
              <button onClick={() => setRoleModal(null)}
                style={{ background: "#f1f5f9", border: "none", borderRadius: 7, padding: "6px", cursor: "pointer", color: "#64748b", display: "flex" }}
                onMouseEnter={e => (e.currentTarget.style.background = "#e2e8f0")}
                onMouseLeave={e => (e.currentTarget.style.background = "#f1f5f9")}>
                <XIcon />
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <div>
                <label style={{ display: "block", fontSize: 11.5, fontWeight: 600, color: "#64748b", marginBottom: 7, textTransform: "uppercase", letterSpacing: "0.05em" }}>Роль</label>
                <select value={roleModal.role} onChange={e => setRoleModal({ ...roleModal, role: e.target.value })} style={{ ...inputStyle, cursor: "pointer" }}>
                  <option value="worker">Работник</option>
                  <option value="manager">Менеджер</option>
                  <option value="safety_engineer">Инженер ОТ и ТБ</option>
                  <option value="admin">Администратор</option>
                </select>
              </div>

              {(roleModal.role === "manager") && (
                <div>
                  <label style={{ display: "block", fontSize: 11.5, fontWeight: 600, color: "#64748b", marginBottom: 7, textTransform: "uppercase", letterSpacing: "0.05em" }}>Участок</label>
                  <select value={roleModal.section_id} onChange={e => setRoleModal({ ...roleModal, section_id: e.target.value })} style={{ ...inputStyle, cursor: "pointer" }}>
                    <option value="">— Выберите участок —</option>
                    {sections.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                  </select>
                </div>
              )}

              {(roleModal.role === "manager" || roleModal.role === "safety_engineer" || roleModal.role === "admin") && (
                <div>
                  <label style={{ display: "block", fontSize: 11.5, fontWeight: 600, color: "#64748b", marginBottom: 7, textTransform: "uppercase", letterSpacing: "0.05em" }}>Пароль для входа</label>
                  <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Введите пароль..." style={inputStyle}
                    onFocus={e => { e.target.style.borderColor = "#f97316"; e.target.style.boxShadow = "0 0 0 3px rgba(249,115,22,0.1)"; }}
                    onBlur={e => { e.target.style.borderColor = "#e2e8f0"; e.target.style.boxShadow = "none"; }} />
                </div>
              )}
            </div>

            <div style={{ display: "flex", gap: 10, marginTop: 20 }}>
              <button onClick={assignRole}
                style={{ flex: 1, padding: "11px", borderRadius: 9, border: "none", background: "linear-gradient(135deg, #f97316 0%, #ea580c 100%)", color: "white", fontSize: 13.5, fontWeight: 600, cursor: "pointer", boxShadow: "0 2px 8px rgba(249,115,22,0.3)" }}
                onMouseEnter={e => (e.currentTarget.style.boxShadow = "0 4px 14px rgba(249,115,22,0.4)")}
                onMouseLeave={e => (e.currentTarget.style.boxShadow = "0 2px 8px rgba(249,115,22,0.3)")}>
                Сохранить
              </button>
              <button onClick={() => setRoleModal(null)}
                style={{ flex: 1, padding: "11px", borderRadius: 9, border: "1px solid #e2e8f0", background: "#f8fafc", color: "#64748b", fontSize: 13.5, fontWeight: 600, cursor: "pointer" }}
                onMouseEnter={e => (e.currentTarget.style.background = "#f1f5f9")}
                onMouseLeave={e => (e.currentTarget.style.background = "#f8fafc")}>
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}
