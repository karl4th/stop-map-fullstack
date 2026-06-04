"use client";
import { useEffect, useState } from "react";
import Layout from "@/components/Layout";
import AuthImage from "@/components/AuthImage";
import { api, isAdmin } from "@/lib/api";

type Photo = { id: number; minio_key: string };
type StopCard = {
  id: number;
  reporter_id: number;
  violator_name: string;
  section_id: number;
  description: string;
  status: string;
  dispute_reason: string | null;
  created_at: string;
  photos: Photo[];
};

const STATUS_LABELS: Record<string, string> = {
  issued: "Выдана", acknowledged: "Принята", closed: "Закрыта", disputed: "Оспорена",
};
const STATUS_STYLE: Record<string, { bg: string; color: string }> = {
  issued:       { bg: "#eff6ff", color: "#1d4ed8" },
  acknowledged: { bg: "#fefce8", color: "#a16207" },
  closed:       { bg: "#f0fdf4", color: "#15803d" },
  disputed:     { bg: "#fef2f2", color: "#dc2626" },
};

export default function StopCardsPage() {
  const [cards, setCards] = useState<StopCard[]>([]);
  const [statusFilter, setStatusFilter] = useState("all");
  const [year, setYear] = useState("");
  const [month, setMonth] = useState("");
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<StopCard | null>(null);
  const [photoUrls, setPhotoUrls] = useState<string[]>([]);
  const [disputeReason, setDisputeReason] = useState("");
  const [admin, setAdmin] = useState(false);

  useEffect(() => { setAdmin(isAdmin()); }, []);

  const prefix = admin ? "/admin" : "/manager";

  async function load() {
    setError("");
    try {
      let path = `${prefix}/stop-cards`;
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

  useEffect(() => { load(); }, [statusFilter, admin]);

  async function action(cardId: number, act: "acknowledge" | "close" | "dispute") {
    try {
      const body = act === "dispute" ? { reason: disputeReason } : undefined;
      const updated = await api.patch<StopCard>(`/manager/stop-cards/${cardId}/${act}`, body);
      setSelected(updated);
      setDisputeReason("");
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Ошибка");
    }
  }

  const filters = ["all", "issued", "acknowledged", "closed", "disputed"];

  return (
    <Layout>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "#0f172a" }}>Стоп-карты</h1>
          <p className="text-sm mt-1" style={{ color: "#64748b" }}>{cards.length} записей</p>
        </div>
      </div>

      {error && (
        <div className="mb-4 px-4 py-3 rounded-xl text-sm font-medium"
          style={{ background: "#fef2f2", color: "#dc2626", border: "1px solid #fecaca" }}>
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-5">
        <div className="flex gap-2 flex-wrap">
          {filters.map(f => (
            <button key={f} onClick={() => setStatusFilter(f)}
              className="px-3 py-2 rounded-xl text-xs font-semibold transition-all"
              style={statusFilter === f
                ? { background: "#0f172a", color: "#fff" }
                : { background: "#fff", color: "#64748b", border: "1px solid #e2e8f0" }}>
              {f === "all" ? "Все" : STATUS_LABELS[f]}
            </button>
          ))}
        </div>
        {admin && (
          <div className="flex gap-2 ml-auto">
            <input type="number" value={year} onChange={e => setYear(e.target.value)}
              placeholder="Год" className="px-3 py-2 rounded-xl text-xs w-20 outline-none"
              style={{ border: "1px solid #e2e8f0", color: "#0f172a", background: "#fff" }} />
            <input type="number" value={month} onChange={e => setMonth(e.target.value)}
              placeholder="Месяц" min={1} max={12} className="px-3 py-2 rounded-xl text-xs w-24 outline-none"
              style={{ border: "1px solid #e2e8f0", color: "#0f172a", background: "#fff" }} />
            <button onClick={load}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-white"
              style={{ background: "#0f172a" }}>
              Применить
            </button>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="rounded-2xl overflow-hidden" style={{ border: "1px solid #e2e8f0", background: "#fff" }}>
        {cards.length === 0 ? (
          <div className="px-6 py-12 text-center text-sm" style={{ color: "#94a3b8" }}>
            Стоп-карт нет
          </div>
        ) : (
          cards.map((c, i) => {
            const ss = STATUS_STYLE[c.status] ?? { bg: "#f1f5f9", color: "#475569" };
            return (
              <div key={c.id}
                className="flex items-center justify-between px-5 py-4 cursor-pointer transition-colors"
                style={{
                  borderBottom: i < cards.length - 1 ? "1px solid #f1f5f9" : "none",
                }}
                onMouseEnter={e => (e.currentTarget.style.background = "#fafafa")}
                onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
                onClick={() => {
                  setSelected(c);
                  setDisputeReason("");
                  setPhotoUrls(c.photos.map(p => p.minio_key));
                }}>
                <div className="flex items-center gap-4">
                  <div className="w-9 h-9 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0"
                    style={{ background: "#fff7ed", color: "#f97316" }}>
                    #{c.id}
                  </div>
                  <div>
                    <p className="font-semibold text-sm" style={{ color: "#0f172a" }}>{c.violator_name}</p>
                    <p className="text-xs mt-0.5 line-clamp-1 max-w-xs" style={{ color: "#94a3b8" }}>
                      {c.description}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  {c.photos.length > 0 && (
                    <span className="text-xs" style={{ color: "#94a3b8" }}>📎 {c.photos.length}</span>
                  )}
                  <span className="text-xs" style={{ color: "#94a3b8" }}>
                    {new Date(c.created_at).toLocaleDateString("ru")}
                  </span>
                  <span className="px-2.5 py-1 rounded-lg text-xs font-semibold"
                    style={{ background: ss.bg, color: ss.color }}>
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
        <div className="fixed inset-0 flex items-center justify-center z-50"
          style={{ background: "rgba(0,0,0,0.5)" }}
          onClick={() => setSelected(null)}>
          <div className="rounded-2xl w-full max-w-md shadow-2xl overflow-hidden"
            style={{ background: "#fff" }}
            onClick={e => e.stopPropagation()}>

            {/* Header */}
            <div className="px-6 py-5" style={{ borderBottom: "1px solid #f1f5f9" }}>
              <div className="flex items-center justify-between">
                <h2 className="font-bold text-lg" style={{ color: "#0f172a" }}>
                  Стоп-карта #{selected.id}
                </h2>
                <span className="px-2.5 py-1 rounded-lg text-xs font-semibold"
                  style={{
                    background: STATUS_STYLE[selected.status]?.bg ?? "#f1f5f9",
                    color: STATUS_STYLE[selected.status]?.color ?? "#475569",
                  }}>
                  {STATUS_LABELS[selected.status]}
                </span>
              </div>
            </div>

            {/* Body */}
            <div className="px-6 py-5 space-y-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide mb-1" style={{ color: "#94a3b8" }}>Нарушитель</p>
                <p className="text-sm font-semibold" style={{ color: "#0f172a" }}>{selected.violator_name}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide mb-1" style={{ color: "#94a3b8" }}>Описание</p>
                <p className="text-sm" style={{ color: "#334155" }}>{selected.description}</p>
              </div>
              {selected.dispute_reason && (
                <div className="px-4 py-3 rounded-xl" style={{ background: "#fef2f2" }}>
                  <p className="text-xs font-semibold mb-1" style={{ color: "#dc2626" }}>Причина оспаривания</p>
                  <p className="text-sm" style={{ color: "#7f1d1d" }}>{selected.dispute_reason}</p>
                </div>
              )}
              <div className="flex gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide mb-1" style={{ color: "#94a3b8" }}>Дата</p>
                  <p className="text-sm" style={{ color: "#334155" }}>{new Date(selected.created_at).toLocaleString("ru")}</p>
                </div>
                {photoUrls.length > 0 && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: "#94a3b8" }}>
                    Фото ({photoUrls.length})
                  </p>
                  <div className="grid grid-cols-2 gap-2">
                    {photoUrls.map((key, i) => (
                      <AuthImage
                        key={i}
                        minioKey={key}
                        className="w-full rounded-lg object-cover"
                        style={{ height: 120 }}
                      />
                    ))}
                  </div>
                </div>
              )}
              </div>

              {/* Manager actions */}
              {!admin && selected.status !== "closed" && selected.status !== "disputed" && (
                <div className="pt-2 space-y-2" style={{ borderTop: "1px solid #f1f5f9" }}>
                  {selected.status === "issued" && (
                    <button onClick={() => action(selected.id, "acknowledge")}
                      className="w-full py-2.5 rounded-xl text-sm font-semibold text-white"
                      style={{ background: "#f97316" }}>
                      Принять стоп-карту
                    </button>
                  )}
                  <button onClick={() => action(selected.id, "close")}
                    className="w-full py-2.5 rounded-xl text-sm font-semibold text-white"
                    style={{ background: "#22c55e" }}>
                    Закрыть
                  </button>
                  <input value={disputeReason} onChange={e => setDisputeReason(e.target.value)}
                    placeholder="Причина оспаривания..."
                    className="w-full px-4 py-2.5 rounded-xl text-sm outline-none"
                    style={{ border: "1px solid #e2e8f0", color: "#0f172a" }} />
                  <button onClick={() => action(selected.id, "dispute")}
                    disabled={!disputeReason}
                    className="w-full py-2.5 rounded-xl text-sm font-semibold text-white disabled:opacity-40"
                    style={{ background: "#ef4444" }}>
                    Оспорить
                  </button>
                </div>
              )}
            </div>

            <div className="px-6 pb-5">
              <button onClick={() => setSelected(null)}
                className="w-full py-2.5 rounded-xl text-sm font-semibold"
                style={{ background: "#f1f5f9", color: "#64748b" }}>
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}
