class AgroTree {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, this.container.clientWidth / this.container.clientHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.container.appendChild(this.renderer.domElement);

        this.mouse = new THREE.Vector2();
        this.targetRotation = new THREE.Vector2();
        
        this.init();
        this.addCrows();
        this.animate();
        this.setupInteractions();
    }

    init() {
        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);

        const sunLight = new THREE.DirectionalLight(0xFFE082, 1);
        sunLight.position.set(5, 10, 5);
        this.scene.add(sunLight);

        // Original AgroSense Colors
        this.trunkMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x3E2723, // Original Deep Brown
            roughness: 0.9
        });
        this.leafMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x4E6E5D, // Original Moss Green
            emissive: 0xDAA520, 
            emissiveIntensity: 0.2
        });

        this.treeGroup = new THREE.Group();
        this.createBranch(0, 0, 0, 1.2, 0, 6);
        this.scene.add(this.treeGroup);

        this.camera.position.set(0, 4, 10);
        this.camera.lookAt(0, 4, 0);
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

    setupInteractions() {
        const handleMove = (x, y) => {
            const rect = this.container.getBoundingClientRect();
            this.mouse.x = ((x - rect.left) / rect.width) * 2 - 1;
            this.mouse.y = -((y - rect.top) / rect.height) * 2 + 1;
        };
        this.container.addEventListener('mousemove', (e) => handleMove(e.clientX, e.clientY));
        this.container.addEventListener('touchmove', (e) => handleMove(e.touches[0].clientX, e.touches[0].clientY));
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        const time = Date.now() * 0.001;

        this.treeGroup.rotation.x += (this.mouse.y * 0.2 - this.treeGroup.rotation.x) * 0.05;
        this.treeGroup.rotation.y += (this.mouse.x * 0.2 - this.treeGroup.rotation.y) * 0.05;

        this.crows.forEach(crow => {
            crow.group.position.x += crow.speed;
            if (crow.group.position.x > 15) crow.group.position.x = -15;
            const flap = Math.sin(time * 12 + crow.offset) * 0.6;
            crow.wings[0].rotation.z = flap;
            crow.wings[1].rotation.z = -flap;
        });

        this.renderer.render(this.scene, this.camera);
    }
}

window.addEventListener('load', () => {
    if (document.getElementById('tree-3d-container')) {
        new AgroTree('tree-3d-container');
    }
});
