"use client";
import { useEffect, useState } from "react";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export default function AuthImage({ minioKey, className, style }: {
  minioKey: string;
  className?: string;
  style?: React.CSSProperties;
}) {
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    let objectUrl: string | null = null;
    const token = localStorage.getItem("token");

    fetch(`${BASE_URL}/photos/${minioKey}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.blob())
      .then(blob => {
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
      })
      .catch(() => {});

    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [minioKey]);

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
