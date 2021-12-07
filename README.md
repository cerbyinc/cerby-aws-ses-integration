# Cerby AWS SES Integration tool

Tool to help you to setup AWS SES service on your AWS Account so you can use your custom domain with us.

## Running the tool

We encorage you to run this tool within a (CloudShell)[https://aws.amazon.com/cloudshell/] in your AWS Account. CloudShell already has all dependencies and libraries required to successfully run the this tool. 

1. Clone this repository
    ```shell
    git clone https://github.com/cerby/aws-ses-integration
    ```
1. Execute it
    ```
    python3 main.py <domain>
    ```

1. Accept or Deny the prompts asked for the tool.
    - Create Identity
    - Create DKIM records in the hosted zone.
    - Create MX record 

