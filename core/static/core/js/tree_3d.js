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

        this.mouse = new THREE.Vector2(0, 0);
        this.leaves = [];
        this.branches = [];
        this.crows = [];
        
        this.init();
        this.addCrows();
        this.animate();
        this.setupInteractions();
    }

    init() {
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
        this.scene.add(ambientLight);

        const sunLight = new THREE.DirectionalLight(0xffe9b5, 1.2);
        sunLight.position.set(5, 10, 7);
        this.scene.add(sunLight);

        this.trunkMaterial = new THREE.MeshStandardMaterial({ color: 0x3E2723, roughness: 0.8 });
        this.leafMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x4E6E5D, 
            emissive: 0xDAA520, 
            emissiveIntensity: 0.1,
            roughness: 0.5 
        });

        this.treeGroup = new THREE.Group();
        this.scene.add(this.treeGroup);

        this.createBranch(this.treeGroup, new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 1, 0), 2.2, 0.25, 5);

        this.camera.position.set(0, 4, 11);
        this.camera.lookAt(0, 4, 0);
    }

    createBranch(parent, start, direction, length, radius, depth) {
        const end = start.clone().add(direction.clone().multiplyScalar(length));
        const geometry = new THREE.CylinderGeometry(radius * 0.7, radius, length, 8);
        const mesh = new THREE.Mesh(geometry, this.trunkMaterial);
        
        const group = new THREE.Group();
        group.position.copy(start);
        
        const axis = new THREE.Vector3(0, 1, 0);
        group.quaternion.setFromUnitVectors(axis, direction.clone().normalize());
        
        mesh.position.set(0, length / 2, 0);
        group.add(mesh);
        parent.add(group);

        group.userData = { depth, phase: Math.random() * Math.PI * 2 };
        this.branches.push(group);

        if (depth <= 1) {
            this.addLeaves(group, length);
            return;
        }

        const branchesCount = depth > 3 ? 2 : 3;
        for (let i = 0; i < branchesCount; i++) {
            const newDir = direction.clone()
                .applyAxisAngle(new THREE.Vector3(1, 0, 0), (Math.random() - 0.5) * 1.2)
                .applyAxisAngle(new THREE.Vector3(0, 0, 1), (Math.random() - 0.5) * 1.2)
                .normalize();
            this.createBranch(group, new THREE.Vector3(0, length, 0), newDir, length * 0.7, radius * 0.7, depth - 1);
        }
    }

    addLeaves(parent, branchLength) {
        const leafGeom = new THREE.IcosahedronGeometry(0.35, 0);
        for (let i = 0; i < 8; i++) {
            const leaf = new THREE.Mesh(leafGeom, this.leafMaterial);
            leaf.position.set(
                (Math.random() - 0.5) * 1.2,
                branchLength + (Math.random() - 0.5) * 0.8,
                (Math.random() - 0.5) * 1.2
            );
            leaf.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, Math.random() * Math.PI);
            leaf.userData = { phase: Math.random() * Math.PI * 2, amp: 0.05 + Math.random() * 0.1 };
            parent.add(leaf);
            this.leaves.push(leaf);
        }
    }

    addCrows() {
        for (let i = 0; i < 5; i++) {
            const crow = new THREE.Group();
            const body = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.1, 0.5), new THREE.MeshStandardMaterial({ color: 0x000000 }));
            const wingL = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.02, 0.3), new THREE.MeshStandardMaterial({ color: 0x111111 }));
            const wingR = wingL.clone();
            wingL.position.x = -0.25; wingR.position.x = 0.25;
            crow.add(body, wingL, wingR);
            crow.position.set((Math.random() - 0.5) * 15, 5 + Math.random() * 3, (Math.random() - 0.5) * 10);
            this.scene.add(crow);
            this.crows.push({ mesh: crow, wings: [wingL, wingR], speed: 0.02 + Math.random() * 0.02, phase: Math.random() * 10 });
        }
    }

    setupInteractions() {
        this.container.addEventListener('mousemove', (e) => {
            const rect = this.container.getBoundingClientRect();
            this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
            this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
        });
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        const time = performance.now() * 0.001;

        const windX = Math.sin(time * 0.5) * 0.03 + this.mouse.x * 0.04;
        const windZ = Math.cos(time * 0.4) * 0.03 + this.mouse.y * 0.04;

        this.branches.forEach(b => {
            const d = b.userData.depth;
            const sway = Math.sin(time * 1.2 + b.userData.phase) * (0.005 * (6 - d));
            b.rotation.x = sway + windZ * (0.3 * (6 - d));
            b.rotation.z = sway + windX * (0.3 * (6 - d));
        });

        this.leaves.forEach(l => {
            l.rotation.y += 0.01;
            l.position.y += Math.sin(time * 2 + l.userData.phase) * 0.002;
        });

        this.crows.forEach(c => {
            c.mesh.position.x += c.speed;
            if (c.mesh.position.x > 12) c.mesh.position.x = -12;
            const flap = Math.sin(time * 10 + c.phase) * 0.5;
            c.wings[0].rotation.z = flap; c.wings[1].rotation.z = -flap;
        });

        this.camera.position.x += (this.mouse.x * 1.5 - this.camera.position.x) * 0.03;
        this.camera.lookAt(0, 4, 0);
        this.renderer.render(this.scene, this.camera);
    }
}

window.addEventListener('load', () => {
    if (document.getElementById('tree-3d-container')) new AgroTree('tree-3d-container');
});
