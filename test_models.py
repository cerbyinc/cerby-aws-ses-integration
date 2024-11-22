from models import DkimAttributes, HostedZoneRecord

region = "us-east-1"
hosted_zone_id = "a2b3c4d5"


def test_identity_dkim_records():
    identity = DkimAttributes(
        name="my-identity.com",
        verification_status="Pending",
        dkim_tokens=["token-a", "token-b"],
    )
    tokens = [
        HostedZoneRecord(
            "token-a._domainkey.my-identity.com",
            "CNAME",
            300,
            ["token-a.dkim.amazonses.com"],
        ),
        HostedZoneRecord(
            "token-b._domainkey.my-identity.com",
            "CNAME",
            300,
            ["token-b.dkim.amazonses.com"],
        ),
    ]

    assert tokens == identity.dkim_tokens_as_records("my-identity.com")
