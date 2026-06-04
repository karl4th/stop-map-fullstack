"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, decodeRole } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await api.post<{ access_token: string }>("/admin/auth/login", { phone, password });
      const role = decodeRole(data.access_token);
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("role", role);
      router.push(role === "manager" ? "/users" : "/sections");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Ошибка входа");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: "#0f172a" }}>
      <div style={{ width: 400 }}>
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-4"
            style={{ background: "#f97316" }}>
            <span className="text-white text-2xl font-bold">S</span>
          </div>
          <h1 className="text-2xl font-bold text-white">StopMap</h1>
          <p className="mt-1" style={{ color: "#94a3b8" }}>Панель управления</p>
        </div>

        <form onSubmit={handleSubmit}
          className="rounded-2xl p-8"
          style={{ background: "#1e293b", border: "1px solid #334155" }}>

          {error && (
            <div className="mb-5 px-4 py-3 rounded-xl text-sm font-medium"
              style={{ background: "#450a0a", color: "#fca5a5", border: "1px solid #7f1d1d" }}>
              {error}
            </div>
          )}

          <div className="mb-5">
            <label className="block text-sm font-semibold mb-2" style={{ color: "#cbd5e1" }}>
              Номер телефона
            </label>
            <input
              type="text"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+77000000000"
              className="w-full px-4 py-3 rounded-xl text-white text-sm outline-none transition-all"
              style={{
                background: "#0f172a",
                border: "1px solid #334155",
                color: "#f1f5f9",
              }}
              required
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-semibold mb-2" style={{ color: "#cbd5e1" }}>
              Пароль
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-4 py-3 rounded-xl text-white text-sm outline-none"
              style={{
                background: "#0f172a",
                border: "1px solid #334155",
                color: "#f1f5f9",
              }}
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl font-semibold text-white transition-opacity"
            style={{ background: "#f97316", opacity: loading ? 0.6 : 1 }}>
            {loading ? "Входим..." : "Войти"}
          </button>
        </form>
      </div>
    </div>
  );
}
