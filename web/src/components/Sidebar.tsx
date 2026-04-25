import type { LatLon, WorldState } from "../types";

type Mode = "add-animal" | "edit-camera" | "view";

interface Props {
  mode: Mode;
  setMode: (m: Mode) => void;
  animals: LatLon[];
  cameraCorners: LatLon[];
  liveState: WorldState | null;
  wsStatus: "open" | "closed" | "error";
  onSave: () => void;
  onClear: () => void;
  saving: boolean;
  error: string | null;
}

export function Sidebar({
  mode,
  setMode,
  animals,
  cameraCorners,
  liveState,
  wsStatus,
  onSave,
  onClear,
  saving,
  error,
}: Props) {
  const canSave = animals.length > 0 && cameraCorners.length === 4 && !saving;

  return (
    <aside className="flex h-full w-[360px] shrink-0 flex-col border-r border-zinc-800 bg-zinc-950/90 p-4 backdrop-blur">
      <header className="mb-4">
        <h1 className="text-lg font-semibold tracking-tight">UAV Animal Detection</h1>
        <p className="text-xs text-zinc-400">
          v0.2 — FastAPI · MapLibre · SQLite
        </p>
      </header>

      <section className="mb-5">
        <h2 className="mb-2 text-xs font-medium uppercase tracking-wider text-zinc-500">
          Mode
        </h2>
        <div className="grid grid-cols-3 gap-1 rounded-lg bg-zinc-900 p-1">
          <ModeButton active={mode === "view"} onClick={() => setMode("view")}>
            View
          </ModeButton>
          <ModeButton
            active={mode === "add-animal"}
            onClick={() => setMode("add-animal")}
          >
            + Animal
          </ModeButton>
          <ModeButton
            active={mode === "edit-camera"}
            onClick={() => setMode("edit-camera")}
          >
            Camera
          </ModeButton>
        </div>
        <p className="mt-2 text-xs text-zinc-500">
          {mode === "add-animal" && "Click map to drop a marker. Right-click marker to remove."}
          {mode === "edit-camera" && "Drag the 4 blue corners to define the camera FOV."}
          {mode === "view" && "Read-only — pan and zoom the map."}
        </p>
      </section>

      <section className="mb-5">
        <h2 className="mb-2 text-xs font-medium uppercase tracking-wider text-zinc-500">
          Edit buffer
        </h2>
        <dl className="grid grid-cols-2 gap-2 text-sm">
          <Stat label="Animals" value={animals.length} />
          <Stat label="Corners" value={`${cameraCorners.length}/4`} />
        </dl>
        <div className="mt-3 flex gap-2">
          <button
            disabled={!canSave}
            onClick={onSave}
            className="flex-1 rounded-md bg-sky-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-sky-500 disabled:cursor-not-allowed disabled:bg-zinc-800 disabled:text-zinc-500"
          >
            {saving ? "Saving…" : "Save state"}
          </button>
          <button
            onClick={onClear}
            disabled={saving}
            className="rounded-md border border-zinc-800 px-3 py-2 text-sm text-zinc-300 transition hover:bg-zinc-900 disabled:opacity-50"
          >
            Clear
          </button>
        </div>
        {error && (
          <p className="mt-2 text-xs text-rose-400">{error}</p>
        )}
      </section>

      <section className="mb-5">
        <h2 className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-zinc-500">
          Live state
          <StatusDot status={wsStatus} />
        </h2>
        {liveState ? (
          <div className="space-y-1 rounded-md bg-zinc-900/60 p-3 text-xs leading-relaxed">
            <div className="flex justify-between">
              <span className="text-zinc-400">center</span>
              <code>
                {liveState.center_x.toFixed(5)}, {liveState.center_y.toFixed(5)}
              </code>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-400">animals</span>
              <code>{Object.keys(liveState.animal_coords).length}</code>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-400">corners</span>
              <code>{liveState.camera_coords.length}</code>
            </div>
          </div>
        ) : (
          <p className="text-xs text-zinc-500">Awaiting first state…</p>
        )}
      </section>

      {liveState && (
        <section className="min-h-0 flex-1 overflow-auto">
          <h2 className="mb-2 text-xs font-medium uppercase tracking-wider text-zinc-500">
            Animals
          </h2>
          <ul className="space-y-1">
            {Object.entries(liveState.animal_coords).map(([id, a]) => (
              <li
                key={id}
                className="rounded-md border border-zinc-800/60 bg-zinc-900/40 px-3 py-2 text-xs"
              >
                <div className="flex justify-between font-medium text-zinc-200">
                  <span>{a.name}</span>
                  <span className="text-zinc-500">{id}</span>
                </div>
                <div className="mt-1 grid grid-cols-2 gap-x-2 text-zinc-500">
                  <span>{a.x.toFixed(5)}, {a.y.toFixed(5)}</span>
                  <span className="text-right text-zinc-300">
                    {a.distance_metre.toFixed(0)} m
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}
    </aside>
  );
}

function ModeButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-md px-2 py-1.5 text-xs font-medium transition ${
        active
          ? "bg-zinc-700 text-white shadow"
          : "text-zinc-400 hover:bg-zinc-800/60 hover:text-zinc-200"
      }`}
    >
      {children}
    </button>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-md bg-zinc-900/60 px-3 py-2">
      <dt className="text-xs text-zinc-500">{label}</dt>
      <dd className="mt-0.5 text-base font-semibold tabular-nums">{value}</dd>
    </div>
  );
}

function StatusDot({ status }: { status: "open" | "closed" | "error" }) {
  const color =
    status === "open"
      ? "bg-emerald-500"
      : status === "error"
      ? "bg-rose-500"
      : "bg-zinc-500";
  return (
    <span
      className={`inline-block h-1.5 w-1.5 rounded-full ${color}`}
      title={`websocket: ${status}`}
    />
  );
}
