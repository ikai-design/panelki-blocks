import fs from 'node:fs/promises';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const loader = new GLTFLoader();
const files = process.argv.slice(2);
if (!files.length) throw new Error('Usage: node scripts/inspect-glb.mjs file.glb ...');

for (const file of files) {
  const data = await fs.readFile(file);
  const gltf = await loader.parseAsync(data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength), file);
  const box = new THREE.Box3().setFromObject(gltf.scene);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const nodes = [];
  const geometry = [];
  const materials = new Map();
  let meshes = 0;
  gltf.scene.traverse((o) => {
    if (o.isMesh) {
      meshes++;
      const uv = o.geometry.attributes.uv;
      geometry.push({ name: o.name || '(unnamed)', vertices: o.geometry.attributes.position?.count ?? 0, triangles: o.geometry.index ? o.geometry.index.count / 3 : (o.geometry.attributes.position?.count ?? 0) / 3, uv: uv ? { count: uv.count, min: [Math.min(...uv.array.filter((_, i) => i % 2 === 0)), Math.min(...uv.array.filter((_, i) => i % 2 === 1))], max: [Math.max(...uv.array.filter((_, i) => i % 2 === 0)), Math.max(...uv.array.filter((_, i) => i % 2 === 1))] } : null });
      const slots = Array.isArray(o.material) ? o.material : [o.material];
      for (const m of slots) if (m && !materials.has(m.uuid)) materials.set(m.uuid, { name: m.name, type: m.type, color: m.color?.getHexString(), roughness: m.roughness, metalness: m.metalness, emissive: m.emissive?.getHexString(), emissiveIntensity: m.emissiveIntensity, maps: { baseColor: !!m.map, roughness: !!m.roughnessMap, metalness: !!m.metalnessMap, normal: !!m.normalMap, ao: !!m.aoMap, emissive: !!m.emissiveMap } });
    }
    nodes.push({ name: o.name || '(unnamed)', type: o.type, position: o.position.toArray(), quaternion: o.quaternion.toArray(), scale: o.scale.toArray(), mesh: !!o.isMesh });
  });
  console.log(JSON.stringify({ file, bytes: data.byteLength, scene: gltf.scene.name, nodes, meshes, geometry, materials: [...materials.values()], min: box.min.toArray(), max: box.max.toArray(), size: size.toArray(), center: center.toArray(), root: { position: gltf.scene.position.toArray(), quaternion: gltf.scene.quaternion.toArray(), scale: gltf.scene.scale.toArray() } }, null, 2));
}
