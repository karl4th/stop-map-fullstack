"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, decodeRole } from "@/lib/api";

const EyeIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
    <circle cx="12" cy="12" r="3"/>
  </svg>
);

const EyeOffIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
    <line x1="1" y1="1" x2="23" y2="23"/>
  </svg>
);

const SpinnerIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
    <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"
      style={{ animation: "spin 1s linear infinite", transformOrigin: "center" }}/>
  </svg>
);

function maskPhone(raw: string): string {
  const digits = raw.replace(/\D/g, "").replace(/^[78]/, "").slice(0, 10);
  let r = "+7";
  if (digits.length > 0) r += " (" + digits.slice(0, 3);
  if (digits.length >= 3) r += ") " + digits.slice(3, 6);
  if (digits.length >= 6) r += "-" + digits.slice(6, 8);
  if (digits.length >= 8) r += "-" + digits.slice(8, 10);
  return r;
}

function rawPhone(masked: string): string {
  const digits = masked.replace(/\D/g, "");
  return "+" + (digits.startsWith("7") ? digits : "7" + digits);
}

export default function LoginPage() {
  const router = useRouter();
  const [phone, setPhone] = useState("+7");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await api.post<{ access_token: string }>("/admin/auth/login", { phone: rawPhone(phone), password });
      const role = decodeRole(data.access_token);
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("role", role);
      if (role === "manager") router.push("/users");
      else if (role === "safety_engineer") router.push("/stop-cards");
      else router.push("/sections");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Ошибка входа");
    } finally {
      setLoading(false);
    }
  }

  const inputStyle: React.CSSProperties = {
    width: "100%",
    padding: "11px 14px",
    borderRadius: 10,
    border: "1px solid rgba(255,255,255,0.08)",
    background: "#0d1117",
    color: "#f1f5f9",
    fontSize: 14,
    outline: "none",
    transition: "border-color 0.15s ease, box-shadow 0.15s ease",
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0d1117",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: 24,
      position: "relative",
      overflow: "hidden",
    }}>
      {/* Background grid */}
      <div style={{
        position: "absolute",
        inset: 0,
        backgroundImage: `
          linear-gradient(rgba(249,115,22,0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(249,115,22,0.03) 1px, transparent 1px)
        `,
        backgroundSize: "40px 40px",
        pointerEvents: "none",
      }} />
      {/* Glow */}
      <div style={{
        position: "absolute",
        top: "35%",
        left: "50%",
        transform: "translate(-50%, -50%)",
        width: 700,
        height: 700,
        background: "radial-gradient(circle, rgba(249,115,22,0.07) 0%, transparent 65%)",
        pointerEvents: "none",
      }} />

      <div style={{ width: "100%", maxWidth: 400, position: "relative", zIndex: 1 }} className="animate-fade">
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            width: 54,
            height: 54,
            borderRadius: 15,
            background: "linear-gradient(135deg, #f97316 0%, #dc2626 100%)",
            boxShadow: "0 8px 28px rgba(249,115,22,0.45)",
            marginBottom: 16,
          }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.25" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: "#f1f5f9", letterSpacing: "-0.5px", margin: "0 0 6px" }}>
            StopMap
          </h1>
          <p style={{ fontSize: 13.5, color: "#64748b", margin: 0 }}>
            Войдите в панель управления
          </p>
        </div>

        {/* Card */}
        <div style={{
          background: "#161b22",
          border: "1px solid rgba(255,255,255,0.07)",
          borderRadius: 18,
          padding: "28px 28px",
          boxShadow: "0 24px 60px rgba(0,0,0,0.5)",
        }}>
          {error && (
            <div style={{
              background: "rgba(239,68,68,0.1)",
              border: "1px solid rgba(239,68,68,0.2)",
              borderRadius: 10,
              padding: "10px 14px",
              marginBottom: 20,
              fontSize: 13,
              color: "#fca5a5",
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "#94a3b8", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Номер телефона
              </label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(maskPhone(e.target.value))}
                placeholder="+7 (___) ___-__-__"
                required
                style={inputStyle}
                onFocus={e => {
                  e.target.style.borderColor = "rgba(249,115,22,0.5)";
                  e.target.style.boxShadow = "0 0 0 3px rgba(249,115,22,0.12)";
                }}
                onBlur={e => {
                  e.target.style.borderColor = "rgba(255,255,255,0.08)";
                  e.target.style.boxShadow = "none";
                }}
              />
            </div>

            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "#94a3b8", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Пароль
              </label>
              <div style={{ position: "relative" }}>
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  style={{ ...inputStyle, paddingRight: 44 }}
                  onFocus={e => {
                    e.target.style.borderColor = "rgba(249,115,22,0.5)";
                    e.target.style.boxShadow = "0 0 0 3px rgba(249,115,22,0.12)";
                  }}
                  onBlur={e => {
                    e.target.style.borderColor = "rgba(255,255,255,0.08)";
                    e.target.style.boxShadow = "none";
                  }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: "absolute",
                    right: 12,
                    top: "50%",
                    transform: "translateY(-50%)",
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    color: "#475569",
                    display: "flex",
                    alignItems: "center",
                    padding: 4,
                    borderRadius: 5,
                    transition: "color 0.12s",
                  }}
                  onMouseEnter={e => (e.currentTarget.style.color = "#94a3b8")}
                  onMouseLeave={e => (e.currentTarget.style.color = "#475569")}
                >
                  {showPassword ? <EyeOffIcon /> : <EyeIcon />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                width: "100%",
                padding: "12px",
                borderRadius: 10,
                border: "none",
                background: loading
                  ? "rgba(249,115,22,0.4)"
                  : "linear-gradient(135deg, #f97316 0%, #ea580c 100%)",
                color: "white",
                fontSize: 14,
                fontWeight: 600,
                cursor: loading ? "not-allowed" : "pointer",
                transition: "all 0.15s ease",
                boxShadow: loading ? "none" : "0 4px 16px rgba(249,115,22,0.35)",
                marginTop: 4,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 8,
              }}
              onMouseEnter={e => { if (!loading) e.currentTarget.style.boxShadow = "0 6px 22px rgba(249,115,22,0.5)"; }}
              onMouseLeave={e => { if (!loading) e.currentTarget.style.boxShadow = "0 4px 16px rgba(249,115,22,0.35)"; }}
            >
              {loading ? <><SpinnerIcon /> Входим...</> : "Войти в систему"}
            </button>
          </form>
        </div>

        <p style={{ textAlign: "center", marginTop: 20, fontSize: 12, color: "#334155" }}>
          StopMap · Система управления безопасностью
        </p>
      </div>
    </div>
  );
}
