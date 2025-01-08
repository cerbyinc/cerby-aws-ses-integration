import pytest

from ses_actions import SESActions


def test_configure_lifecycle(mock_boto3_client_patch):
    # case 1: a new AWS SES Identity, and domain is present in Route53
    domain = "new-identity-present-in-route53.com"

    ses_actions = SESActions(domain=domain)
    ses_actions.configure_sending_email()
    ses_actions.configure_receiving_email()
    ses_actions.configure_mail_from_domain()
    ses_actions.configure_email_receiving_rules()

    # test that records were created correctly.
    assert ses_actions.records_pending_to_create == []
    assert ses_actions.rules_failed_to_create == {}

    # case 2: an existing AWS SES identity, and domain is present in Route53

    domain = "existing-identity-present-in-route53.com"

    ses_actions = SESActions(domain=domain)
    ses_actions.configure_sending_email()
    ses_actions.configure_receiving_email()
    ses_actions.configure_mail_from_domain()
    ses_actions.configure_email_receiving_rules()

    # test that records were created correctly.
    assert ses_actions.records_pending_to_create == []
    assert ses_actions.rules_failed_to_create == {}

    # case 3: a new AWS SES identity, and domain is NOT present in Route53

    domain = "new-identity-not-present-in-route53.com"

    ses_actions = SESActions(domain=domain)
    ses_actions.configure_sending_email()
    ses_actions.configure_receiving_email()
    ses_actions.configure_mail_from_domain()
    ses_actions.configure_email_receiving_rules()

    assert ses_actions.records_pending_to_create
    assert len(ses_actions.records_pending_to_create) == 5
    assert ses_actions.rules_failed_to_create == {}

    # case 4: an existing AWS SES identity, and domain is NOT present in Route53

    domain = "existing-identity-not-present-in-route53.com"

    ses_actions = SESActions(domain=domain)
    ses_actions.configure_sending_email()
    ses_actions.configure_receiving_email()
    ses_actions.configure_mail_from_domain()
    ses_actions.configure_email_receiving_rules()

    assert ses_actions.records_pending_to_create
    assert len(ses_actions.records_pending_to_create) == 5
    assert ses_actions.rules_failed_to_create == {}


def test_mail_from_correct_record(mock_boto3_client_patch, mock_boto3_region_patch):
    domain = "new-identity-not-present-in-route53.com"

    ses_actions = SESActions(domain=domain)
    ses_actions.configure_mail_from_domain()
    records_to_create = ses_actions.records_pending_to_create

    records_values = [
        "10 feedback-smtp.us-east-1.amazonses.com",
        '"v=spf1 include:amazonses.com ~all"',
    ]
    assert len(records_to_create) == 2
    records_values_to_create = [
        value for record in records_to_create for value in record.values
    ]
    assert records_values_to_create == records_values


def test_configure_email_receiving_rules_access_denied(
    mock_boto3_client_patch, mock_boto3_region_patch
):
    domain = "accessdenied.com"

    ses_actions = SESActions(domain=domain)
    with pytest.raises(Exception):
        ses_actions.configure_email_receiving_rules()

    assert ses_actions.rules_failed_to_create
    assert len(ses_actions.rules_failed_to_create) == 1
    error = ses_actions.rules_failed_to_create["rule-set-for-cerby-accessdenied"]
    assert (
        error
        == "An error occurred (AccessDenied) when calling the SetActiveReceiptRule operation: User is not authorized to perform this action."
    )
