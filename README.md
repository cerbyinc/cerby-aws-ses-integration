# Cerby AWS SES Integration tool

A Tool to help you to setup AWS SES service on your AWS Account so you can use your custom domain with us.

## Running the tool

We encorage you to run this tool within a [CloudShell](https://aws.amazon.com/cloudshell/) in your AWS Account. CloudShell already has all dependencies and libraries required to successfully run the this tool.

1. Clone this repository
    ```shell
    git clone https://github.com/cerbyinc/cerby-aws-ses-integration.git && cd cerby-aws-ses-integration
    ```
1. Execute it
    ```
    python3 main.py <domain> --workspace <your-workspace-name>
    ```

1. Tool will proceed to create the following resources:
    - Create Identity
    - Create DKIM records in the hosted zone.
    - Create MAIL From using `bounce.${domain}`
    - Create MX record
    - Create RuleSet, and Rule to deliver arriving email to Cerby (you need to add the --workspace flag to create these resources)


Tool will try to to add the DNS records to your Route53, if a hosted zone with the specified domain is not found, we still output the records so you can add [DKIM](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/send-email-authentication-dkim-easy-setup-domain.html) and [MX](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/receiving-email-mx-record.html) it to your DNS provider.
