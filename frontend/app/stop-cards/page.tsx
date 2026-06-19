"use client";
import { useEffect, useState } from "react";
import Layout from "@/components/Layout";
import AuthImage from "@/components/AuthImage";
import { api, getRole, isAdmin } from "@/lib/api";

type Photo = { id: number; minio_key: string; photo_type: string };
type UserBrief = { id: number; full_name: string };

type StopCard = {
  id: number;
  reporter: UserBrief | null;
  violator_name: string;
  section_id: number;
  description: string;
  status: string;
  acknowledged_by: UserBrief | null;
  acknowledged_at: string | null;
  fix_description: string | null;
  fixed_by: UserBrief | null;
  fixed_at: string | null;
  manager_note: string | null;
  manager_checked_by: UserBrief | null;
  manager_checked_at: string | null;
  safety_note: string | null;
  safety_checked_by: UserBrief | null;
  safety_checked_at: string | null;
  created_at: string;
  closed_at: string | null;
  photos: Photo[];
};

const STATUS_LABELS: Record<string, string> = {
  created:      "Создана",
  waiting_violator: "Ожидает регистрации нарушителя",
  violator_fixing:  "Устраняется нарушителем",
  manager_review:  "Проверка менеджера",
  safety_check: "Проверка ОТ и ТБ",
  approved:     "Разрешено к работе",
  rejected:     "Запрещено",
  closed:       "Закрыто",
};

const STATUS_STYLE: Record<string, { bg: string; color: string; dot: string }> = {
  created:      { bg: "#f8fafc",  color: "#475569", dot: "#94a3b8" },
  waiting_violator: { bg: "#f8fafc",  color: "#475569", dot: "#94a3b8" },
  violator_fixing:  { bg: "#fff7ed",  color: "#c2410c", dot: "#f97316" },
  manager_review:  { bg: "#eff6ff",  color: "#1d4ed8", dot: "#3b82f6" },
  safety_check: { bg: "#fefce8",  color: "#a16207", dot: "#eab308" },
  approved:     { bg: "#f0fdf4",  color: "#15803d", dot: "#22c55e" },
  rejected:     { bg: "#fef2f2",  color: "#dc2626", dot: "#ef4444" },
  closed:       { bg: "#f1f5f9",  color: "#334155", dot: "#64748b" },
};

const XIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
);
const PhotoIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="2"/>
    <circle cx="8.5" cy="8.5" r="1.5"/>
    <polyline points="21 15 16 10 5 21"/>
  </svg>
);
const CalendarIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
    <line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/>
    <line x1="3" y1="10" x2="21" y2="10"/>
  </svg>
);

function fmt(dt: string | null | undefined): string {
  if (!dt) return "—";
  return new Date(dt).toLocaleString("ru");
}

function AuditRow({ label, who, when }: { label: string; who: UserBrief | null; when: string | null }) {
  if (!who && !when) return null;
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "7px 0", borderBottom: "1px solid #f1f5f9" }}>
      <span style={{ fontSize: 12, color: "#64748b", fontWeight: 500 }}>{label}</span>
      <span style={{ fontSize: 12, color: "#0f172a", fontWeight: 600, textAlign: "right" }}>
        {who?.full_name ?? "—"} <span style={{ color: "#94a3b8", fontWeight: 400 }}>{fmt(when)}</span>
      </span>
    </div>
  );
}

