export type LatLon = [number, number];

export interface AnimalCoord {
  x: number;
  y: number;
  name: string;
  temperature: number;
  distance_metre: number;
}

export interface WorldState {
  center_x: number;
  center_y: number;
  animal_coords: Record<string, AnimalCoord>;
  camera_coords: number[][];
}

export interface WSMessage {
  type: "snapshot" | "update";
  payload: WorldState;
}
