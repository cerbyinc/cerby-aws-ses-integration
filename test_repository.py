from unittest.mock import MagicMock, patch

from models import HostedZoneRecord, Identity
from repository import (
    AWSHostedZoneRecordsRepository,
    AWSHostedZoneRepository,
    AWSIdentityRepository,
)


@patch("boto3.session.Session.client")
def test_identity_repository_add(mock_client: MagicMock):
    mock_client.return_value = mock_client
    mock_client.get_identity_dkim_attributes.return_value = {"DkimAttributes": {}}
    mock_client.verify_domain_dkim.return_value = {"DkimTokens": ["token-a", "token-b"]}
    identity_repo = AWSIdentityRepository()
    identity = Identity("my-identity.com")

    identity = identity_repo.add(identity)
    assert identity
    assert identity.verification_status == "Pending"
    assert identity.dkim_tokens == ["token-a", "token-b"]


@patch("boto3.session.Session.client")
def test_identity_repository_get(mock_client: MagicMock):
    mock_client.return_value = mock_client
    mock_client.get_identity_dkim_attributes.return_value = {
        "DkimAttributes": {
            "my-identity.com": {
                "DkimTokens": [
                    "token-a",
                    "token-b",
                ],
                "DkimVerificationStatus": "Pending",
            }
        }
    }
    identity_repo = AWSIdentityRepository()

    identity = identity_repo.get("my-identity.com")
    assert identity
    assert identity.verification_status == "Pending"
    assert identity.dkim_tokens == ["token-a", "token-b"]

    identity = identity_repo.get("unknown.com")
    assert identity is None


@patch("boto3.session.Session.client")
def test_hosted_zone_repository_get(mock_client: MagicMock):
    mock_client.return_value = mock_client
    mock_client.list_hosted_zones_by_name.return_value = {
        "HostedZones": [{"Name": "my-identity.com", "Id": "some-long-id"}]
    }
    hosted_zone_repo = AWSHostedZoneRepository()
    hosted_zone = hosted_zone_repo.get("my-identity.com")

    assert hosted_zone
    assert hosted_zone == "some-long-id"

    hosted_zone = hosted_zone_repo.get("unknown.com")
    assert hosted_zone is None


@patch("boto3.session.Session.client")
def test_hosted_zone_records_repository_add(mock_client: MagicMock):
    mock_client.return_value = mock_client
    mock_client.change_resource_record_sets()
    record = HostedZoneRecord(
        "some-long-id",
        "token-a._domainkey.us-east-1.my-identity.com",
        "CNAME",
        300,
        ["token-a.dkim.amazonses.com"],
    )

    hosted_zone_record_repo = AWSHostedZoneRecordsRepository()
    hosted_zone_record_repo.add(record)

    mock_client.change_resource_record_sets.assert_called()


@patch("boto3.session.Session.client")
def test_hosted_zone_records_repository_get(mock_client: MagicMock):
    mock_client.return_value = mock_client
    mock_client.list_resource_record_sets.return_value = {
        "ResourceRecordSets": [
            {
                "Name": "token-a._domainkey.us-east-1.my-identity.com",
                "Type": "CNAME",
                "TTL": 300,
                "ResourceRecords": [{"Value": "token-a.dkim.amazonses.com"}],
            }
        ]
    }
    record = HostedZoneRecord(
        "some-long-id",
        "token-a._domainkey.us-east-1.my-identity.com",
        "CNAME",
        300,
        ["token-a.dkim.amazonses.com"],
    )

    hosted_zone_record_repo = AWSHostedZoneRecordsRepository()
    records = hosted_zone_record_repo.get("some-long-id")
    assert record in records

    records = hosted_zone_record_repo.get("short-id")
    assert record not in records
