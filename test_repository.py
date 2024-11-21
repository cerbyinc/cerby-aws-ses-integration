from models import DkimAttributes, HostedZoneRecord, MailFromDomainAttributes
from repository import (
    AWSHostedZoneRecordsRepository,
    AWSHostedZoneRepository,
    AWSIdentityRepository,
)


def test_identity_repository_add_dkim_attributes(mock_boto3_client_patch):
    identity_repo = AWSIdentityRepository()
    identity_dkim_attributes = DkimAttributes("new-identity-present-in-route53.com")

    identity_dkim_attributes = identity_repo.add_dkim_attributes(
        identity_dkim_attributes
    )
    assert identity_dkim_attributes
    assert identity_dkim_attributes.verification_status == "Pending"
    assert identity_dkim_attributes.dkim_tokens == ["token-a", "token-b"]


def test_identity_repository_get_dkim_attributes(mock_boto3_client_patch):
    identity_repo = AWSIdentityRepository()

    identity_dkim_attributes = identity_repo.get_dkim_attributes(
        "existing-identity-present-in-route53.com"
    )
    assert identity_dkim_attributes
    assert identity_dkim_attributes.verification_status == "Pending"
    assert identity_dkim_attributes.dkim_tokens == ["token-a", "token-b"]

    identity_dkim_attributes = identity_repo.get_dkim_attributes("unknown.com")
    assert identity_dkim_attributes is None


def test_identity_repository_add_mail_from_domain_attributes(mock_boto3_client_patch):
    identity_repo = AWSIdentityRepository()
    identity_mail_from_domain_attributes = MailFromDomainAttributes(
        name="existing-identity-present-in-route53.com",
        mail_from_domain="bounce.existing-identity-present-in-route53.com",
    )

    identity_mail_from_domain_attributes = (
        identity_repo.add_mail_from_domain_attributes(
            identity_mail_from_domain_attributes
        )
    )
    assert identity_mail_from_domain_attributes
    assert identity_mail_from_domain_attributes.mail_from_domain_status == "Pending"


def test_identity_repository_get_mail_from_domain_attributes(mock_boto3_client_patch):
    identity_repo = AWSIdentityRepository()

    identity_mail_from_domain_attributes = (
        identity_repo.get_mail_from_domain_attributes(
            name="existing-identity-present-in-route53.com"
        )
    )
    assert identity_mail_from_domain_attributes
    assert identity_mail_from_domain_attributes.mail_from_domain_status == "Pending"


def test_identity_repository_get_mail_from_domain_attributes_empty(
    mock_boto3_client_patch,
):
    identity_repo = AWSIdentityRepository()

    identity_mail_from_domain_attributes = (
        identity_repo.get_mail_from_domain_attributes(
            name="empty-mail-from-attributes.com"
        )
    )
    assert identity_mail_from_domain_attributes is None


def test_hosted_zone_repository_get(mock_boto3_client_patch):
    hosted_zone_repo = AWSHostedZoneRepository()
    hosted_zone = hosted_zone_repo.get("new-identity-present-in-route53.com")

    assert hosted_zone
    assert hosted_zone == "some-long-id"

    hosted_zone = hosted_zone_repo.get("unknown.com")
    assert hosted_zone is None


def test_hosted_zone_records_repository_add(mock_boto3_client_patch):
    record = HostedZoneRecord(
        "token-a._domainkey.us-east-1.my-identity.com",
        "CNAME",
        300,
        ["token-a.dkim.amazonses.com"],
    )

    hosted_zone_record_repo = AWSHostedZoneRecordsRepository()
    hosted_zone_record_repo.add(hosted_zone_id="some-long-id", record=record)

    # client is mocked
    hosted_zone_record_repo.client.change_resource_record_sets.assert_called()


def test_hosted_zone_records_repository_get(mock_boto3_client_patch):
    hosted_zone_record_repo = AWSHostedZoneRecordsRepository()
    record = HostedZoneRecord(
        "token-a._domainkey.my-identity.com",
        "CNAME",
        300,
        ["token-a.dkim.amazonses.com"],
    )

    records = hosted_zone_record_repo.get(hosted_zone_id="token-a-id")
    assert record in records

    records = hosted_zone_record_repo.get(hosted_zone_id="token-b-id")
    assert record not in records
