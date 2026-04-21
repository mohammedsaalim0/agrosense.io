class AgroTree {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(52, this.container.clientWidth / this.container.clientHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.container.appendChild(this.renderer.domElement);

        this.mouse = new THREE.Vector2();
        this.targetRotation = new THREE.Vector2();
        
        this.leaves = [];
        this.init();
        this.addCrows();
        this.addFireflies();
        this.animate();
        this.setupInteractions();
    }

    init() {
        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.75);
        this.scene.add(ambientLight);

        const sunLight = new THREE.DirectionalLight(0xffe9b5, 1.2);
        sunLight.position.set(8, 12, 6);
        sunLight.castShadow = true;
        this.scene.add(sunLight);
        this.rimLight = new THREE.PointLight(0xc6f7d4, 1.1, 18);
        this.rimLight.position.set(-5, 7, 5);
        this.scene.add(this.rimLight);

        // Original AgroSense Colors
        this.trunkMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x3E2723, // Original Deep Brown
            roughness: 0.9
        });
        this.leafMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x4E6E5D, // Original Moss Green
            emissive: 0xDAA520, 
            emissiveIntensity: 0.15
        });

        this.treeGroup = new THREE.Group();
        this.createBranch(0, 0, 0, 1.2, 0, 6);
        this.scene.add(this.treeGroup);

        this.camera.position.set(0, 4.8, 11);
        this.camera.lookAt(0, 4.2, 0);
    }

    createBranch(x, y, z, height, angle, depth) {
        if (depth === 0) {
            const leafCount = 3;
            for(let i=0; i<leafCount; i++) {
                const leafGeom = new THREE.IcosahedronGeometry(0.4, 0);
                const leaf = new THREE.Mesh(leafGeom, this.leafMaterial);
                leaf.position.set(
                    x + (Math.random() - 0.5) * 0.5,
                    y + (Math.random() - 0.5) * 0.5,
                    z + (Math.random() - 0.5) * 0.5
                );
                leaf.userData = {
                    swayOffset: Math.random() * Math.PI * 2,
                    swayAmp: 0.05 + Math.random() * 0.08,
                    baseY: leaf.position.y,
                };
                this.leaves.push(leaf);
                this.treeGroup.add(leaf);
            }
            return;
        }

        const thickness = depth * 0.1;
        const geometry = new THREE.CylinderGeometry(thickness * 0.7, thickness, height, 8);
        const branch = new THREE.Mesh(geometry, this.trunkMaterial);
        branch.position.set(x, y + height/2, z);
        branch.rotation.z = angle;
        this.treeGroup.add(branch);

        const nextX = x - Math.sin(angle) * height;
        const nextY = y + Math.cos(angle) * height;
        const numBranches = depth > 3 ? 2 : 3;
        for (let i = 0; i < numBranches; i++) {
            const nextAngle = angle + (Math.random() - 0.5) * 0.8;
            this.createBranch(nextX, nextY, z + (Math.random()-0.5), height * 0.8, nextAngle, depth - 1);
        }
    }

    addCrows() {
        this.crows = [];
        for (let i = 0; i < 5; i++) {
            const crowGroup = new THREE.Group();
            const body = new THREE.Mesh(
                new THREE.BoxGeometry(0.3, 0.1, 0.5),
                new THREE.MeshStandardMaterial({ color: 0x000000 })
            );
            crowGroup.add(body);
            const wingGeom = new THREE.BoxGeometry(0.6, 0.02, 0.3);
            const wingMat = new THREE.MeshStandardMaterial({ color: 0x111111 });
            const leftWing = new THREE.Mesh(wingGeom, wingMat);
            leftWing.position.x = -0.3;
            crowGroup.add(leftWing);
            const rightWing = new THREE.Mesh(wingGeom, wingMat);
            rightWing.position.x = 0.3;
            crowGroup.add(rightWing);

            crowGroup.position.set((Math.random()-0.5)*20, 5+Math.random()*5, (Math.random()-0.5)*10);
            this.crows.push({ group: crowGroup, wings: [leftWing, rightWing], offset: Math.random()*Math.PI*2, speed: 0.02+Math.random()*0.03 });
            this.scene.add(crowGroup);
        }
    }

    addFireflies() {
        this.fireflies = [];
        const glowMaterial = new THREE.MeshBasicMaterial({ color: 0xffe082 });
        for (let i = 0; i < 18; i++) {
            const dot = new THREE.Mesh(new THREE.SphereGeometry(0.03, 6, 6), glowMaterial);
            dot.position.set((Math.random() - 0.5) * 8, 3 + Math.random() * 6, (Math.random() - 0.5) * 8);
            this.fireflies.push({
                dot,
                ox: dot.position.x,
                oy: dot.position.y,
                oz: dot.position.z,
                speed: 0.6 + Math.random() * 1.2,
                phase: Math.random() * Math.PI * 2,
            });
            this.scene.add(dot);
        }
    }

    setupInteractions() {
        const handleMove = (x, y) => {
            const rect = this.container.getBoundingClientRect();
            this.mouse.x = ((x - rect.left) / rect.width) * 2 - 1;
            this.mouse.y = -((y - rect.top) / rect.height) * 2 + 1;
        };
        this.container.addEventListener('mousemove', (e) => handleMove(e.clientX, e.clientY));
        this.container.addEventListener('touchmove', (e) => handleMove(e.touches[0].clientX, e.touches[0].clientY));
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
        const time = Date.now() * 0.001;

        this.treeGroup.rotation.x += (this.mouse.y * 0.16 - this.treeGroup.rotation.x) * 0.04;
        this.treeGroup.rotation.y += (this.mouse.x * 0.2 + Math.sin(time * 0.5) * 0.08 - this.treeGroup.rotation.y) * 0.04;
        this.treeGroup.position.y = Math.sin(time * 0.75) * 0.08;

        this.leaves.forEach((leaf) => {
            leaf.position.y = leaf.userData.baseY + Math.sin(time * 2 + leaf.userData.swayOffset) * leaf.userData.swayAmp;
            leaf.rotation.y += 0.003;
        });

        this.crows.forEach(crow => {
            crow.group.position.x += crow.speed;
            if (crow.group.position.x > 15) crow.group.position.x = -15;
            const flap = Math.sin(time * 12 + crow.offset) * 0.6;
            crow.wings[0].rotation.z = flap;
            crow.wings[1].rotation.z = -flap;
        });

        this.fireflies.forEach((f) => {
            f.dot.position.x = f.ox + Math.sin(time * f.speed + f.phase) * 0.8;
            f.dot.position.y = f.oy + Math.cos(time * f.speed * 1.2 + f.phase) * 0.5;
            f.dot.position.z = f.oz + Math.sin(time * f.speed * 0.9 + f.phase) * 0.7;
            f.dot.scale.setScalar(0.6 + (Math.sin(time * 5 + f.phase) + 1) * 0.5);
        });

        this.rimLight.intensity = 0.8 + Math.sin(time * 1.2) * 0.2;
        this.camera.position.x = Math.sin(time * 0.25) * 0.8;
        this.camera.lookAt(0, 4.2, 0);

        this.renderer.render(this.scene, this.camera);
    }
}

window.addEventListener('load', () => {
    if (document.getElementById('tree-3d-container')) {
        new AgroTree('tree-3d-container');
    }
});
