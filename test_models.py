from models import HostedZoneRecord, Identity

region = "us-east-1"
hosted_zone_id = "a2b3c4d5"


def test_identity_dkim_records():
    identity = Identity("my-identity.com", ["token-a", "token-b"], "Pending")
    tokens = [
        HostedZoneRecord(
            hosted_zone_id,
            "token-a._domainkey.us-east-1.my-identity.com",
            "CNAME",
            300,
            ["token-a.dkim.amazonses.com"],
        ),
        HostedZoneRecord(
            hosted_zone_id,
            "token-b._domainkey.us-east-1.my-identity.com",
            "CNAME",
            300,
            ["token-b.dkim.amazonses.com"],
        ),
    ]

    assert tokens == identity.dkim_tokens_as_records(hosted_zone_id, region)
