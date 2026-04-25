import { useEffect, useRef } from "react";
import maplibregl, { type LngLatLike } from "maplibre-gl";
import type { LatLon } from "../types";

interface Props {
  initialCenter: LatLon;
  initialZoom?: number;
  animals: LatLon[];
  cameraCorners: LatLon[];
  onAddAnimal: (latlon: LatLon) => void;
  onMoveCorner: (index: number, latlon: LatLon) => void;
  onMoveAnimal: (index: number, latlon: LatLon) => void;
  onRemoveAnimal: (index: number) => void;
  mode: "add-animal" | "edit-camera" | "view";
}

const OSM_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "© OpenStreetMap contributors",
    },
  },
  layers: [{ id: "osm", type: "raster", source: "osm" }],
  glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
};

const POLYGON_SOURCE = "uav-camera-poly";
const POLYGON_FILL = "uav-camera-fill";
const POLYGON_OUTLINE = "uav-camera-outline";

export function MapView({
  initialCenter,
  initialZoom = 16,
  animals,
  cameraCorners,
  onAddAnimal,
  onMoveCorner,
  onMoveAnimal,
  onRemoveAnimal,
  mode,
}: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const animalMarkersRef = useRef<maplibregl.Marker[]>([]);
  const cornerMarkersRef = useRef<maplibregl.Marker[]>([]);

  // Ref to latest props so map handlers always read current values
  const cbRef = useRef({ onAddAnimal, onMoveCorner, onMoveAnimal, onRemoveAnimal, mode });
  cbRef.current = { onAddAnimal, onMoveCorner, onMoveAnimal, onRemoveAnimal, mode };

  // --- Map init (once) ---
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: OSM_STYLE,
      center: [initialCenter[1], initialCenter[0]] as LngLatLike,
      zoom: initialZoom,
      attributionControl: { compact: true },
    });
    map.addControl(new maplibregl.NavigationControl({}), "top-right");
    map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-left");

    map.on("load", () => {
      map.addSource(POLYGON_SOURCE, {
        type: "geojson",
        data: {
          type: "Feature",
          geometry: { type: "Polygon", coordinates: [[]] },
          properties: {},
        },
      });
      map.addLayer({
        id: POLYGON_FILL,
        type: "fill",
        source: POLYGON_SOURCE,
        paint: { "fill-color": "#0ea5e9", "fill-opacity": 0.18 },
      });
      map.addLayer({
        id: POLYGON_OUTLINE,
        type: "line",
        source: POLYGON_SOURCE,
        paint: { "line-color": "#38bdf8", "line-width": 2 },
      });
    });

    map.on("click", (e) => {
      if (cbRef.current.mode !== "add-animal") return;
      cbRef.current.onAddAnimal([e.lngLat.lat, e.lngLat.lng]);
    });

    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // --- Sync animal markers ---
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    for (const m of animalMarkersRef.current) m.remove();
    animalMarkersRef.current = animals.map((coord, idx) => {
      const el = document.createElement("div");
      el.className = "uav-marker";
      el.title = `Hayvan${idx + 1} (right-click to remove)`;
      const marker = new maplibregl.Marker({ element: el, draggable: true })
        .setLngLat([coord[1], coord[0]])
        .addTo(map);
      marker.on("dragend", () => {
        const ll = marker.getLngLat();
        cbRef.current.onMoveAnimal(idx, [ll.lat, ll.lng]);
      });
      el.addEventListener("contextmenu", (ev) => {
        ev.preventDefault();
        cbRef.current.onRemoveAnimal(idx);
      });
      return marker;
    });
  }, [animals]);

  // --- Sync corner markers + polygon ---
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    for (const m of cornerMarkersRef.current) m.remove();
    cornerMarkersRef.current = cameraCorners.map((coord, idx) => {
      const el = document.createElement("div");
      el.className = "uav-marker";
      el.dataset.mode = "camera-corner";
      el.title = `Camera corner ${idx + 1}`;
      const marker = new maplibregl.Marker({ element: el, draggable: true })
        .setLngLat([coord[1], coord[0]])
        .addTo(map);
      marker.on("dragend", () => {
        const ll = marker.getLngLat();
        cbRef.current.onMoveCorner(idx, [ll.lat, ll.lng]);
      });
      return marker;
    });

    const updatePolygon = () => {
      const src = map.getSource(POLYGON_SOURCE) as maplibregl.GeoJSONSource | undefined;
      if (!src) return;
      const ring =
        cameraCorners.length >= 3
          ? [...cameraCorners.map((c) => [c[1], c[0]]), [cameraCorners[0]![1], cameraCorners[0]![0]]]
          : [];
      src.setData({
        type: "Feature",
        geometry: { type: "Polygon", coordinates: [ring] },
        properties: {},
      });
    };

    if (map.isStyleLoaded()) updatePolygon();
    else map.once("load", updatePolygon);
  }, [cameraCorners]);

  return (
    <div
      ref={containerRef}
      data-mode={mode}
      className="h-full w-full"
      style={{ cursor: mode === "add-animal" ? "crosshair" : "grab" }}
    />
  );
}
