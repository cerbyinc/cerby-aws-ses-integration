from unittest.mock import MagicMock, PropertyMock, patch

import boto3
import pytest
from botocore.exceptions import ClientError


def mock_boto3_client(service_name):
    mock_client = MagicMock()

    if service_name == "ses":

        def get_identity_dkim_attributes(Identities):
            dkim_attributes_map = {
                "existing-identity-not-present-in-route53.com": {
                    "DkimTokens": ["token-a", "token-b"],
                    "DkimVerificationStatus": "Pending",
                },
                "existing-identity-present-in-route53.com": {
                    "DkimTokens": ["token-a", "token-b"],
                    "DkimVerificationStatus": "Pending",
                },
            }

            if any(
                identity in Identities
                for identity in [
                    "new-identity-present-in-route53.com",
                    "new-identity-not-present-in-route53.com",
                ]
            ):
                return {"DkimAttributes": {}}

            for identity, dkim_attributes in dkim_attributes_map.items():
                if identity in Identities:
                    return {"DkimAttributes": {identity: dkim_attributes}}

            return {"DkimAttributes": {}}

        def verify_domain_dkim(Domain):
            return {"DkimTokens": ["token-a", "token-b"]}

        def get_identity_mail_from_domain_attributes(Identities):
            identity = Identities[0]
            if identity == "empty-mail-from-attributes.com":
                return {
                    "MailFromDomainAttributes": {
                        identity: {
                            "BehaviorOnMXFailure": "UseDefaultValue",
                        }
                    }
                }
            return {
                "MailFromDomainAttributes": {
                    identity: {
                        "MailFromDomain": f"bounce.{identity}",
                        "MailFromDomainStatus": "Pending",
                        "BehaviorOnMXFailure": "UseDefaultValue",
                    }
                }
            }

        def create_receipt_rule_set(RuleSetName):
            if RuleSetName == "rule-set-for-cerby-accessdenied":
                raise ClientError(
                    {
                        "Error": {
                            "Code": "AccessDenied",
                            "Message": "User is not authorized to perform this action.",
                        }
                    },
                    "SetActiveReceiptRule",
                )
            return {"RuleSetName": RuleSetName}

        def set_active_receipt_rule_set(RuleSetName):
            if RuleSetName == "rule-set-for-cerby-accessdenied":
                raise ClientError(
                    {
                        "Error": {
                            "Code": "AccessDenied",
                            "Message": "User is not authorized to perform this action.",
                        }
                    },
                    "SetActiveReceiptRule",
                )
            return {"RuleSetName": RuleSetName}

        def create_receipt_rule(RuleSetName, Rule):
            if RuleSetName == "rule-set-for-cerby-accessdenied":
                raise ClientError(
                    {
                        "Error": {
                            "Code": "AccessDenied",
                            "Message": "User is not authorized to perform this action.",
                        }
                    },
                    "SetActiveReceiptRule",
                )
            return {"Rule": Rule}

        mock_client.get_identity_dkim_attributes.side_effect = (
            get_identity_dkim_attributes
        )
        mock_client.verify_domain_dkim.side_effect = verify_domain_dkim
        mock_client.get_identity_mail_from_domain_attributes.side_effect = (
            get_identity_mail_from_domain_attributes
        )
        mock_client.set_identity_mail_from_domain = MagicMock()
        mock_client.create_receipt_rule_set.side_effect = create_receipt_rule_set
        mock_client.set_active_receipt_rule_set.side_effect = (
            set_active_receipt_rule_set
        )
        mock_client.create_receipt_rule.side_effect = create_receipt_rule

    elif service_name == "route53":

        def list_hosted_zones_by_name(DNSName):
            hosted_zone_map = {
                "new-identity-present-in-route53.com": {
                    "HostedZones": [
                        {
                            "Name": "new-identity-present-in-route53.com",
                            "Id": "some-long-id",
                        }
                    ]
                },
                "existing-identity-present-in-route53.com": {
                    "HostedZones": [
                        {
                            "Name": "existing-identity-present-in-route53.com",
                            "Id": "some-long-id",
                        }
                    ]
                },
            }

            if DNSName in hosted_zone_map:
                return hosted_zone_map.get(DNSName)

            return {"HostedZones": []}

        def list_resource_record_sets(HostedZoneId):
            if HostedZoneId == "token-a-id":
                return {
                    "ResourceRecordSets": [
                        {
                            "Name": "token-a._domainkey.my-identity.com",
                            "Type": "CNAME",
                            "TTL": 300,
                            "ResourceRecords": [
                                {"Value": "token-a.dkim.amazonses.com"}
                            ],
                        }
                    ]
                }
            if HostedZoneId == "token-b-id":
                return {
                    "ResourceRecordSets": [
                        {
                            "Name": "token-b._domainkey.my-identity.com",
                            "Type": "CNAME",
                            "TTL": 300,
                            "ResourceRecords": [
                                {"Value": "token-b.dkim.amazonses.com"}
                            ],
                        }
                    ]
                }
            return {"ResourceRecordSets": []}

        mock_client.list_hosted_zones_by_name.side_effect = list_hosted_zones_by_name
        mock_client.list_resource_record_sets.side_effect = list_resource_record_sets
        mock_client.change_resource_records_sets = MagicMock()
    return mock_client


@pytest.fixture
def mock_boto3_client_patch():
    with patch("boto3.session.Session.client") as mock_client_method:
        mock_client_method.side_effect = mock_boto3_client
        yield mock_client_method


@pytest.fixture
def mock_boto3_region_patch():
    with patch.object(
        boto3.session.Session, "region_name", new_callable=PropertyMock
    ) as mock_region_field:
        mock_region_field.return_value = "us-east-1"
        yield mock_region_field
