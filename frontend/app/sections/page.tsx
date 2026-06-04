"use client";
import { useEffect, useState } from "react";
import Layout from "@/components/Layout";
import { api } from "@/lib/api";

type Section = { id: number; name: string };

export default function SectionsPage() {
  const [sections, setSections] = useState<Section[]>([]);
  const [name, setName] = useState("");
  const [editId, setEditId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      setSections(await api.get<Section[]>("/admin/sections"));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Ошибка");
    }
  }

  useEffect(() => { load(); }, []);

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
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: "#0f172a" }}>Участки</h1>
        <p className="text-sm mt-1" style={{ color: "#64748b" }}>Управление производственными участками</p>
      </div>

      {error && (
        <div className="mb-4 px-4 py-3 rounded-xl text-sm font-medium"
          style={{ background: "#fef2f2", color: "#dc2626", border: "1px solid #fecaca" }}>
          {error}
        </div>
      )}

      {/* Add form */}
      <form onSubmit={create} className="flex gap-3 mb-6">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Название участка"
          className="flex-1 px-4 py-2.5 rounded-xl text-sm outline-none"
          style={{
            background: "#fff",
            border: "1px solid #e2e8f0",
            color: "#0f172a",
          }}
          required
        />
        <button type="submit"
          className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white"
          style={{ background: "#f97316" }}>
          + Добавить
        </button>
      </form>

      {/* List */}
      <div className="rounded-2xl overflow-hidden" style={{ border: "1px solid #e2e8f0", background: "#fff" }}>
        {sections.length === 0 ? (
          <div className="px-6 py-12 text-center text-sm" style={{ color: "#94a3b8" }}>
            Участков нет. Добавьте первый.
          </div>
        ) : (
          sections.map((s, i) => (
            <div key={s.id}
              className="flex items-center justify-between px-5 py-4"
              style={{
                borderBottom: i < sections.length - 1 ? "1px solid #f1f5f9" : "none",
              }}>
              {editId === s.id ? (
                <input
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="flex-1 px-3 py-1.5 rounded-lg text-sm mr-3 outline-none"
                  style={{ border: "1px solid #e2e8f0", color: "#0f172a" }}
                  autoFocus
                />
              ) : (
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold"
                    style={{ background: "#fff7ed", color: "#f97316" }}>
                    {i + 1}
                  </div>
                  <span className="font-medium text-sm" style={{ color: "#0f172a" }}>{s.name}</span>
                </div>
              )}
              <div className="flex gap-2">
                {editId === s.id ? (
                  <>
                    <button onClick={() => update(s.id)}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold text-white"
                      style={{ background: "#22c55e" }}>
                      Сохранить
                    </button>
                    <button onClick={() => setEditId(null)}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold"
                      style={{ background: "#f1f5f9", color: "#64748b" }}>
                      Отмена
                    </button>
                  </>
                ) : (
                  <>
                    <button onClick={() => { setEditId(s.id); setEditName(s.name); }}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold"
                      style={{ background: "#f1f5f9", color: "#475569" }}>
                      Изменить
                    </button>
                    <button onClick={() => remove(s.id)}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold"
                      style={{ background: "#fef2f2", color: "#dc2626" }}>
                      Удалить
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
