import { ImageResponse } from "next/og";
import { profile } from "@/content/profile";

export const alt = `${profile.name}: I build software that notices.`;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpengraphImage() {
  return new ImageResponse(
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        padding: 64,
        background: "#e5ece0",
        backgroundImage:
          "linear-gradient(#dae3d4 1px, transparent 1px), linear-gradient(90deg, #dae3d4 1px, transparent 1px)",
        backgroundSize: "30px 30px",
        color: "#12211c",
      }}
    >
      <div style={{ fontSize: 28 }}>{`${profile.name}, ${profile.location}`}</div>
      <div style={{ display: "flex", flexDirection: "column" }}>
        <div style={{ fontSize: 56 }}>I build software that</div>
        <div style={{ fontSize: 200, fontWeight: 800, color: "#1c2bbe", lineHeight: 1 }}>notices.</div>
      </div>
    </div>,
    size,
  );
}
