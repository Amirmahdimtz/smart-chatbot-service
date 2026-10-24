# Phase 05 — Third-party synthetic CI S3 image supply-chain review (NOT APPROVED)

**Dossier date:** 2026-10-24. **Review status:** `PENDING_SECURITY_ACCEPTANCE`. This review documents inspectable source and risks, not an independent signer, a proven provenance chain or Production authorization.

## Artifact and bounded purpose

- CI image (S3 compatible) `ghcr.io/coollabsio/minio@sha256:69b55a1c1c5dc285ce04db96689f5b2102317fc77a50680a1874ca6efd1c87f9`. It is used only in the ephemeral GitHub Actions `ingestion-integration` job with generated synthetic-only payloads, random per-run root credentials and host-only loopback port 9000. It is not part of the runtime deployment Dockerfile or an approved enterprise S3 supplier.
- Verified **public metadata**: [GitHub Container Registry package](https://github.com/coollabsio/minio/pkgs/container/minio) lists the matching multi-arch digest and release tag `RELEASE.2025-10-15T17-29-55Z`; that corroborates the registry digest, not cryptographic publisher attestation.
- Verified **published build description**: [source repository](https://github.com/coollabsio/minio), [Dockerfile](https://github.com/coollabsio/minio/blob/main/Dockerfile), and [GitHub Actions build workflow](https://github.com/coollabsio/minio/blob/main/.github/workflows/build-minio.yml). The publicly readable Dockerfile clones the upstream MinIO Git repository and compiles a selected release. No independently trusted mapping from the digest to the exact source/build environment was established.

## Explicit unresolved risks and controls

| Observation | Risk or limitation | Status |
| --- | --- | --- |
| Third-party publisher; digest pinned | Digest prevents accidental tag drift, not a malicious or compromised publisher | UNACCEPTED_PENDING_OWNER |
| Dockerfile includes floating build/runtime bases (`golang:1.24-alpine`, `ubi9/ubi-micro:latest`) and source checkout without established verified attestation for this published digest | Source transparency is not reproducible-build / signed provenance evidence | PENDING_SECURITY_REVIEW |
| Published Dockerfile uses `chmod -R 777 /usr/bin`; it does not declare an unprivileged runtime `USER` | Overly permissive image design; inspect actual runtime image/user before approving | PENDING_SECURITY_REVIEW |
| CI service on host loopback, disposable credentials, synthetic files, no organization secrets/data | Reduces sensitivity but does not prove network egress isolation or make the publisher trustworthy | MITIGATION_ONLY |
| Separate ClamAV CI image is digest pinned and signature refresh disabled during isolated test run | CI verifies real scanner behavior for preloaded signatures, not up-to-date enterprise AV efficacy | GROUP_C_ENTERPRISE_POLICY_REQUIRED |

## Required accountable decision

A designated independent **Security** reviewer, with Architecture/Operations as appropriate, must either:

1. Accept this exact digest strictly for **synthetic CI-only** use, documenting image/runtime scan, source and license evaluation, signer identity and any compensating controls; **or**
2. Reject and replace it with an independently approved S3-compatible integration service image, rerun all Group A/B acceptance evidence and record the resulting tested SHA.

**Neither option has been approved.** Do not promote this test image into a real deployment or call Phase05 `CLOSED` from this dossier alone. Real On-Prem object storage, credentials, backups, retention, and audit belong to Phase18. D-07/D-08 organization access/content policy remain blocked decisions.
