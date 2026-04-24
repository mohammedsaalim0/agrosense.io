class AgroTree {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;
        
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(45, this.container.clientWidth / this.container.clientHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, logarithmicDepthBuffer: true });
        
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.container.appendChild(this.renderer.domElement);

        this.mouse = new THREE.Vector2(0, 0);
        this.windForce = 0.05;
        this.leaves = [];
        this.branches = [];
        
        this.init();
        this.addEnvironment();
        this.animate();
        this.setupInteractions();
    }

    init() {
        // Advanced Lighting
        const ambientLight = new THREE.AmbientLight(0x404040, 0.8);
        this.scene.add(ambientLight);

        const sunLight = new THREE.DirectionalLight(0xfff5e6, 1.5);
        sunLight.position.set(10, 15, 10);
        sunLight.castShadow = true;
        sunLight.shadow.mapSize.width = 1024;
        sunLight.shadow.mapSize.height = 1024;
        this.scene.add(sunLight);

        const fillLight = new THREE.PointLight(0x4E6E5D, 1.5, 20);
        fillLight.position.set(-8, 5, -5);
        this.scene.add(fillLight);

        // Materials with high detail
        this.trunkMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x3E2723, 
            roughness: 0.9,
            metalness: 0.1,
            flatShading: false
        });

        this.leafMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x2e7d32, 
            roughness: 0.8,
            metalness: 0.0,
            side: THREE.DoubleSide
        });

        this.treeGroup = new THREE.Group();
        this.scene.add(this.treeGroup);

        // Procedural realistic tree generation
        this.generateTree(this.treeGroup, new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 1, 0), 2.5, 0.3, 5);

        this.camera.position.set(0, 5, 12);
        this.camera.lookAt(0, 4, 0);
    }

    generateTree(parentGroup, start, direction, length, radius, depth) {
        const end = start.clone().add(direction.clone().multiplyScalar(length));
        
        // Create smooth branch geometry
        const curve = new THREE.LineCurve3(new THREE.Vector3(0,0,0), new THREE.Vector3(0, length, 0));
        const geometry = new THREE.TubeGeometry(curve, 8, radius, 8, false);
        const branch = new THREE.Mesh(geometry, this.trunkMaterial);
        branch.castShadow = true;
        branch.receiveShadow = true;
        
        // Position at the start of the branch relative to parent
        branch.position.copy(start);
        
        // Orient the branch
        const quaternion = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.clone().normalize());
        branch.quaternion.copy(quaternion);

        // Group to hold this branch and its children
        const branchGroup = new THREE.Group();
        branchGroup.position.copy(start);
        branchGroup.quaternion.copy(quaternion);
        branchGroup.add(branch);
        branch.position.set(0,0,0); // Reset local pos since group is at start

        parentGroup.add(branchGroup);
        
        // Store for physics
        branchGroup.userData = {
            depth: depth,
            phase: Math.random() * Math.PI * 2,
            originalQuat: branchGroup.quaternion.clone()
        };
        this.branches.push(branchGroup);

        if (depth === 1) {
            this.createLeafCloud(branchGroup, new THREE.Vector3(0, length, 0));
            return;
        }

        const numChildren = depth > 3 ? 2 : 3;
        for (let i = 0; i < numChildren; i++) {
            const newDir = new THREE.Vector3(
                (Math.random() - 0.5) * 1.0,
                1.0,
                (Math.random() - 0.5) * 1.0
            ).normalize();
            
            this.generateTree(branchGroup, new THREE.Vector3(0, length, 0), newDir, length * 0.75, radius * 0.65, depth - 1);
        }
    }

    createLeafCloud(parent, position) {
        const leafGeom = new THREE.PlaneGeometry(0.3, 0.5);
        for (let i = 0; i < 12; i++) {
            const leaf = new THREE.Mesh(leafGeom, this.leafMaterial);
            leaf.position.copy(position).add(new THREE.Vector3(
                (Math.random() - 0.5) * 0.8,
                (Math.random() - 0.5) * 0.8,
                (Math.random() - 0.5) * 0.8
            ));
            leaf.rotation.set(Math.random() * 6, Math.random() * 6, Math.random() * 6);
            leaf.userData = {
                phase: Math.random() * Math.PI * 2,
                amp: 0.1 + Math.random() * 0.2,
                baseRot: leaf.rotation.clone()
            };
            parent.add(leaf);
            this.leaves.push(leaf);
        }
    }

    addEnvironment() {
        // Grassy mound
        const moundGeom = new THREE.CircleGeometry(4, 32);
        const moundMat = new THREE.MeshStandardMaterial({ color: 0x1b5e20, roughness: 1 });
        const mound = new THREE.Mesh(moundGeom, moundMat);
        mound.rotation.x = -Math.PI / 2;
        mound.receiveShadow = true;
        this.treeGroup.add(mound);

        // Fireflies
        this.fireflies = [];
        const ffGeom = new THREE.SphereGeometry(0.04, 8, 8);
        const ffMat = new THREE.MeshBasicMaterial({ color: 0xffe082 });
        for (let i = 0; i < 25; i++) {
            const ff = new THREE.Mesh(ffGeom, ffMat);
            ff.position.set((Math.random() - 0.5) * 10, Math.random() * 8, (Math.random() - 0.5) * 10);
            this.scene.add(ff);
            this.fireflies.push({
                mesh: ff,
                phase: Math.random() * Math.PI * 2,
                speed: 0.5 + Math.random() * 0.5,
                base: ff.position.clone()
            });
        }
    }

    setupInteractions() {
        const handleMove = (x, y) => {
            const rect = this.container.getBoundingClientRect();
            this.mouse.x = ((x - rect.left) / rect.width) * 2 - 1;
            this.mouse.y = -((y - rect.top) / rect.height) * 2 + 1;
        };
        this.container.addEventListener('mousemove', (e) => handleMove(e.clientX, e.clientY));
        window.addEventListener('resize', () => {
            const width = this.container.clientWidth;
            const height = this.container.clientHeight;
            this.camera.aspect = width / height;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(width, height);
        });
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        const time = performance.now() * 0.001;

        // Realistic Wind Physics
        const windX = Math.sin(time * 0.5) * 0.02 + this.mouse.x * 0.05;
        const windZ = Math.cos(time * 0.4) * 0.02 + this.mouse.y * 0.05;

        this.branches.forEach(branchGroup => {
            const d = branchGroup.userData.depth;
            const swayX = Math.sin(time * 1.5 + branchGroup.userData.phase) * (0.008 * (6 - d));
            const swayZ = Math.cos(time * 1.3 + branchGroup.userData.phase) * (0.008 * (6 - d));
            
            // Soft relative rotation
            branchGroup.rotation.x = swayZ + windZ * (0.4 * (6 - d));
            branchGroup.rotation.z = swayX + windX * (0.4 * (6 - d));
        });

        this.leaves.forEach(leaf => {
            const flutter = Math.sin(time * 5 + leaf.userData.phase) * 0.12;
            leaf.rotation.x = leaf.userData.baseRot.x + flutter;
            leaf.rotation.y = leaf.userData.baseRot.y + flutter;
        });

        this.fireflies.forEach(f => {
            f.mesh.position.x = f.base.x + Math.sin(time * f.speed + f.phase) * 1.5;
            f.mesh.position.y = f.base.y + Math.cos(time * f.speed * 1.2 + f.phase) * 1.2;
            f.mesh.position.z = f.base.z + Math.sin(time * f.speed * 0.8 + f.phase) * 1.5;
            f.mesh.scale.setScalar(0.5 + Math.sin(time * 4 + f.phase) * 0.5);
        });

        // Soft camera orbit
        this.camera.position.x += (this.mouse.x * 2 - this.camera.position.x) * 0.02;
        this.camera.position.y += (5 + this.mouse.y * 1 - this.camera.position.y) * 0.02;
        this.camera.lookAt(0, 4, 0);

        this.renderer.render(this.scene, this.camera);
    }
}

window.addEventListener('load', () => {
    if (document.getElementById('tree-3d-container')) {
        new AgroTree('tree-3d-container');
    }
});
