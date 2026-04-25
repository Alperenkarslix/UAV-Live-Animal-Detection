import { useCallback, useEffect, useMemo, useState } from "react";
import { MapView } from "./components/MapView";
import { Sidebar } from "./components/Sidebar";
import { buildState, fetchState, streamState } from "./api";
import type { LatLon, WorldState } from "./types";

const DEFAULT_CENTER: LatLon = [39.647, 27.883]; // Balikesir region
const DEFAULT_CORNERS: LatLon[] = [
  [39.6454, 27.8807],
  [39.6454, 27.8857],
  [39.6494, 27.8857],
  [39.6494, 27.8807],
];

type Mode = "add-animal" | "edit-camera" | "view";

export default function App() {
  const [mode, setMode] = useState<Mode>("add-animal");
  const [animals, setAnimals] = useState<LatLon[]>([]);
  const [cameraCorners, setCameraCorners] = useState<LatLon[]>(DEFAULT_CORNERS);
  const [liveState, setLiveState] = useState<WorldState | null>(null);
  const [wsStatus, setWsStatus] = useState<"open" | "closed" | "error">("closed");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const initialCenter = useMemo<LatLon>(() => {
    if (liveState) return [liveState.center_x, liveState.center_y];
    return DEFAULT_CENTER;
  }, [liveState]);

  // --- Hydrate from server on mount ---
  useEffect(() => {
    fetchState()
      .then((s) => {
        if (!s) return;
        setLiveState(s);
        setCameraCorners(s.camera_coords.slice(0, 4).map((c) => [c[0]!, c[1]!] as LatLon));
        setAnimals(
          Object.values(s.animal_coords).map((a) => [a.x, a.y] as LatLon),
        );
      })
      .catch(() => {
        // 404 / network — fine on cold start
      });

    const stream = streamState(setLiveState, setWsStatus);
    return () => stream.close();
  }, []);

  // --- Editing handlers ---
  const onAddAnimal = useCallback((coord: LatLon) => {
    setAnimals((prev) => [...prev, coord]);
  }, []);
  const onMoveAnimal = useCallback((idx: number, coord: LatLon) => {
    setAnimals((prev) => prev.map((a, i) => (i === idx ? coord : a)));
  }, []);
  const onRemoveAnimal = useCallback((idx: number) => {
    setAnimals((prev) => prev.filter((_, i) => i !== idx));
  }, []);
  const onMoveCorner = useCallback((idx: number, coord: LatLon) => {
    setCameraCorners((prev) => prev.map((c, i) => (i === idx ? coord : c)));
  }, []);

  const onClear = useCallback(() => {
    setAnimals([]);
    setCameraCorners(DEFAULT_CORNERS);
    setError(null);
  }, []);

  const onSave = useCallback(async () => {
    setSaving(true);
    setError(null);
    try {
      const result = await buildState(animals, cameraCorners);
      setLiveState(result);
      setMode("view");
    } catch (e) {
      setError(e instanceof Error ? e.message : "save failed");
    } finally {
      setSaving(false);
    }
  }, [animals, cameraCorners]);

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <Sidebar
        mode={mode}
        setMode={setMode}
        animals={animals}
        cameraCorners={cameraCorners}
        liveState={liveState}
        wsStatus={wsStatus}
        onSave={onSave}
        onClear={onClear}
        saving={saving}
        error={error}
      />
      <main className="relative h-full flex-1">
        <MapView
          initialCenter={initialCenter}
          animals={animals}
          cameraCorners={cameraCorners}
          mode={mode}
          onAddAnimal={onAddAnimal}
          onMoveAnimal={onMoveAnimal}
          onRemoveAnimal={onRemoveAnimal}
          onMoveCorner={onMoveCorner}
        />
      </main>
    </div>
  );
}
