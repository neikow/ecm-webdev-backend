# python
# !/usr/bin/env python3
"""
Generate self-signed TLS certificates for local development.

Generates two cert/key pairs:
 - certs/localhost-5173.key.pem  / certs/localhost-5173.crt.pem
 - certs/localhost-8000.key.pem  / certs/localhost-8000.crt.pem

Certificates contain SubjectAlternativeName for DNS 'localhost' and IP '127.0.0.1'.
"""
from __future__ import annotations

import argparse
import ipaddress
import os
from datetime import datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.x509 import DNSName, IPAddress, SubjectAlternativeName, BasicConstraints, KeyUsage
from cryptography.x509.oid import NameOID

DEFAULT_DAYS = 365


def generate_self_signed_cert(
        out_dir: Path,
        basename: str,
        common_name: str = "localhost",
        dns_names: list[str] | None = None,
        ip_addresses: list[str] | None = None,
        days_valid: int = DEFAULT_DAYS,
) -> tuple[Path, Path]:
    dns_names = dns_names or ["localhost"]
    ip_addresses = ip_addresses or ["127.0.0.1"]

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )

    san_list = []
    for d in dns_names:
        san_list.append(DNSName(d))
    for ip in ip_addresses:
        san_list.append(IPAddress(ipaddress.ip_address(ip)))

    now = datetime.utcnow()
    cert_builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=days_valid))
        .add_extension(SubjectAlternativeName(san_list), critical=False)
        .add_extension(BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
    )

    cert = cert_builder.sign(private_key=key, algorithm=hashes.SHA256())

    out_dir.mkdir(parents=True, exist_ok=True)
    key_path = out_dir / f"{basename}.key.pem"
    cert_path = out_dir / f"{basename}.crt.pem"

    # write private key
    key_bytes = key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=NoEncryption(),
    )
    key_path.write_bytes(key_bytes)
    os.chmod(key_path, 0o600)

    # write certificate
    cert_bytes = cert.public_bytes(Encoding.PEM)
    cert_path.write_bytes(cert_bytes)

    return key_path, cert_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate self-signed certs for local dev")
    parser.add_argument("--out", "-o", default="certs", help="output directory (default: certs)")
    parser.add_argument("--days", "-d", type=int, default=DEFAULT_DAYS, help="validity days")
    args = parser.parse_args()

    out_dir = Path(args.out)

    pairs = [
        ("localhost-5173", 5173),
        ("localhost-8000", 8000),
    ]

    for basename, _port in pairs:
        key_path, cert_path = generate_self_signed_cert(
            out_dir=out_dir,
            basename=basename,
            common_name="localhost",
            dns_names=["localhost"],
            ip_addresses=["127.0.0.1"],
            days_valid=args.days,
        )
        print(f"Generated {key_path} and {cert_path}")

    print()
    print("Note: browsers may not trust these self-signed certs by default.")
    print("To trust a certificate on macOS for local development:")
    print(r"  sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain <path-to-cert>")
    print("Alternatively add the .crt.pem file to your keychain via Keychain Access and mark it trusted.")


if __name__ == "__main__":
    main()
