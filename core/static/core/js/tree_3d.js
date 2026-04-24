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
        const ambientLight = new THREE.AmbientLight(0xffffff, 1.0);
        this.scene.add(ambientLight);

        const sunLight = new THREE.DirectionalLight(0xffe9b5, 1.5);
        sunLight.position.set(5, 10, 7);
        this.scene.add(sunLight);

        this.wheatGroup = new THREE.Group();
        this.scene.add(this.wheatGroup);

        // Materials
        const stemMat = new THREE.MeshStandardMaterial({ color: 0xD4AF37, roughness: 0.5 }); // Golden stem
        const grainMat = new THREE.MeshStandardMaterial({ color: 0xFFD700, roughness: 0.3 }); // Bright gold grains

        // Create Wheat Stalks
        for (let i = 0; i < 5; i++) {
            const stalk = new THREE.Group();
            stalk.position.set((Math.random()-0.5)*2, 0, (Math.random()-0.5)*2);
            
            // Stem
            const stemGeom = new THREE.CylinderGeometry(0.02, 0.04, 5, 8);
            const stem = new THREE.Mesh(stemGeom, stemMat);
            stem.position.y = 2.5;
            stalk.add(stem);

            // Grains (The "Ear" of the wheat)
            for (let j = 0; j < 18; j++) {
                const grainWrap = new THREE.Group();
                grainWrap.position.y = 4 + (j * 0.12);
                grainWrap.position.x = Math.sin(j) * 0.12;
                grainWrap.position.z = Math.cos(j) * 0.12;
                
                const grain = new THREE.Mesh(new THREE.IcosahedronGeometry(0.1, 0), grainMat);
                grainWrap.add(grain);
                
                // Add "Awns" (The hair-like parts of wheat)
                const awn = new THREE.Mesh(new THREE.CylinderGeometry(0.005, 0.005, 0.4), stemMat);
                awn.position.y = 0.2;
                awn.rotation.x = 0.2;
                grainWrap.add(awn);
                
                stalk.add(grainWrap);
            }
            
            this.wheatGroup.add(stalk);
        }

        this.camera.position.set(0, 4, 10);
        this.camera.lookAt(0, 3, 0);
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        const time = performance.now() * 0.001;

        // Auto 360 Rotation
        this.wheatGroup.rotation.y += 0.01;
        
        // Gentle swaying
        this.wheatGroup.children.forEach((stalk, i) => {
            stalk.rotation.x = Math.sin(time + i) * 0.05;
            stalk.rotation.z = Math.cos(time * 0.8 + i) * 0.05;
        });

        this.renderer.render(this.scene, this.camera);
    }
}

window.addEventListener('load', () => {
    if (document.getElementById('tree-3d-container')) {
        new AgroTree('tree-3d-container');
    }
});
