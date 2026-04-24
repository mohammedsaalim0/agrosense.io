class AgroTree {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;
        
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(40, this.container.clientWidth / this.container.clientHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.container.appendChild(this.renderer.domElement);

        this.branches = [];
        this.leaves = [];
        this.fireflies = [];
        
        this.init();
        this.animate();
        
        window.addEventListener('resize', () => {
            const width = this.container.clientWidth;
            const height = this.container.clientHeight;
            this.camera.aspect = width / height;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(width, height);
        });
    }

    init() {
        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
        this.scene.add(ambientLight);

        const sunLight = new THREE.DirectionalLight(0xffe9b5, 1.5);
        sunLight.position.set(5, 10, 7);
        this.scene.add(sunLight);

        // Materials
        this.trunkMat = new THREE.MeshStandardMaterial({ color: 0x3E2723, roughness: 0.9 });
        this.leafMat = new THREE.MeshStandardMaterial({ 
            color: 0x2e7d32, 
            emissive: 0x1b5e20, 
            emissiveIntensity: 0.2,
            roughness: 0.6 
        });

        this.treeGroup = new THREE.Group();
        this.scene.add(this.treeGroup);

        // Create Majestic Tree
        this.createBranch(this.treeGroup, new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 1, 0), 2.5, 0.4, 5);

        // Add Glowing Insects (Fireflies)
        const ffGeom = new THREE.SphereGeometry(0.06, 8, 8);
        const ffMat = new THREE.MeshBasicMaterial({ color: 0xffe082 });
        for (let i = 0; i < 30; i++) {
            const ff = new THREE.Mesh(ffGeom, ffMat);
            const angle = Math.random() * Math.PI * 2;
            const radius = 2 + Math.random() * 4;
            ff.position.set(Math.cos(angle) * radius, Math.random() * 8, Math.sin(angle) * radius);
            this.scene.add(ff);
            this.fireflies.push({
                mesh: ff,
                angle: angle,
                radius: radius,
                y: ff.position.y,
                speed: 0.01 + Math.random() * 0.02,
                phase: Math.random() * 10
            });
        }

        this.camera.position.set(0, 5, 12);
        this.camera.lookAt(0, 4, 0);
    }

    createBranch(parent, start, direction, length, radius, depth) {
        const group = new THREE.Group();
        group.position.copy(start);
        
        const axis = new THREE.Vector3(0, 1, 0);
        group.quaternion.setFromUnitVectors(axis, direction.clone().normalize());
        
        const geometry = new THREE.CylinderGeometry(radius * 0.65, radius, length, 12);
        const mesh = new THREE.Mesh(geometry, this.trunkMat);
        mesh.position.y = length / 2;
        group.add(mesh);
        
        parent.add(group);
        group.userData = { depth, phase: Math.random() * Math.PI * 2 };
        this.branches.push(group);

        if (depth <= 1) {
            this.addLeaves(group, length);
            return;
        }

        const count = depth > 3 ? 2 : 3;
        for (let i = 0; i < count; i++) {
            const newDir = direction.clone()
                .applyAxisAngle(new THREE.Vector3(1, 0, 0), (Math.random() - 0.5) * 1.5)
                .applyAxisAngle(new THREE.Vector3(0, 0, 1), (Math.random() - 0.5) * 1.5)
                .normalize();
            this.createBranch(group, new THREE.Vector3(0, length, 0), newDir, length * 0.75, radius * 0.6, depth - 1);
        }
    }

    addLeaves(parent, branchLength) {
        const leafGeom = new THREE.IcosahedronGeometry(0.4, 0);
        for (let i = 0; i < 10; i++) {
            const leaf = new THREE.Mesh(leafGeom, this.leafMat);
            leaf.position.set(
                (Math.random() - 0.5) * 1.5,
                branchLength + (Math.random() - 0.5) * 1.0,
                (Math.random() - 0.5) * 1.5
            );
            leaf.rotation.set(Math.random() * 6, Math.random() * 6, Math.random() * 6);
            leaf.userData = { phase: Math.random() * Math.PI * 2 };
            parent.add(leaf);
            this.leaves.push(leaf);
        }
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        const time = performance.now() * 0.001;

        // Auto 360 Rotation
        this.treeGroup.rotation.y += 0.005;

        // Physics Sway
        this.branches.forEach(b => {
            const d = b.userData.depth;
            const sway = Math.sin(time + b.userData.phase) * (0.005 * (6 - d));
            b.rotation.x = sway;
            b.rotation.z = sway;
        });

        // Leaf Flutter
        this.leaves.forEach(l => {
            l.rotation.y += 0.01;
            l.scale.setScalar(1 + Math.sin(time * 2 + l.userData.phase) * 0.05);
        });

        // Glowing Insects (Fireflies)
        this.fireflies.forEach(f => {
            f.angle += f.speed;
            f.mesh.position.x = Math.cos(f.angle) * f.radius;
            f.mesh.position.z = Math.sin(f.angle) * f.radius;
            f.mesh.position.y = f.y + Math.sin(time + f.phase) * 1.0;
            // Flashing
            f.mesh.scale.setScalar(0.5 + Math.sin(time * 4 + f.phase) * 0.5);
        });

        this.renderer.render(this.scene, this.camera);
    }
}

window.addEventListener('load', () => {
    if (document.getElementById('tree-3d-container')) {
        new AgroTree('tree-3d-container');
    }
});