export default function StopCardsPage() {
  const [cards, setCards] = useState<StopCard[]>([]);
  const [statusFilter, setStatusFilter] = useState("all");
  const [year, setYear] = useState("");
  const [month, setMonth] = useState("");
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<StopCard | null>(null);
  const [admin, setAdmin] = useState(false);
  const [role, setRole] = useState("");

  useEffect(() => {
    setAdmin(isAdmin());
    setRole(getRole() ?? "");
  }, []);

  function apiPrefix(): string {
    if (admin) return "/admin";
    if (role === "safety_engineer") return "/safety-engineer";
    return "/manager";
  }

  async function load() {
    setError("");
    try {
      let path = `${apiPrefix()}/stop-cards`;
      if (admin) {
        const params = new URLSearchParams();
        if (statusFilter !== "all") params.set("status", statusFilter);
        if (year) params.set("year", year);
        if (month) params.set("month", month);
        if (params.toString()) path += `?${params}`;
      }
      let result = await api.get<StopCard[]>(path);
      if (!admin && statusFilter !== "all") result = result.filter(c => c.status === statusFilter);
      setCards(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Ошибка");
    }
  }

  useEffect(() => { if (role) load(); }, [statusFilter, role]);

  async function adminClose(cardId: number) {
    try {
      const updated = await api.patch<StopCard>(`/admin/stop-cards/${cardId}/close`);
      setSelected(updated);
      load();
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Ошибка"); }
  }

  const allStatuses = ["all", "created", "waiting_violator", "violator_fixing", "manager_review", "safety_check", "approved", "rejected", "closed"];
  const beforePhotos = selected?.photos.filter(p => p.photo_type === "before") ?? [];
  const afterPhotos = selected?.photos.filter(p => p.photo_type === "after") ?? [];

  return (
    <Layout>
      <div style={{ marginBottom: 28 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: "#0f172a", letterSpacing: "-0.4px", margin: 0 }}>Стоп-карты</h1>
          {cards.length > 0 && (
            <span style={{ padding: "2px 9px", borderRadius: 20, fontSize: 12, fontWeight: 600, background: "#f1f5f9", color: "#475569", border: "1px solid #e2e8f0" }}>
              {cards.length}
            </span>
          )}
        </div>
        <p style={{ fontSize: 13.5, color: "#64748b", margin: 0 }}>Журнал нарушений безопасности. Действия выполняются в Telegram.</p>
      </div>

      {error && (
        <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 10, padding: "10px 14px", marginBottom: 16, fontSize: 13, color: "#dc2626" }}>
          {error}
        </div>
      )}

      {/* Filters */}
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 10, marginBottom: 20 }}>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {allStatuses.map(f => {
            const active = statusFilter === f;
            const ss = f !== "all" ? STATUS_STYLE[f] : null;
            return (
              <button key={f} onClick={() => setStatusFilter(f)}
                style={{
                  display: "flex", alignItems: "center", gap: 5,
                  padding: "7px 13px", borderRadius: 8, fontSize: 12, fontWeight: 600,
                  cursor: "pointer", transition: "all 0.12s",
                  border: active ? "none" : "1px solid #e2e8f0",
                  background: active ? "#0f172a" : "#fff",
                  color: active ? "#fff" : "#64748b",
                  boxShadow: active ? "0 2px 8px rgba(15,23,42,0.15)" : "none",
                }}
              >
                {ss && !active && <span style={{ width: 7, height: 7, borderRadius: "50%", background: ss.dot, flexShrink: 0 }} />}
                {f === "all" ? "Все" : STATUS_LABELS[f]}
              </button>
            );
          })}
        </div>

        {admin && (
          <div style={{ display: "flex", gap: 8, marginLeft: "auto", alignItems: "center" }}>
            <input type="number" value={year} onChange={e => setYear(e.target.value)} placeholder="Год"
              style={{ padding: "7px 12px", borderRadius: 8, fontSize: 12.5, border: "1px solid #e2e8f0", background: "#fff", color: "#0f172a", outline: "none", width: 80 }} />
            <input type="number" value={month} onChange={e => setMonth(e.target.value)} placeholder="Месяц"
              style={{ padding: "7px 12px", borderRadius: 8, fontSize: 12.5, border: "1px solid #e2e8f0", background: "#fff", color: "#0f172a", outline: "none", width: 88 }} />
            <button onClick={load}
              style={{ padding: "7px 16px", borderRadius: 8, fontSize: 12.5, fontWeight: 600, background: "#0f172a", color: "#fff", border: "none", cursor: "pointer" }}>
              Применить
            </button>
          </div>
        )}
      </div>

      {/* List */}
      <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 14, overflow: "hidden", boxShadow: "0 1px 4px rgba(0,0,0,0.04)" }}>
        {cards.length === 0 ? (
          <div style={{ padding: "56px 24px", textAlign: "center" }}>
            <p style={{ fontSize: 14, fontWeight: 600, color: "#64748b", margin: "0 0 4px" }}>Стоп-карт нет</p>
            <p style={{ fontSize: 13, color: "#94a3b8", margin: 0 }}>
              {statusFilter !== "all" ? `Нет карт со статусом "${STATUS_LABELS[statusFilter]}"` : "Нарушения не зафиксированы"}
            </p>
          </div>
        ) : (
          cards.map((c, i) => {
            const ss = STATUS_STYLE[c.status] ?? { bg: "#f1f5f9", color: "#475569", dot: "#94a3b8" };
            return (
              <div key={c.id}
                style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  padding: "14px 18px", cursor: "pointer",
                  borderBottom: i < cards.length - 1 ? "1px solid #f1f5f9" : "none",
                  transition: "background 0.1s",
                }}
                onMouseEnter={e => (e.currentTarget.style.background = "#fafafa")}
                onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
                onClick={() => setSelected(c)}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <div style={{
                    width: 36, height: 36, borderRadius: 9,
                    background: "linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 11.5, fontWeight: 700, color: "#c2410c", flexShrink: 0,
                  }}>#{c.id}</div>
                  <div>
                    <p style={{ fontSize: 13.5, fontWeight: 600, color: "#0f172a", margin: "0 0 2px" }}>{c.violator_name}</p>
                    <p style={{ fontSize: 12, color: "#94a3b8", margin: 0, maxWidth: 340, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {c.description}
                    </p>
                  </div>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: 10, flexShrink: 0 }}>
                  {c.photos.length > 0 && (
                    <span style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 12, color: "#94a3b8" }}>
                      <PhotoIcon /> {c.photos.length}
                    </span>
                  )}
                  <span style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 12, color: "#94a3b8" }}>
                    <CalendarIcon /> {new Date(c.created_at).toLocaleDateString("ru")}
                  </span>
                  <span style={{
                    display: "flex", alignItems: "center", gap: 5,
                    padding: "4px 10px", borderRadius: 20, fontSize: 11.5, fontWeight: 600,
                    background: ss.bg, color: ss.color,
                  }}>
                    <span style={{ width: 6, height: 6, borderRadius: "50%", background: ss.dot, flexShrink: 0 }} />
                    {STATUS_LABELS[c.status]}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Detail modal */}
      {selected && (
        <div
          style={{ position: "fixed", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50, padding: 16, background: "rgba(0,0,0,0.55)", backdropFilter: "blur(4px)" }}
          onClick={() => setSelected(null)}
        >
          <div
            className="animate-modal"
            style={{
              background: "#fff", borderRadius: 18, width: "100%", maxWidth: 520,
              boxShadow: "0 32px 72px rgba(0,0,0,0.25)", border: "1px solid #e2e8f0",
              maxHeight: "92vh", overflow: "hidden", display: "flex", flexDirection: "column",
            }}
            onClick={e => e.stopPropagation()}
          >
            {/* Header */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "18px 20px", borderBottom: "1px solid #f1f5f9", flexShrink: 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{
                  width: 34, height: 34, borderRadius: 9,
                  background: "linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 11, fontWeight: 700, color: "#c2410c",
                }}>#{selected.id}</div>
                <h2 style={{ fontSize: 15, fontWeight: 700, color: "#0f172a", margin: 0 }}>Стоп-карта #{selected.id}</h2>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                {(() => {
                  const ss = STATUS_STYLE[selected.status] ?? { bg: "#f1f5f9", color: "#475569", dot: "#94a3b8" };
                  return (
                    <span style={{ display: "flex", alignItems: "center", gap: 5, padding: "4px 10px", borderRadius: 20, fontSize: 11.5, fontWeight: 600, background: ss.bg, color: ss.color }}>
                      <span style={{ width: 6, height: 6, borderRadius: "50%", background: ss.dot }} />
                      {STATUS_LABELS[selected.status]}
                    </span>
                  );
                })()}
                <button onClick={() => setSelected(null)}
                  style={{ background: "#f1f5f9", border: "none", borderRadius: 7, padding: "6px", cursor: "pointer", color: "#64748b", display: "flex" }}
                  onMouseEnter={e => (e.currentTarget.style.background = "#e2e8f0")}
                  onMouseLeave={e => (e.currentTarget.style.background = "#f1f5f9")}>
                  <XIcon />
                </button>
              </div>
            </div>

            {/* Body */}
            <div style={{ padding: "20px", overflowY: "auto", flex: 1, display: "flex", flexDirection: "column", gap: 14 }}>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                <div style={{ background: "#f8fafc", borderRadius: 10, padding: "12px 14px" }}>
                  <p style={{ fontSize: 10.5, fontWeight: 600, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 4px" }}>Нарушитель</p>
                  <p style={{ fontSize: 13.5, fontWeight: 600, color: "#0f172a", margin: 0 }}>{selected.violator_name}</p>
                </div>
                <div style={{ background: "#f8fafc", borderRadius: 10, padding: "12px 14px" }}>
                  <p style={{ fontSize: 10.5, fontWeight: 600, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 4px" }}>Создана</p>
                  <p style={{ fontSize: 12.5, fontWeight: 500, color: "#334155", margin: 0 }}>{fmt(selected.created_at)}</p>
                </div>
              </div>

              {selected.reporter && (
                <div style={{ background: "#f8fafc", borderRadius: 10, padding: "10px 14px" }}>
                  <p style={{ fontSize: 10.5, fontWeight: 600, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 3px" }}>Наблюдатель</p>
                  <p style={{ fontSize: 13, fontWeight: 500, color: "#0f172a", margin: 0 }}>{selected.reporter.full_name}</p>
                </div>
              )}

              <div style={{ background: "#f8fafc", borderRadius: 10, padding: "12px 14px" }}>
                <p style={{ fontSize: 10.5, fontWeight: 600, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 6px" }}>Описание нарушения</p>
                <p style={{ fontSize: 13.5, color: "#334155", margin: 0, lineHeight: 1.55 }}>{selected.description}</p>
              </div>

              {beforePhotos.length > 0 && (
                <div>
                  <p style={{ fontSize: 10.5, fontWeight: 600, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 8px" }}>
                    Фото до устранения ({beforePhotos.length})
                  </p>
                  <div style={{ display: "grid", gridTemplateColumns: beforePhotos.length === 1 ? "1fr" : "1fr 1fr", gap: 8 }}>
                    {beforePhotos.map((p, i) => (
                      <AuthImage key={i} minioKey={p.minio_key} style={{ height: beforePhotos.length === 1 ? 200 : 140, borderRadius: 10 }} />
                    ))}
                  </div>
                </div>
              )}

              {(selected.acknowledged_by || selected.fixed_by || selected.manager_checked_by || selected.safety_checked_by) && (
                <div style={{ background: "#f8fafc", borderRadius: 10, padding: "12px 14px" }}>
                  <p style={{ fontSize: 10.5, fontWeight: 600, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 8px" }}>
                    История согласования
                  </p>
                  <AuditRow label="Принял"              who={selected.acknowledged_by}   when={selected.acknowledged_at} />
                  <AuditRow label="Устранил"            who={selected.fixed_by}          when={selected.fixed_at} />
                  <AuditRow label="Проверил менеджер"   who={selected.manager_checked_by} when={selected.manager_checked_at} />
                  <AuditRow label="Проверил (ОТ и ТБ)" who={selected.safety_checked_by} when={selected.safety_checked_at} />
                </div>
              )}

              {selected.fix_description && (
                <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 10, padding: "12px 14px" }}>
                  <p style={{ fontSize: 10.5, fontWeight: 600, color: "#15803d", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 6px" }}>Устранение</p>
                  <p style={{ fontSize: 13.5, color: "#14532d", margin: 0, lineHeight: 1.55 }}>{selected.fix_description}</p>
                </div>
              )}

              {selected.manager_note && (
                <div style={{ background: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: 10, padding: "12px 14px" }}>
                  <p style={{ fontSize: 10.5, fontWeight: 600, color: "#1d4ed8", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 6px" }}>Комментарий менеджера</p>
                  <p style={{ fontSize: 13.5, color: "#1e3a8a", margin: 0, lineHeight: 1.55 }}>{selected.manager_note}</p>
                </div>
              )}

              {afterPhotos.length > 0 && (
                <div>
                  <p style={{ fontSize: 10.5, fontWeight: 600, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 8px" }}>
                    Фото после устранения ({afterPhotos.length})
                  </p>
                  <div style={{ display: "grid", gridTemplateColumns: afterPhotos.length === 1 ? "1fr" : "1fr 1fr", gap: 8 }}>
                    {afterPhotos.map((p, i) => (
                      <AuthImage key={i} minioKey={p.minio_key} style={{ height: afterPhotos.length === 1 ? 200 : 140, borderRadius: 10 }} />
                    ))}
                  </div>
                </div>
              )}

              {selected.safety_note && (
                <div style={{
                  background: selected.status === "approved" ? "#f0fdf4" : selected.status === "rejected" ? "#fef2f2" : "#fefce8",
                  border: `1px solid ${selected.status === "approved" ? "#bbf7d0" : selected.status === "rejected" ? "#fecaca" : "#fef08a"}`,
                  borderRadius: 10, padding: "12px 14px",
                }}>
                  <p style={{ fontSize: 10.5, fontWeight: 600, color: selected.status === "approved" ? "#15803d" : selected.status === "rejected" ? "#dc2626" : "#a16207", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 6px" }}>
                    Комментарий инженера ОТ и ТБ
                  </p>
                  <p style={{ fontSize: 13.5, color: "#334155", margin: 0, lineHeight: 1.55 }}>{selected.safety_note}</p>
                </div>
              )}

              {admin && selected.status === "approved" && (
                <div style={{ paddingTop: 4, borderTop: "1px solid #f1f5f9" }}>
                  <button onClick={() => adminClose(selected.id)}
                    style={{ padding: "10px 14px", borderRadius: 9, border: "none", fontSize: 13, fontWeight: 600, cursor: "pointer", width: "100%", background: "#0f172a", color: "#fff" }}>
                    🔒 Закрыть стоп-карту
                  </button>
                </div>
              )}
            </div>

            <div style={{ padding: "14px 20px", borderTop: "1px solid #f1f5f9", flexShrink: 0 }}>
              <button onClick={() => setSelected(null)}
                style={{ width: "100%", padding: "10px", borderRadius: 9, border: "1px solid #e2e8f0", background: "#f8fafc", color: "#64748b", fontSize: 13.5, fontWeight: 600, cursor: "pointer" }}>
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}
