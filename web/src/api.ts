import type { LatLon, WSMessage, WorldState } from "./types";

const HTTP_BASE = ""; // dev: Vite proxies; prod: same-origin
const WS_BASE = (() => {
  if (typeof window === "undefined") return "";
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${window.location.host}`;
})();

export async function fetchState(): Promise<WorldState | null> {
  const r = await fetch(`${HTTP_BASE}/api/state`);
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`GET /api/state failed: ${r.status}`);
  return (await r.json()) as WorldState;
}

export async function buildState(
  markers: LatLon[],
  rectangle: LatLon[],
): Promise<WorldState> {
  const fd = new FormData();
  fd.append("marker_data", JSON.stringify(markers));
  fd.append("rectangle_data", JSON.stringify(rectangle));
  const r = await fetch(`${HTTP_BASE}/api/state/build`, {
    method: "POST",
    body: fd,
  });
  if (!r.ok) throw new Error(`POST /api/state/build failed: ${await r.text()}`);
  return (await r.json()) as WorldState;
}

export async function saveCamera(
  cameraCoords: number[][],
  centerCoords: LatLon,
): Promise<void> {
  const r = await fetch(`${HTTP_BASE}/api/state/camera`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      camera_coords: cameraCoords,
      center_coords: centerCoords,
    }),
  });
  if (!r.ok) throw new Error(`POST /api/state/camera failed: ${r.status}`);
}

export interface StateStream {
  close: () => void;
}

export function streamState(
  onMessage: (state: WorldState) => void,
  onStatus?: (status: "open" | "closed" | "error") => void,
): StateStream {
  let closed = false;
  let ws: WebSocket | null = null;
  let reconnectTimer: number | null = null;

  const connect = () => {
    if (closed) return;
    ws = new WebSocket(`${WS_BASE}/ws/state`);
    ws.onopen = () => onStatus?.("open");
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data) as WSMessage;
        onMessage(msg.payload);
      } catch (e) {
        console.error("malformed ws message", e);
      }
    };
    ws.onerror = () => onStatus?.("error");
    ws.onclose = () => {
      onStatus?.("closed");
      if (!closed) {
        reconnectTimer = window.setTimeout(connect, 1500);
      }
    };
  };
  connect();

  return {
    close: () => {
      closed = true;
      if (reconnectTimer != null) window.clearTimeout(reconnectTimer);
      ws?.close();
    },
  };
}
