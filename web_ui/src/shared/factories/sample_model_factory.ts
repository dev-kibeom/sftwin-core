import * as THREE from 'three';

export class SampleModelFactory {
    /**
     * 1. 6축 협동로봇/매니퓰레이터 (공정 피킹/가공 로봇)
     */
    public static createRobotArm(assetId: string = 'robot_arm'): THREE.Group {
        const root = new THREE.Group();
        root.name = assetId;

        // Base Frame
        const baseGeo = new THREE.CylinderGeometry(0.5, 0.6, 0.3, 32);
        const darkMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.8, roughness: 0.3 });
        const baseMesh = new THREE.Mesh(baseGeo, darkMat);
        baseMesh.position.y = 0.15;
        root.add(baseMesh);

        // Joint 1 (Base 회전축)
        const joint1 = new THREE.Group();
        joint1.name = 'joint_1';
        joint1.position.y = 0.3;

        const shoulderGeo = new THREE.CylinderGeometry(0.35, 0.35, 0.4, 24);
        const blueMat = new THREE.MeshStandardMaterial({ color: 0x2563eb, metalness: 0.6, roughness: 0.3 });
        const shoulderMesh = new THREE.Mesh(shoulderGeo, blueMat);
        shoulderMesh.position.y = 0.2;
        joint1.add(shoulderMesh);

        // Joint 2 (Lower Arm)
        const joint2 = new THREE.Group();
        joint2.name = 'joint_2';
        joint2.position.y = 0.4;

        const arm1Geo = new THREE.BoxGeometry(0.24, 1.4, 0.24);
        const arm1Mesh = new THREE.Mesh(arm1Geo, darkMat);
        arm1Mesh.position.y = 0.7;
        joint2.add(arm1Mesh);

        // Joint 3 (Upper Arm & Wrist)
        const joint3 = new THREE.Group();
        joint3.name = 'joint_3';
        joint3.position.y = 1.4;

        const arm2Geo = new THREE.BoxGeometry(0.2, 1.1, 0.2);
        const arm2Mesh = new THREE.Mesh(arm2Geo, blueMat);
        arm2Mesh.position.y = 0.55;
        joint3.add(arm2Mesh);

        // End-Effector (그리퍼)
        const gripperGeo = new THREE.BoxGeometry(0.3, 0.1, 0.15);
        const yellowMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.5, roughness: 0.4 });
        const gripperMesh = new THREE.Mesh(gripperGeo, yellowMat);
        gripperMesh.position.y = 1.15;
        joint3.add(gripperMesh);

        joint2.add(joint3);
        joint1.add(joint2);
        root.add(joint1);

        return root;
    }

    /**
     * 2. 자율이동로봇 (AMR/AGV - 상단 리프트 포함)
     */
    public static createAmr(assetId: string = 'amr_01'): THREE.Group {
        const root = new THREE.Group();
        root.name = assetId;

        // Body Chassis
        const bodyGeo = new THREE.BoxGeometry(1.6, 0.4, 1.0);
        const bodyMat = new THREE.MeshStandardMaterial({ color: 0x0ea5e9, metalness: 0.7, roughness: 0.2 });
        const bodyMesh = new THREE.Mesh(bodyGeo, bodyMat);
        bodyMesh.position.y = 0.25;
        root.add(bodyMesh);

        // LiDAR Sensor Dome
        const lidarGeo = new THREE.CylinderGeometry(0.12, 0.12, 0.15, 16);
        const blackMat = new THREE.MeshStandardMaterial({ color: 0x0f172a });
        const lidarMesh = new THREE.Mesh(lidarGeo, blackMat);
        lidarMesh.position.set(0.6, 0.5, 0);
        root.add(lidarMesh);

        // Wheels (4-Wheel)
        const wheelGeo = new THREE.CylinderGeometry(0.18, 0.18, 0.1, 16);
        const wheelMat = new THREE.MeshStandardMaterial({ color: 0x334155 });
        const wheelPositions = [
            [-0.5, 0.18, 0.55],
            [0.5, 0.18, 0.55],
            [-0.5, 0.18, -0.55],
            [0.5, 0.18, -0.55],
        ];

        wheelPositions.forEach(([x, y, z]) => {
            const wheel = new THREE.Mesh(wheelGeo, wheelMat);
            wheel.rotation.x = Math.PI / 2;
            wheel.position.set(x, y, z);
            root.add(wheel);
        });

        return root;
    }

    /**
     * 3. 스마트 컨베이어 벨트 라인
     */
    public static createConveyor(assetId: string = 'conveyor_01'): THREE.Group {
        const root = new THREE.Group();
        root.name = assetId;

        // Conveyor Frame (길이 6m, 폭 1.2m)
        const frameGeo = new THREE.BoxGeometry(6.0, 0.15, 1.2);
        const frameMat = new THREE.MeshStandardMaterial({ color: 0x475569, metalness: 0.8, roughness: 0.3 });
        const frameMesh = new THREE.Mesh(frameGeo, frameMat);
        frameMesh.position.y = 0.75;
        root.add(frameMesh);

        // Belt Surface
        const beltGeo = new THREE.BoxGeometry(5.8, 0.02, 1.0);
        const beltMat = new THREE.MeshStandardMaterial({ color: 0x18181b, roughness: 0.9 });
        const beltMesh = new THREE.Mesh(beltGeo, beltMat);
        beltMesh.position.y = 0.84;
        root.add(beltMesh);

        // Support Legs (4개 다리)
        const legGeo = new THREE.CylinderGeometry(0.06, 0.06, 0.75, 16);
        const legPositions = [
            [-2.6, 0.375, 0.5],
            [2.6, 0.375, 0.5],
            [-2.6, 0.375, -0.5],
            [2.6, 0.375, -0.5],
        ];

        legPositions.forEach(([x, y, z]) => {
            const leg = new THREE.Mesh(legGeo, frameMat);
            leg.position.set(x, y, z);
            root.add(leg);
        });

        return root;
    }

    /**
     * 4. CNC 머시닝 센터 / 사출성형 설비 (KAMP 주요 데이터 소스)
     */
    public static createCncMachine(assetId: string = 'cnc_machine_01'): THREE.Group {
        const root = new THREE.Group();
        root.name = assetId;

        // Machine Main Body
        const bodyGeo = new THREE.BoxGeometry(2.4, 2.8, 2.2);
        const bodyMat = new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.6, roughness: 0.4 });
        const bodyMesh = new THREE.Mesh(bodyGeo, bodyMat);
        bodyMesh.position.y = 1.4;
        root.add(bodyMesh);

        // Front Window (작업 챔버 유리창)
        const windowGeo = new THREE.PlaneGeometry(1.4, 1.2);
        const glassMat = new THREE.MeshPhysicalMaterial({
            color: 0x38bdf8,
            transparent: true,
            opacity: 0.5,
            roughness: 0.1,
            transmission: 0.9,
        });
        const windowMesh = new THREE.Mesh(windowGeo, glassMat);
        windowMesh.position.set(0, 1.6, 1.11);
        root.add(windowMesh);

        // Status Indicator Tower (3색 타워 램프: Green/Yellow/Red)
        const towerGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.6, 16);
        const towerMesh = new THREE.Mesh(towerGeo, new THREE.MeshStandardMaterial({ color: 0x64748b }));
        towerMesh.position.set(1.0, 3.1, 0.8);
        root.add(towerMesh);

        const lampGeo = new THREE.CylinderGeometry(0.06, 0.06, 0.15, 16);
        const greenLamp = new THREE.Mesh(
            lampGeo,
            new THREE.MeshStandardMaterial({ color: 0x22c55e, emissive: 0x22c55e, emissiveIntensity: 0.8 })
        );
        greenLamp.position.set(1.0, 3.4, 0.8);
        root.add(greenLamp);

        return root;
    }
}
