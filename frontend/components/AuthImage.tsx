"use client";
import { useEffect, useState } from "react";
import { getAuthHeaders } from "@/lib/api";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export default function AuthImage({ minioKey, className, style }: {
  minioKey: string;
  className?: string;
  style?: React.CSSProperties;
}) {
  const [src, setSrc] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let objectUrl: string | null = null;
    const controller = new AbortController();
    const encodedKey = minioKey.split("/").map(encodeURIComponent).join("/");

    setSrc(null);
    setFailed(false);
    fetch(`${BASE_URL}/photos/${encodedKey}`, {
      credentials: "include",
      headers: getAuthHeaders(),
      signal: controller.signal,
    })
      .then(r => {
        if (!r.ok) throw new Error("Не удалось загрузить фото");
        return r.blob();
      })
      .then(blob => {
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
      })
      .catch((e) => {
        if (e instanceof DOMException && e.name === "AbortError") return;
        setFailed(true);
      });

    return () => {
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [minioKey]);

  if (failed) return (
    <div className={className} style={{ ...style, background: "#fef2f2", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <span style={{ color: "#dc2626", fontSize: 12 }}>Не удалось загрузить</span>
    </div>
  );

  if (!src) return (
    <div className={className} style={{ ...style, background: "#f1f5f9", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <span style={{ color: "#94a3b8", fontSize: 12 }}>⏳</span>
    </div>
  );

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt="фото" className={className} style={style} />
  );
}
