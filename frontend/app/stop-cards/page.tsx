"use client";
import { useEffect, useRef, useState } from "react";
import Layout from "@/components/Layout";
import AuthImage from "@/components/AuthImage";
import { api, getRole, isAdmin } from "@/lib/api";

type Photo = { id: number; minio_key: string; photo_type: string };
type UserBrief = { id: number; full_name: string };

type StopCard = {
  id: number;
  reporter_id: number;
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
  safety_note: string | null;
  safety_checked_by: UserBrief | null;
  safety_checked_at: string | null;
  created_at: string;
  closed_at: string | null;
  photos: Photo[];
};

const STATUS_LABELS: Record<string, string> = {
  created:      "Создана",
  under_review: "На рассмотрении",
  in_progress:  "В работе",
  safety_check: "Проверка ОТ и ТБ",
  approved:     "Разрешено к работе",
  rejected:     "Запрещено",
  closed:       "Закрыто",
};

const STATUS_STYLE: Record<string, { bg: string; color: string; dot: string }> = {
  created:      { bg: "#f8fafc",  color: "#475569", dot: "#94a3b8" },
  under_review: { bg: "#eff6ff",  color: "#1d4ed8", dot: "#3b82f6" },
  in_progress:  { bg: "#fff7ed",  color: "#c2410c", dot: "#f97316" },
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
  const [role, setRole] = useState("");
  const [admin, setAdmin] = useState(false);

  // Fix modal state
  const [fixDesc, setFixDesc] = useState("");
  const [fixFiles, setFixFiles] = useState<FileList | null>(null);
  const [fixLoading, setFixLoading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  // Safety engineer decision
  const [safetyNote, setSafetyNote] = useState("");
  const [safetyLoading, setSafetyLoading] = useState(false);

  useEffect(() => {
    const r = getRole() ?? "";
    setRole(r);
    setAdmin(isAdmin());
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

  function openCard(c: StopCard) {
    setSelected(c);
    setFixDesc("");
    setFixFiles(null);
    setSafetyNote("");
  }

  // ── Менеджер: принять карту ──────────────────────────────────────────────
  async function acknowledge(cardId: number) {
    try {
      const updated = await api.patch<StopCard>(`/manager/stop-cards/${cardId}/acknowledge`);
      setSelected(updated);
      load();
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Ошибка"); }
  }

  // ── Менеджер: загрузить устранение ───────────────────────────────────────
  async function submitFix(cardId: number) {
    if (!fixDesc.trim()) return;
    setFixLoading(true);
    try {
      const fd = new FormData();
      fd.append("fix_description", fixDesc);
      if (fixFiles) {
        Array.from(fixFiles).forEach(f => fd.append("photos", f));
      }
      const updated = await api.postForm<StopCard>(`/manager/stop-cards/${cardId}/fix`, fd);
      setSelected(updated);
      setFixDesc("");
      setFixFiles(null);
      if (fileRef.current) fileRef.current.value = "";
      load();
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Ошибка"); }
    finally { setFixLoading(false); }
  }

  // ── Инженер ОТ и ТБ ──────────────────────────────────────────────────────
  async function safetyAction(cardId: number, action: "approve" | "reject" | "revision") {
    setSafetyLoading(true);
    try {
      const updated = await api.patch<StopCard>(
        `/safety-engineer/stop-cards/${cardId}/${action}`,
        { note: safetyNote || null }
      );
      setSelected(updated);
      setSafetyNote("");
      load();
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Ошибка"); }
    finally { setSafetyLoading(false); }
  }

  // ── Администратор: закрыть ────────────────────────────────────────────────
  async function adminClose(cardId: number) {
    try {
      const updated = await api.patch<StopCard>(`/admin/stop-cards/${cardId}/close`);
      setSelected(updated);
      load();
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Ошибка"); }
  }

  const allStatuses = ["all", "created", "under_review", "in_progress", "safety_check", "approved", "rejected", "closed"];
  const beforePhotos = selected?.photos.filter(p => p.photo_type === "before") ?? [];
  const afterPhotos = selected?.photos.filter(p => p.photo_type === "after") ?? [];

  const btnBase: React.CSSProperties = {
    padding: "10px 14px", borderRadius: 9, border: "none",
    fontSize: 13, fontWeight: 600, cursor: "pointer", width: "100%",
    transition: "opacity 0.12s",
  };

  return (
    <Layout>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: "#0f172a", letterSpacing: "-0.4px", margin: 0 }}>
            Стоп-карты
          </h1>
          {cards.length > 0 && (
            <span style={{ padding: "2px 9px", borderRadius: 20, fontSize: 12, fontWeight: 600, background: "#f1f5f9", color: "#475569", border: "1px solid #e2e8f0" }}>
              {cards.length}
            </span>
          )}
        </div>
        <p style={{ fontSize: 13.5, color: "#64748b", margin: 0 }}>
          {role === "safety_engineer" ? "Карты на проверке ОТ и ТБ" : "Журнал стоп-карт и нарушений безопасности"}
        </p>
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
                  cursor: "pointer", transition: "all 0.12s ease",
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
            <input type="number" value={month} onChange={e => setMonth(e.target.value)} placeholder="Месяц" min={1} max={12}
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
            <div style={{ width: 52, height: 52, borderRadius: 13, background: "#f1f5f9", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 14px" }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
            </div>
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
                onClick={() => openCard(c)}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <div style={{
                    width: 36, height: 36, borderRadius: 9,
                    background: "linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 11.5, fontWeight: 700, color: "#c2410c", flexShrink: 0,
                  }}>
                    #{c.id}
                  </div>
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
            {/* Modal header */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "18px 20px", borderBottom: "1px solid #f1f5f9", flexShrink: 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{
                  width: 34, height: 34, borderRadius: 9,
                  background: "linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 11, fontWeight: 700, color: "#c2410c",
                }}>#{selected.id}</div>
                <h2 style={{ fontSize: 15, fontWeight: 700, color: "#0f172a", margin: 0 }}>
                  Стоп-карта #{selected.id}
                </h2>
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
                  style={{ background: "#f1f5f9", border: "none", borderRadius: 7, padding: "6px", cursor: "pointer", color: "#64748b", display: "flex", transition: "background 0.12s" }}
                  onMouseEnter={e => (e.currentTarget.style.background = "#e2e8f0")}
                  onMouseLeave={e => (e.currentTarget.style.background = "#f1f5f9")}>
                  <XIcon />
                </button>
              </div>
            </div>

            {/* Modal body */}
            <div style={{ padding: "20px", overflowY: "auto", flex: 1, display: "flex", flexDirection: "column", gap: 14 }}>

              {/* Info grid */}
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

              {/* Фото ДО */}
              {beforePhotos.length > 0 && (
                <div>
                  <p style={{ fontSize: 10.5, fontWeight: 600, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 8px" }}>
                    Фото до устранения ({beforePhotos.length})
                  </p>
                  <div style={{ display: "grid", gridTemplateColumns: beforePhotos.length === 1 ? "1fr" : "1fr 1fr", gap: 8 }}>
                    {beforePhotos.map((p, i) => (
                      <AuthImage key={i} minioKey={p.minio_key} className="w-full rounded-xl object-cover"
                        style={{ height: beforePhotos.length === 1 ? 200 : 140, borderRadius: 10 }} />
                    ))}
                  </div>
                </div>
              )}

              {/* Аудит цепочка */}
              {(selected.acknowledged_by || selected.fixed_by || selected.safety_checked_by) && (
                <div style={{ background: "#f8fafc", borderRadius: 10, padding: "12px 14px" }}>
                  <p style={{ fontSize: 10.5, fontWeight: 600, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 8px" }}>
                    История согласования
                  </p>
                  <AuditRow label="Принял"              who={selected.acknowledged_by}   when={selected.acknowledged_at} />
                  <AuditRow label="Устранил"            who={selected.fixed_by}          when={selected.fixed_at} />
                  <AuditRow label="Проверил (ОТ и ТБ)" who={selected.safety_checked_by} when={selected.safety_checked_at} />
                </div>
              )}

              {/* Описание устранения */}
              {selected.fix_description && (
                <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 10, padding: "12px 14px" }}>
                  <p style={{ fontSize: 10.5, fontWeight: 600, color: "#15803d", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 6px" }}>
                    Описание устранения
                  </p>
                  <p style={{ fontSize: 13.5, color: "#14532d", margin: 0, lineHeight: 1.55 }}>{selected.fix_description}</p>
                </div>
              )}

              {/* Фото ПОСЛЕ */}
              {afterPhotos.length > 0 && (
                <div>
                  <p style={{ fontSize: 10.5, fontWeight: 600, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 8px" }}>
                    Фото после устранения ({afterPhotos.length})
                  </p>
                  <div style={{ display: "grid", gridTemplateColumns: afterPhotos.length === 1 ? "1fr" : "1fr 1fr", gap: 8 }}>
                    {afterPhotos.map((p, i) => (
                      <AuthImage key={i} minioKey={p.minio_key} className="w-full rounded-xl object-cover"
                        style={{ height: afterPhotos.length === 1 ? 200 : 140, borderRadius: 10 }} />
                    ))}
                  </div>
                </div>
              )}

              {/* Комментарий инженера */}
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

              {/* ── Действия менеджера ─────────────────────────────────────────── */}
              {(role === "manager" || admin) && (
                <>
                  {selected.status === "created" && (
                    <div style={{ paddingTop: 4, borderTop: "1px solid #f1f5f9" }}>
                      <button onClick={() => acknowledge(selected.id)}
                        style={{ ...btnBase, background: "linear-gradient(135deg, #f97316 0%, #ea580c 100%)", color: "#fff", boxShadow: "0 2px 8px rgba(249,115,22,0.3)" }}>
                        ✅ Принять стоп-карту (остановить работу)
                      </button>
                    </div>
                  )}

                  {(selected.status === "under_review" || selected.status === "in_progress") && (
                    <div style={{ paddingTop: 4, borderTop: "1px solid #f1f5f9", display: "flex", flexDirection: "column", gap: 10 }}>
                      <p style={{ fontSize: 12, fontWeight: 600, color: "#64748b", margin: 0, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                        Устранение нарушения
                      </p>
                      {selected.safety_note && selected.status === "in_progress" && (
                        <div style={{ background: "#fefce8", border: "1px solid #fef08a", borderRadius: 9, padding: "10px 12px" }}>
                          <p style={{ fontSize: 12, fontWeight: 600, color: "#a16207", margin: "0 0 3px" }}>Замечания инженера:</p>
                          <p style={{ fontSize: 12.5, color: "#713f12", margin: 0 }}>{selected.safety_note}</p>
                        </div>
                      )}
                      <textarea
                        value={fixDesc}
                        onChange={e => setFixDesc(e.target.value)}
                        placeholder="Опишите что было сделано для устранения нарушения..."
                        rows={3}
                        style={{
                          width: "100%", padding: "10px 12px", borderRadius: 9,
                          border: "1px solid #e2e8f0", background: "#f8fafc",
                          color: "#0f172a", fontSize: 13, outline: "none",
                          resize: "vertical", fontFamily: "inherit", boxSizing: "border-box",
                        }}
                        onFocus={e => { e.target.style.borderColor = "#f97316"; e.target.style.boxShadow = "0 0 0 3px rgba(249,115,22,0.1)"; }}
                        onBlur={e => { e.target.style.borderColor = "#e2e8f0"; e.target.style.boxShadow = "none"; }}
                      />
                      <div>
                        <label style={{ display: "block", fontSize: 11.5, fontWeight: 600, color: "#64748b", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                          Фото после устранения
                        </label>
                        <input ref={fileRef} type="file" accept="image/*" multiple
                          onChange={e => setFixFiles(e.target.files)}
                          style={{ fontSize: 12.5, color: "#64748b", width: "100%" }} />
                        {fixFiles && fixFiles.length > 0 && (
                          <p style={{ fontSize: 12, color: "#64748b", margin: "4px 0 0" }}>{fixFiles.length} файл(ов) выбрано</p>
                        )}
                      </div>
                      <button
                        onClick={() => submitFix(selected.id)}
                        disabled={!fixDesc.trim() || fixLoading}
                        style={{
                          ...btnBase,
                          background: fixDesc.trim() ? "linear-gradient(135deg, #22c55e 0%, #16a34a 100%)" : "#f1f5f9",
                          color: fixDesc.trim() ? "#fff" : "#94a3b8",
                          cursor: fixDesc.trim() ? "pointer" : "not-allowed",
                          boxShadow: fixDesc.trim() ? "0 2px 8px rgba(34,197,94,0.25)" : "none",
                        }}>
                        {fixLoading ? "Отправляем..." : "📤 Отправить на проверку ОТ и ТБ"}
                      </button>
                    </div>
                  )}
                </>
              )}

              {/* ── Действия инженера ОТ и ТБ ────────────────────────────────── */}
              {(role === "safety_engineer" || admin) && selected.status === "safety_check" && (
                <div style={{ paddingTop: 4, borderTop: "1px solid #f1f5f9", display: "flex", flexDirection: "column", gap: 10 }}>
                  <p style={{ fontSize: 12, fontWeight: 600, color: "#64748b", margin: 0, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                    Решение инженера ОТ и ТБ
                  </p>
                  <textarea
                    value={safetyNote}
                    onChange={e => setSafetyNote(e.target.value)}
                    placeholder="Комментарий (необязательно)..."
                    rows={2}
                    style={{
                      width: "100%", padding: "10px 12px", borderRadius: 9,
                      border: "1px solid #e2e8f0", background: "#f8fafc",
                      color: "#0f172a", fontSize: 13, outline: "none",
                      resize: "none", fontFamily: "inherit", boxSizing: "border-box",
                    }}
                  />
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
                    <button onClick={() => safetyAction(selected.id, "approve")} disabled={safetyLoading}
                      style={{ ...btnBase, background: "linear-gradient(135deg, #22c55e 0%, #16a34a 100%)", color: "#fff", boxShadow: "0 2px 8px rgba(34,197,94,0.25)", fontSize: 12 }}>
                      ✅ Разрешить
                    </button>
                    <button onClick={() => safetyAction(selected.id, "revision")} disabled={safetyLoading}
                      style={{ ...btnBase, background: "linear-gradient(135deg, #f97316 0%, #ea580c 100%)", color: "#fff", boxShadow: "0 2px 8px rgba(249,115,22,0.25)", fontSize: 12 }}>
                      🔄 Доработать
                    </button>
                    <button onClick={() => safetyAction(selected.id, "reject")} disabled={safetyLoading}
                      style={{ ...btnBase, background: "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)", color: "#fff", boxShadow: "0 2px 8px rgba(239,68,68,0.25)", fontSize: 12 }}>
                      ⛔ Запретить
                    </button>
                  </div>
                </div>
              )}

              {/* ── Администратор: закрыть ────────────────────────────────────── */}
              {admin && selected.status === "approved" && (
                <div style={{ paddingTop: 4, borderTop: "1px solid #f1f5f9" }}>
                  <button onClick={() => adminClose(selected.id)}
                    style={{ ...btnBase, background: "#0f172a", color: "#fff" }}>
                    🔒 Закрыть стоп-карту
                  </button>
                </div>
              )}
            </div>

            {/* Modal footer */}
            <div style={{ padding: "14px 20px", borderTop: "1px solid #f1f5f9", flexShrink: 0 }}>
              <button onClick={() => setSelected(null)}
                style={{ width: "100%", padding: "10px", borderRadius: 9, border: "1px solid #e2e8f0", background: "#f8fafc", color: "#64748b", fontSize: 13.5, fontWeight: 600, cursor: "pointer", transition: "background 0.12s" }}
                onMouseEnter={e => (e.currentTarget.style.background = "#f1f5f9")}
                onMouseLeave={e => (e.currentTarget.style.background = "#f8fafc")}>
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}
