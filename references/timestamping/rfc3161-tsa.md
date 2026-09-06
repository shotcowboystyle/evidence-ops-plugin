# RFC 3161 Time Stamping Authorities

This document describes the implementation and usage of RFC 3161 Time Stamping Authority (TSA) protocols. Operators use these standardized methods to obtain a trusted, digitally signed timestamp from an authoritative third party, mathematically proving that a specific hash was witnessed by the authority at a specific, coordinated network time.

## Why it matters

While decentralized methods like OpenTimestamps offer robust mathematical proofs without relying on a central point of failure, many legal, corporate, and regulatory frameworks mandate reliance on centralized, accredited trust providers. An RFC 3161 TSA provides an X.509-signed attestation of time. This is the established standard in digital forensics, document signing, and enterprise compliance. Using a TSA defends against local clock manipulation (such as changing the system time before hashing) and ensures the evidence's temporal origin is validated by a recognized, legally compliant entity.

## Tools

| Tool | Platform | Notes |
| --- | --- | --- |
| `openssl ts` | both | The standard subcommand in OpenSSL for generating and verifying TSA requests. Native on macOS and Linux. |
| `curl` | both | Used to transport the timestamp request to the TSA server over HTTP/HTTPS. |
| `shasum` | macOS / Linux | Primary hashing tool used to generate the digest before submission to ensure privacy. |

## Practical recipes

### Creating a Timestamp Request
First, generate a binary request file `.tsq` from the target file or manifest. We use the `-cert` flag to request that the TSA includes its signing certificate in the response payload for easier verification.

```bash
# macOS and Linux
openssl ts -query -data evidence.raw -cert -sha256 -out evidence.tsq
```

### Submitting the Request to a TSA
Use `curl` to submit the `.tsq` payload to a public or private Time Stamping Authority. You must specify the correct content type for the server to recognize the payload.

```bash
# Submit to a public TSA (example URL)
curl -H "Content-Type: application/timestamp-query" \
     --data-binary "@evidence.tsq" \
     http://freetsa.org/tsr > evidence.tsr
```

### Inspecting the Response
You can read the contents of the binary `.tsr` (Time Stamp Response) file to confirm the time provided by the server and the hashing algorithm used.

```bash
# View the response details in human-readable text
openssl ts -reply -in evidence.tsr -text
```

### Verifying the Timestamp
To prove the timestamp is valid, you must verify the `.tsr` file against the original data file and the Certificate Authority (CA) certificate chain that issued the TSA's signing certificate.

```bash
# Verify the token against the data file and a trusted CA certificate bundle
openssl ts -verify -in evidence.tsr -data evidence.raw -CAfile cacert.pem
```

## Pitfalls

*   **Unverified TSA Certificates:** Relying on a TSA without verifying its root of trust (the CA certificate chain) renders the timestamp legally meaningless. Always obtain and archive the public keys of the TSA.
*   **Privacy considerations:** Submitting the raw data file directly to the TSA transmits the data over the network. Always use the hash of the data (or let `openssl ts` compute it locally as shown in the query command) to ensure only the fingerprint leaves your isolated network.
*   **Transient infrastructure:** Free or public TSAs might rotate their keys, lose funding, or go offline entirely. Archiving the TSA's certificate bundle alongside the `.tsr` file is critical for long-term verification years in the future.
*   **Mismatched algorithms:** Ensure the hash algorithm used in the request (`-sha256`) matches the expected standard. Legacy TSAs might default to SHA-1 if not specified, which should be overridden to avoid collision risks.
*   **macOS OpenSSL variants:** macOS has historically shipped with LibreSSL by default in some environments, but modern macOS (via Homebrew or Xcode tools) provides robust OpenSSL. Ensure you are using an up-to-date binary that properly supports the `ts` subcommand.

## See also

*   [OpenTimestamps](opentimestamps.md)
*   [Algorithms and Manifests](../hashing/algorithms-and-manifests.md)
*   [Legal Considerations](../custody/legal-considerations.md)

## Advanced Operational Scenarios

### Establishing a Private TSA
For high-security environments where evidence cannot be acknowledged by a public authority (e.g., classified military operations or sensitive internal HR investigations), organizations often establish a private internal TSA. This involves deploying a dedicated hardware security module (HSM) and establishing a private Root CA. Operators must ensure that the Root CA is documented in the Chain of Custody to prove the internal TSA's validity to external auditors.

### Long-Term Validation (LTV)
An RFC 3161 timestamp is only valid as long as the TSA's certificate is valid. If the certificate expires or is revoked, the timestamp may become legally questionable. To counter this, operators must utilize Long-Term Validation (LTV) techniques. This involves periodically re-timestamping the original `.tsr` file and the evidence using a new, currently valid TSA before the old certificate expires, creating a nested chain of trust that extends indefinitely.

## Timestamping the Timestamp
Because a TSA relies on standard PKI certificates that typically expire after 1 to 3 years, an operator must proactively "timestamp the timestamp." Before the original TSA certificate expires, the operator hashes the original evidence file *and* the original `.tsr` file together, and submits this combined hash to a new TSA (or the same TSA with a newly issued certificate). This creates a cryptographically verifiable chain, proving the first timestamp was valid at the time it was generated, extending the legal validity of the evidence indefinitely as long as the chain is maintained.

## Glossary of Terms
*   **TSA (Time Stamping Authority):** A trusted third party that provides cryptographically secure attestations of time, proving a hash existed at a specific moment.
*   **PKI (Public Key Infrastructure):** The complex system of digital certificates, Certificate Authorities, and registration authorities that verify and authenticate the validity of each party involved in an electronic transaction.
*   **X.509:** The standard defining the format of public key certificates, serving as the foundational trust structure for RFC 3161 timestamping.
*   **LTV (Long-Term Validation):** The archival process of capturing and nesting certificate status information (like OCSP responses) and subsequent timestamps to ensure a signature remains verifiable decades after the original certificate expires.
