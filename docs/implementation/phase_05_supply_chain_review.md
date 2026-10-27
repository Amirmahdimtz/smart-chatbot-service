# Phase 05 — Supply chain evidence and residual CI image risk

> **Gate classification — 2026-10-27 / Implementation Plan v1.1.1:** This file assesses the signed, pinned **synthetic CI-only** S3 test image (Group A/B), not an image approved for organization Production. Runtime/license/vulnerability risk not yet assessed or accepted must be reported as unresolved **CI-only residual risk**, not mislabeled as a missing corporate On-Prem/Release test. `ADR-0008` separately requires independently accepted **technical** Phase05 DoD; this note neither waives that explicit phase-specific gate nor simulates Security reviewer approval. Final organizational image/security/operations acceptance and real On-Prem object storage are **Group C — Phase18**.

**Reviewed date:** 2026-10-24. **Exact tested source:** 15f4326cd5dba898a185dd95f067969ca90aa01c. **CI:** https://github.com/Amirmahdimtz/smart-chatbot-service/actions/runs/40103038011, all 6 jobs SUCCESS.

## Artifact change

The previous third-party Coollabs MinIO CI image was removed. The isolated real S3 integration now uses **upstream SeaweedFS 4.48**, image:

    chrislusf/seaweedfs@sha256:4e61d15fd35994cb1e43e1e553dff106794841fd9a99ade2fc8c8bfce4d7872d

This immutable digest was observed on the CI Docker pull. The official SeaweedFS source repository is https://github.com/seaweedfs/seaweedfs and the upstream release is https://github.com/seaweedfs/seaweedfs/releases/tag/4.48 .

## Automated provenance proof (actual Group B run)

The workflow installs the Sigstore cosign installer from pinned upstream commit ba7bc0a3fef59531c69a25acd34668d6d3fe6f22 and **requires successful cosign verify before starting the S3 server**, with GitHub Actions certificate OIDC issuer and expected identity:

    https://github.com/seaweedfs/seaweedfs/.github/workflows/container_release_unified.yml@refs/tags/4.48

GitHub Actions CI run 40103038011 showed successful cosign verification, trusted certificate authority validation and offline verification of public transparency-log claims for the exact image digest. A failed verifier fails the integration job. This is **verified publisher/release-workflow provenance**, not merely pinning a tag or trusting a registry label.

CI uses masked, random per-run S3 credentials, synthetic files, loopback-only S3 endpoint, named **disposable** persistent data volume and bounded genuine S3 operations. Real tests confirm incorrect credentials and unsigned anonymous access are rejected, conditional write is immutable, bytes survive full container replacement, and a separate worker actually runs ClamAV before durable awaiting_approval.

## Residual security risks and approval

| Control | Result |
| --- | --- |
| Trusted signer/expected release workflow for exact digest | PASSED in CI |
| Immutable image reference and repeatable image selection | PASSED |
| Real S3 deny-invalid/anonymous auth and immutable data access | PASSED |
| Real object and worker recovery after container replacement | PASSED |
| OCI image vulnerability scan/independent license and runtime policy acceptance | NOT_APPROVED; not claimed as performed |
| Independent accountable Security and Architecture CI-only residual-risk sign-off | NOT_SIGNED |
| Actual production S3, IdP, retention, backup, HA/DR and network isolation | Group C, Phase18, NOT_RUN |

Strict Python pip-audit does **not** scan OCI layers. Signing verifies declared builder identity, not absence of vulnerabilities. The test image is never declared suitable for organization deployment. The Security risk owner must independently assess residual risk and accept this **synthetic-only CI** image or mandate change. No owner signature has been invented. Technical DoD PENDING_INDEPENDENT_REVIEW; Phase05 IN_PROGRESS; Production NOT_READY.
