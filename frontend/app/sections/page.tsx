"use client";
import { useCallback, useEffect, useState } from "react";
import Layout from "@/components/Layout";
import { api } from "@/lib/api";

type Section = { id: number; name: string };

const PlusIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
    <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
  </svg>
);

const EditIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
  </svg>
);

const TrashIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="3 6 5 6 21 6"/>
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
  </svg>
);

const CheckIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
);

const XIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
);

const btn = (bg: string, color: string, hoverBg: string) => ({
  base: {
    display: "flex" as const, alignItems: "center" as const, gap: 5,
    padding: "6px 12px", borderRadius: 7,
    background: bg, color,
    border: "none", cursor: "pointer" as const,
    fontSize: 12.5, fontWeight: 600,
    transition: "background 0.12s",
  },
  hover: { background: hoverBg },
});

export default function SectionsPage() {
  const [sections, setSections] = useState<Section[]>([]);
  const [name, setName] = useState("");
  const [editId, setEditId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setSections(await api.get<Section[]>("/admin/sections"));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Ошибка");
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api.post("/admin/sections", { name });
      setName("");
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Ошибка");
    }
  }

  async function update(id: number) {
    setError("");
    try {
      await api.put(`/admin/sections/${id}`, { name: editName });
      setEditId(null);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Ошибка");
    }
  }

  async function remove(id: number) {
    if (!confirm("Удалить участок?")) return;
    try {
      await api.delete(`/admin/sections/${id}`);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Ошибка");
    }
  }

  return (
    <Layout>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: "#0f172a", letterSpacing: "-0.4px", margin: 0 }}>
            Участки
          </h1>
          {sections.length > 0 && (
            <span style={{
              padding: "2px 9px", borderRadius: 20, fontSize: 12, fontWeight: 600,
              background: "#fff7ed", color: "#c2410c", border: "1px solid #fed7aa",
            }}>
              {sections.length}
            </span>
          )}
        </div>
        <p style={{ fontSize: 13.5, color: "#64748b", margin: 0 }}>
          Управление производственными участками
        </p>
      </div>

      {error && (
        <div style={{
          background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 10,
          padding: "10px 14px", marginBottom: 16, fontSize: 13, color: "#dc2626",
          display: "flex", alignItems: "center", gap: 8,
        }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          {error}
        </div>
      )}

      {/* Add form */}
      <form
        onSubmit={create}
        style={{
          display: "flex",
          gap: 10,
          marginBottom: 20,
          background: "#fff",
          border: "1px solid #e2e8f0",
          borderRadius: 14,
          padding: "14px",
          boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
        }}
      >
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Название нового участка..."
          required
          style={{
            flex: 1,
            padding: "9px 14px",
            borderRadius: 9,
            border: "1px solid #e2e8f0",
            background: "#f8fafc",
            color: "#0f172a",
            fontSize: 14,
            outline: "none",
            transition: "border-color 0.15s, box-shadow 0.15s",
          }}
          onFocus={e => {
            e.target.style.borderColor = "#f97316";
            e.target.style.boxShadow = "0 0 0 3px rgba(249,115,22,0.1)";
          }}
          onBlur={e => {
            e.target.style.borderColor = "#e2e8f0";
            e.target.style.boxShadow = "none";
          }}
        />
        <button
          type="submit"
          style={{
            display: "flex",
            alignItems: "center",
            gap: 7,
            padding: "9px 18px",
            borderRadius: 9,
            border: "none",
            background: "linear-gradient(135deg, #f97316 0%, #ea580c 100%)",
            color: "white",
            fontSize: 13.5,
            fontWeight: 600,
            cursor: "pointer",
            transition: "box-shadow 0.15s, transform 0.1s",
            boxShadow: "0 2px 8px rgba(249,115,22,0.3)",
            flexShrink: 0,
          }}
          onMouseEnter={e => {
            e.currentTarget.style.boxShadow = "0 4px 14px rgba(249,115,22,0.4)";
            e.currentTarget.style.transform = "translateY(-1px)";
          }}
          onMouseLeave={e => {
            e.currentTarget.style.boxShadow = "0 2px 8px rgba(249,115,22,0.3)";
            e.currentTarget.style.transform = "translateY(0)";
          }}
        >
          <PlusIcon />
          Добавить
        </button>
      </form>

      {/* List */}
      <div style={{
        background: "#fff",
        border: "1px solid #e2e8f0",
        borderRadius: 14,
        overflow: "hidden",
        boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
      }}>
        {sections.length === 0 ? (
          <div style={{ padding: "56px 24px", textAlign: "center" }}>
            <div style={{
              width: 52, height: 52, borderRadius: 13, background: "#f1f5f9",
              display: "flex", alignItems: "center", justifyContent: "center",
              margin: "0 auto 14px",
            }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 20a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8l-7 5V8l-7 5V4a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/>
              </svg>
            </div>
            <p style={{ fontSize: 14, fontWeight: 600, color: "#64748b", margin: "0 0 4px" }}>Участков нет</p>
            <p style={{ fontSize: 13, color: "#94a3b8", margin: 0 }}>Добавьте первый участок выше</p>
          </div>
        ) : (
          sections.map((s, i) => (
            <div
              key={s.id}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "14px 18px",
                borderBottom: i < sections.length - 1 ? "1px solid #f1f5f9" : "none",
                transition: "background 0.1s",
              }}
              onMouseEnter={e => (e.currentTarget.style.background = "#fafafa")}
              onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
            >
              {editId === s.id ? (
                <input
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  autoFocus
                  style={{
                    flex: 1,
                    padding: "7px 12px",
                    borderRadius: 8,
                    border: "1.5px solid #f97316",
                    background: "#fff",
                    color: "#0f172a",
                    fontSize: 13.5,
                    outline: "none",
                    marginRight: 12,
                    boxShadow: "0 0 0 3px rgba(249,115,22,0.1)",
                  }}
                />
              ) : (
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: 8,
                    background: "linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 12, fontWeight: 700, color: "#c2410c", flexShrink: 0,
                  }}>
                    {i + 1}
                  </div>
                  <span style={{ fontSize: 14, fontWeight: 500, color: "#0f172a" }}>{s.name}</span>
                </div>
              )}

              <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
                {editId === s.id ? (
                  <>
                    <button
                      onClick={() => update(s.id)}
                      style={btn("#22c55e", "white", "#16a34a").base}
                      onMouseEnter={e => (e.currentTarget.style.background = "#16a34a")}
                      onMouseLeave={e => (e.currentTarget.style.background = "#22c55e")}
                    >
                      <CheckIcon /> Сохранить
                    </button>
                    <button
                      onClick={() => setEditId(null)}
                      style={btn("#f1f5f9", "#64748b", "#e2e8f0").base}
                      onMouseEnter={e => (e.currentTarget.style.background = "#e2e8f0")}
                      onMouseLeave={e => (e.currentTarget.style.background = "#f1f5f9")}
                    >
                      <XIcon /> Отмена
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => { setEditId(s.id); setEditName(s.name); }}
                      style={btn("#f1f5f9", "#475569", "#e2e8f0").base}
                      onMouseEnter={e => (e.currentTarget.style.background = "#e2e8f0")}
                      onMouseLeave={e => (e.currentTarget.style.background = "#f1f5f9")}
                    >
                      <EditIcon /> Изменить
                    </button>
                    <button
                      onClick={() => remove(s.id)}
                      style={btn("#fef2f2", "#dc2626", "#fee2e2").base}
                      onMouseEnter={e => (e.currentTarget.style.background = "#fee2e2")}
                      onMouseLeave={e => (e.currentTarget.style.background = "#fef2f2")}
                    >
                      <TrashIcon /> Удалить
                    </button>
                  </>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </Layout>
  );
}
