# SF-Twin 배포 파이프라인 및 무중단 배포 전략 명세서 (DEPLOYMENT.md)

## 1. 배포 아키텍처 및 타겟 환경 (Deployment Target Architecture)
SF-Twin 데모 및 운영 인프라는 Edge 독립성(Offline Availability)과 클라우드 확장성(K8s Readiness)을 동시 충족하도록 설계되었습니다.

- **Group A (Cloud SaaS Layer: Asset, Sim, KPI Service):**
  - 단일/다중 호스트 인프라 상에서 Docker-Compose 기반으로 구동되며, Stateless 컨테이너 구조 및 환경변수 외부화 원칙을 준수하여 향후 Kubernetes(K8s) Helm Chart 배포 구조로 즉시 전환 가능한 논리적 격리를 유지합니다.
- **Group B (Edge & OT Field Layer: Edge Core, FastDDS):**
  - TSN/DDS 네트워크를 통한 초저지연(50ms 이내 패킷 도달, 100ms 이내 Failsafe E-Stop) 및 인터넷 단절 환경 독립 구동을 보장하기 위해 Docker-Compose 단일/다중 Edge PC 구조를 유지합니다.

---

## 2. CI/CD 파이프라인 및 컨테이너 레지스트리 (GHCR)
GitHub Actions 및 GitHub Packages (GHCR - `ghcr.io`)를 연동하여 이미지 빌드, 무결성 검증, 자동 태깅을 일원화합니다.

1. **Trigger:** `main` / `develop` 브랜치 Push 및 PR 승인 시 자동 트리거.
2. **Build & Tagging:** `ghcr.io/{owner}/sftwin-{service}:{version|sha}` 버전 태그 부여.
3. **Registry Push:** GHCR (GitHub Packages) 권한 통제 하에 안전하게 컨테이너 이미지 Push.

---

## 3. Nginx Upstream 기반 Blue/Green 무중단 배포 전략 (Zero-Downtime Deployment)
현장 관제 텔레메트리 스트리밍 및 API 단절(Downtime)을 방지하기 위해 Ingress Nginx의 Dynamic Upstream Reload 방식을 적용합니다.

1. **Green 환경 컨테이너 기동:** 신규 버전의 컨테이너를 신규 포트/네트워크로 기동.
2. **Health Check 검증:** `/healthz` 엔드포인트를 통한 독립성 검증(Status 200 OK) 완료 대기.
3. **Nginx Upstream Switch:** `nginx -s reload` 명령을 통해 트래픽 전량 Green 환경으로 무중단 이관.
4. **Blue 환경 자원 회수:** 기존 컨테이너 중지 및 자원 정리.

---

## 4. Sim-to-Real 제어 패키지 보안 및 무결성 검증 (SHA-256 & HMAC-SHA256)
Cloud Simulation Service에서 Edge Control 엔진으로 gRPC(Port 50051) 통신을 통해 배포되는 제어 스크립트/패킷에 대한 2단계 보안 검증을 수행합니다.

- **SHA-256 Checksum:** 전송 중 제어 스크립트 파일의 변조/손상 여부 검증.
- **HMAC-SHA256 디지털 서명:** gRPC 헤더 내 대칭키 기반 디지털 서명을 첨부하여 Edge Core 진입 시 무결성 검증을 통과한 패킷만 디코딩 및 실행.