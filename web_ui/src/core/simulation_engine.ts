import { ThreeViewportController } from './three_viewport_controller';

export class SimulationEngine {
    private viewportController: ThreeViewportController;
    private isRunning: boolean = false;
    private animationTimer: number | null = null;
    private startTime: number = 0;

    constructor(viewportController: ThreeViewportController) {
        this.viewportController = viewportController;
    }

    public start(): void {
        if (this.isRunning) return;
        this.isRunning = true;
        this.startTime = performance.now();

        const step = () => {
            if (!this.isRunning) return;

            const elapsed = (performance.now() - this.startTime) / 1000; // 초 단위 경과 시간

            // 1. 머신 텐딩 로봇 #1: CNC <-> 컨베이어 피킹 관절 애니메이션 (Sin/Cos 궤적)
            const r1Joint1 = Math.sin(elapsed * 1.5) * 0.8; // Base Swivel
            const r1Joint2 = (Math.sin(elapsed * 2.0) + 1) * 0.4 - 0.2; // Shoulder
            const r1Joint3 = (Math.cos(elapsed * 2.0) + 1) * 0.5 - 0.2; // Elbow

            // 2. 조립/검사 로봇 #2: 주기적 픽앤플레이스 관절 애니메이션
            const r2Joint1 = Math.cos(elapsed * 1.2) * 0.7;
            const r2Joint2 = (Math.cos(elapsed * 1.8) + 1) * 0.35 - 0.1;
            const r2Joint3 = (Math.sin(elapsed * 1.8) + 1) * 0.45 - 0.1;

            // 3. 자율이동로봇 AMR: 바닥 타원 순회 경로 주행 (ROS 좌표계 X, Y 이동)
            const amrRadiusX = 2.8;
            const amrRadiusY = 1.6;
            const amrSpeed = 0.8;
            const amrX = Math.cos(elapsed * amrSpeed) * amrRadiusX;
            const amrY = Math.sin(elapsed * amrSpeed) * amrRadiusY - 1.0;

            // AMR 진행 방향을 향하는 요(Yaw) 회전 계산
            const headingAngle = Math.atan2(
                Math.cos(elapsed * amrSpeed) * amrRadiusY * amrSpeed,
                -Math.sin(elapsed * amrSpeed) * amrRadiusX * amrSpeed
            );
            const halfAngle = headingAngle / 2;
            const qz = Math.sin(halfAngle);
            const qw = Math.cos(halfAngle);

            // 4. 텔레메트리 프레임 생성 및 링버퍼 주입
            this.viewportController.pushTelemetryFrame({
                timestamp: performance.now(),
                jointPositions: {
                    robot_arm_1: {
                        joint_1: r1Joint1,
                        joint_2: r1Joint2,
                        joint_3: r1Joint3,
                    },
                    robot_arm_2: {
                        joint_1: r2Joint1,
                        joint_2: r2Joint2,
                        joint_3: r2Joint3,
                    },
                },
                tfTransforms: {
                    amr_01: {
                        position: [amrX, amrY, 0.0],
                        rotation: [0, 0, qz, qw],
                    },
                },
            });

            this.animationTimer = window.requestAnimationFrame(step);
        };

        this.animationTimer = window.requestAnimationFrame(step);
    }

    public stop(): void {
        this.isRunning = false;
        if (this.animationTimer !== null) {
            window.cancelAnimationFrame(this.animationTimer);
            this.animationTimer = null;
        }
    }

    public reset(): void {
        this.stop();
        // 초기 원점 위치 및 관절각으로 복귀 프레임 발행
        this.viewportController.pushTelemetryFrame({
            timestamp: performance.now(),
            jointPositions: {
                robot_arm_1: { joint_1: 0, joint_2: 0, joint_3: 0 },
                robot_arm_2: { joint_1: 0, joint_2: 0, joint_3: 0 },
            },
            tfTransforms: {
                amr_01: {
                    position: [0.0, -2.5, 0.0],
                    rotation: [0, 0, 0, 1],
                },
            },
        });
    }
}
