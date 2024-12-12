from ses_actions import SESActions


def test_configure_lifecycle(mock_boto3_client_patch):
    # case 1: a new AWS SES Identity, and domain is present in Route53
    domain = "new-identity-present-in-route53.com"

    ses_actions = SESActions(domain=domain)
    ses_actions.configure_sending_email()
    ses_actions.configure_receiving_email()
    ses_actions.configure_mail_from_domain()

    # test that records were created correctly.
    assert ses_actions.records_pending_to_create == []

    # case 2: an existing AWS SES identity, and domain is present in Route53

    domain = "existing-identity-present-in-route53.com"

    ses_actions = SESActions(domain=domain)
    ses_actions.configure_sending_email()
    ses_actions.configure_receiving_email()
    ses_actions.configure_mail_from_domain()

    # test that records were created correctly.
    assert ses_actions.records_pending_to_create == []

    # case 3: a new AWS SES identity, and domain is NOT present in Route53

    domain = "new-identity-not-present-in-route53.com"

    ses_actions = SESActions(domain=domain)
    ses_actions.configure_sending_email()
    ses_actions.configure_receiving_email()
    ses_actions.configure_mail_from_domain()

    assert ses_actions.records_pending_to_create
    assert len(ses_actions.records_pending_to_create) == 5

    # case 4: an existing AWS SES identity, and domain is NOT present in Route53

    domain = "existing-identity-not-present-in-route53.com"

    ses_actions = SESActions(domain=domain)
    ses_actions.configure_sending_email()
    ses_actions.configure_receiving_email()
    ses_actions.configure_mail_from_domain()

    assert ses_actions.records_pending_to_create
    assert len(ses_actions.records_pending_to_create) == 5


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
