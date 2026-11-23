declare module 'three' {
  export type Scene = any
  export type PerspectiveCamera = any
  export type WebGLRenderer = any
  export type Object3D = any
  export type Group = any
  export type Raycaster = any
  export type Vector2 = any
  export type Sprite = any

  export const Scene: any
  export const Color: any
  export const PerspectiveCamera: any
  export const WebGLRenderer: any
  export const AmbientLight: any
  export const DirectionalLight: any
  export const PointLight: any
  export const Box3: any
  export const Vector3: any
  export const TorusKnotGeometry: any
  export const MeshStandardMaterial: any
  export const Mesh: any
  export const Group: any
  export const Raycaster: any
  export const Vector2: any
  export const CanvasTexture: any
  export const Sprite: any
  export const SpriteMaterial: any
  export const SRGBColorSpace: any
  export const LinearFilter: any
  export const MathUtils: any
}

declare module 'three/examples/jsm/controls/OrbitControls' {
  export type OrbitControls = any
  export const OrbitControls: any
}

declare module 'three/examples/jsm/loaders/GLTFLoader' {
  export class GLTFLoader {
    load(
      url: string,
      onLoad: (gltf: any) => void,
      onProgress?: ((event: ProgressEvent) => void) | undefined,
      onError?: ((error: unknown) => void) | undefined,
    ): void
  }
}
