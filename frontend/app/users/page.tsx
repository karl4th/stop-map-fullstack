"use client";
import { useEffect, useState } from "react";
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
  worker: "Работник", manager: "Менеджер", admin: "Админ",
};
const STATUS_STYLE: Record<string, { bg: string; color: string }> = {
  pending:  { bg: "#fefce8", color: "#a16207" },
  active:   { bg: "#f0fdf4", color: "#15803d" },
  blocked:  { bg: "#fef2f2", color: "#dc2626" },
};
const ROLE_STYLE: Record<string, { bg: string; color: string }> = {
  worker:  { bg: "#f1f5f9", color: "#475569" },
  manager: { bg: "#eff6ff", color: "#1d4ed8" },
  admin:   { bg: "#fdf4ff", color: "#7e22ce" },
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [sections, setSections] = useState<Section[]>([]);
  const [filter, setFilter] = useState("all");
  const [error, setError] = useState("");
  const [roleModal, setRoleModal] = useState<{ userId: number; role: string; section_id: string } | null>(null);
  const [password, setPassword] = useState("");
  const [admin, setAdmin] = useState(false);

  useEffect(() => {
    setAdmin(isAdmin());
    api.get<Section[]>("/admin/sections").then(setSections).catch(() => {});
  }, []);

  const prefix = admin ? "/admin" : "/manager";

  async function load() {
    try {
      const path = filter === "pending" ? `${prefix}/users/pending` : `${prefix}/users`;
      setUsers(await api.get<User[]>(path));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Ошибка");
    }
  }

  useEffect(() => { load(); }, [filter, admin]);

  async function approve(id: number) {
    try { await api.patch(`${prefix}/users/${id}/approve`); load(); }
    catch (e: unknown) { setError(e instanceof Error ? e.message : "Ошибка"); }
  }

  async function block(id: number) {
    try { await api.patch(`${prefix}/users/${id}/block`); load(); }
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
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Ошибка");
    }
  }

  const pendingCount = users.filter(u => u.status === "pending").length;

  return (
    <Layout>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "#0f172a" }}>Пользователи</h1>
          <p className="text-sm mt-1" style={{ color: "#64748b" }}>
            {users.length} пользователей
            {pendingCount > 0 && <span className="ml-2 font-semibold" style={{ color: "#f97316" }}>• {pendingCount} ожидают</span>}
          </p>
        </div>
      </div>

      {error && (
        <div className="mb-4 px-4 py-3 rounded-xl text-sm font-medium"
          style={{ background: "#fef2f2", color: "#dc2626", border: "1px solid #fecaca" }}>
          {error}
        </div>
      )}

      <div className="flex gap-2 mb-5">
        {["all", "pending"].map((f) => (
          <button key={f} onClick={() => setFilter(f)}
            className="px-4 py-2 rounded-xl text-sm font-semibold transition-all"
            style={filter === f
              ? { background: "#0f172a", color: "#fff" }
              : { background: "#fff", color: "#64748b", border: "1px solid #e2e8f0" }}>
            {f === "all" ? "Все" : `Ожидают ${pendingCount > 0 ? `(${pendingCount})` : ""}`}
          </button>
        ))}
      </div>

      <div className="rounded-2xl overflow-hidden" style={{ border: "1px solid #e2e8f0", background: "#fff" }}>
        {users.length === 0 ? (
          <div className="px-6 py-12 text-center text-sm" style={{ color: "#94a3b8" }}>
            {filter === "pending" ? "Нет ожидающих подтверждения" : "Пользователей нет"}
          </div>
        ) : (
          users.map((u, i) => {
            const ss = STATUS_STYLE[u.status] ?? { bg: "#f1f5f9", color: "#475569" };
            const rs = ROLE_STYLE[u.role] ?? { bg: "#f1f5f9", color: "#475569" };
            return (
              <div key={u.id} className="flex items-center justify-between px-5 py-4"
                style={{ borderBottom: i < users.length - 1 ? "1px solid #f1f5f9" : "none" }}>
                <div className="flex items-center gap-4">
                  <div className="w-9 h-9 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0"
                    style={{ background: "#fff7ed", color: "#f97316" }}>
                    {u.full_name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <p className="font-semibold text-sm" style={{ color: "#0f172a" }}>{u.full_name}</p>
                    <p className="text-xs mt-0.5" style={{ color: "#94a3b8" }}>
                      {u.phone ?? "—"}{u.telegram_id ? ` · TG ${u.telegram_id}` : ""}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-1 rounded-lg text-xs font-semibold"
                    style={{ background: rs.bg, color: rs.color }}>
                    {ROLE_LABELS[u.role]}
                  </span>
                  <span className="px-2.5 py-1 rounded-lg text-xs font-semibold"
                    style={{ background: ss.bg, color: ss.color }}>
                    {STATUS_LABELS[u.status]}
                  </span>
                  {u.status === "pending" && (
                    <button onClick={() => approve(u.id)}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold text-white"
                      style={{ background: "#22c55e" }}>
                      Принять
                    </button>
                  )}
                  {u.status === "active" && (
                    <button onClick={() => block(u.id)}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold"
                      style={{ background: "#fef2f2", color: "#dc2626" }}>
                      Блокировать
                    </button>
                  )}
                  {admin && (
                    <button onClick={() => setRoleModal({ userId: u.id, role: u.role, section_id: u.section_id?.toString() ?? "" })}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold"
                      style={{ background: "#f1f5f9", color: "#475569" }}>
                      Роль
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
        <div className="fixed inset-0 flex items-center justify-center z-50"
          style={{ background: "rgba(0,0,0,0.5)" }}
          onClick={() => setRoleModal(null)}>
          <div className="rounded-2xl p-6 w-96 shadow-2xl"
            style={{ background: "#fff" }}
            onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-bold mb-5" style={{ color: "#0f172a" }}>Назначить роль</h2>
            <div className="space-y-3 mb-4">
              <div>
                <label className="block text-xs font-semibold mb-1.5" style={{ color: "#64748b" }}>Роль</label>
                <select value={roleModal.role}
                  onChange={(e) => setRoleModal({ ...roleModal, role: e.target.value })}
                  className="w-full px-4 py-3 rounded-xl text-sm outline-none"
                  style={{ border: "1px solid #e2e8f0", color: "#0f172a" }}>
                  <option value="worker">Работник</option>
                  <option value="manager">Менеджер</option>
                  <option value="admin">Администратор</option>
                </select>
              </div>

              {roleModal.role === "manager" && (
                <div>
                  <label className="block text-xs font-semibold mb-1.5" style={{ color: "#64748b" }}>Участок</label>
                  <select value={roleModal.section_id}
                    onChange={(e) => setRoleModal({ ...roleModal, section_id: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl text-sm outline-none"
                    style={{ border: "1px solid #e2e8f0", color: "#0f172a" }}>
                    <option value="">— Выберите участок —</option>
                    {sections.map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
              )}

              {(roleModal.role === "manager" || roleModal.role === "admin") && (
                <div>
                  <label className="block text-xs font-semibold mb-1.5" style={{ color: "#64748b" }}>Пароль для входа</label>
                  <input type="password" value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Введите пароль"
                    className="w-full px-4 py-3 rounded-xl text-sm outline-none"
                    style={{ border: "1px solid #e2e8f0", color: "#0f172a" }} />
                </div>
              )}
            </div>
            <div className="flex gap-3">
              <button onClick={assignRole}
                className="flex-1 py-3 rounded-xl text-sm font-semibold text-white"
                style={{ background: "#f97316" }}>
                Сохранить
              </button>
              <button onClick={() => setRoleModal(null)}
                className="flex-1 py-3 rounded-xl text-sm font-semibold"
                style={{ background: "#f1f5f9", color: "#64748b" }}>
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}
