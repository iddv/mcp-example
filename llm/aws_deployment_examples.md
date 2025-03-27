# AWS Deployment Examples

This document provides concrete examples for deploying the MCP server to AWS using infrastructure as code (IaC) solutions.

## Overview

We provide two approaches for deploying the MCP server to AWS:
1. AWS CloudFormation - A template-based approach
2. AWS Cloud Development Kit (CDK) - A code-based approach

Both approaches deploy the same architecture:
- AWS Lambda for serverless function execution
- Amazon API Gateway for HTTP and WebSocket endpoints
- Amazon DynamoDB for result caching and session state
- Amazon CloudWatch for monitoring and logging

## Prerequisites

- AWS account with appropriate permissions
- AWS CLI installed and configured
- For CDK: Node.js and npm installed

## AWS CloudFormation Example

### CloudFormation Template

Create a file named `mcp-server-cloudformation.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'MCP Server CloudFormation Stack'

Parameters:
  Environment:
    Type: String
    Default: 'dev'
    AllowedValues:
      - 'dev'
      - 'staging'
      - 'prod'
    Description: 'Deployment environment'
  
  ApiKeyName:
    Type: String
    Default: 'MCPApiKey'
    Description: 'Name of the API key for API Gateway'

Resources:
  # DynamoDB Table for caching tool results
  MCPToolResultsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub 'mcp-tool-results-${Environment}'
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: tool_name
          AttributeType: S
        - AttributeName: params_hash
          AttributeType: S
        - AttributeName: created_at
          AttributeType: N
      KeySchema:
        - AttributeName: tool_name
          KeyType: HASH
        - AttributeName: params_hash
          KeyType: RANGE
      GlobalSecondaryIndexes:
        - IndexName: CreatedAtIndex
          KeySchema:
            - AttributeName: created_at
              KeyType: HASH
          Projection:
            ProjectionType: ALL
      TimeToLiveSpecification:
        AttributeName: expires_at
        Enabled: true

  # Lambda execution role
  MCPLambdaRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        - PolicyName: DynamoDBAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - dynamodb:GetItem
                  - dynamodb:PutItem
                  - dynamodb:Query
                  - dynamodb:DeleteItem
                Resource: !GetAtt MCPToolResultsTable.Arn

  # Lambda function
  MCPServerFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: !Sub 'mcp-server-${Environment}'
      Runtime: python3.9
      Handler: mcp_example.server.lambda_handler.handler
      Role: !GetAtt MCPLambdaRole.Arn
      MemorySize: 512
      Timeout: 30
      Environment:
        Variables:
          ENVIRONMENT: !Ref Environment
          DYNAMODB_TABLE: !Ref MCPToolResultsTable
          ENABLE_CACHING: 'true'
          CACHE_TTL: '300'
          LOG_LEVEL: 'INFO'
      Code:
        S3Bucket: !Sub 'mcp-deployment-${AWS::AccountId}'
        S3Key: 'mcp-server-package.zip'
      Tags:
        - Key: Environment
          Value: !Ref Environment

  # REST API Gateway
  MCPRestApi:
    Type: AWS::ApiGateway::RestApi
    Properties:
      Name: !Sub 'mcp-server-api-${Environment}'
      Description: 'API for Model Context Protocol server'
      EndpointConfiguration:
        Types:
          - REGIONAL

  # API Gateway Resources and Methods - simplified example
  MCPFunctionsResource:
    Type: AWS::ApiGateway::Resource
    Properties:
      RestApiId: !Ref MCPRestApi
      ParentId: !GetAtt MCPRestApi.RootResourceId
      PathPart: 'functions'

  # GET method to list functions
  MCPListFunctionsMethod:
    Type: AWS::ApiGateway::Method
    Properties:
      RestApiId: !Ref MCPRestApi
      ResourceId: !Ref MCPFunctionsResource
      HttpMethod: GET
      AuthorizationType: API_KEY
      ApiKeyRequired: true
      Integration:
        Type: AWS_PROXY
        IntegrationHttpMethod: POST
        Uri: !Sub 'arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${MCPServerFunction.Arn}/invocations'

  # API Gateway Deployment
  MCPApiDeployment:
    Type: AWS::ApiGateway::Deployment
    DependsOn:
      - MCPListFunctionsMethod
    Properties:
      RestApiId: !Ref MCPRestApi
      StageName: !Ref Environment

  # API Key
  MCPApiKey:
    Type: AWS::ApiGateway::ApiKey
    DependsOn:
      - MCPApiDeployment
    Properties:
      Name: !Ref ApiKeyName
      Enabled: true
      StageKeys:
        - RestApiId: !Ref MCPRestApi
          StageName: !Ref Environment

  # Usage Plan
  MCPUsagePlan:
    Type: AWS::ApiGateway::UsagePlan
    DependsOn:
      - MCPApiDeployment
    Properties:
      UsagePlanName: !Sub 'mcp-usage-plan-${Environment}'
      Description: 'Usage plan for MCP Server API'
      ApiStages:
        - ApiId: !Ref MCPRestApi
          Stage: !Ref Environment
      Throttle:
        RateLimit: 10
        BurstLimit: 20

  # API Key to Usage Plan mapping
  MCPUsagePlanKey:
    Type: AWS::ApiGateway::UsagePlanKey
    Properties:
      KeyId: !Ref MCPApiKey
      KeyType: API_KEY
      UsagePlanId: !Ref MCPUsagePlan

  # Lambda Permission
  MCPLambdaPermission:
    Type: AWS::Lambda::Permission
    Properties:
      Action: lambda:InvokeFunction
      FunctionName: !Ref MCPServerFunction
      Principal: apigateway.amazonaws.com
      SourceArn: !Sub 'arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${MCPRestApi}/*'

Outputs:
  APIEndpoint:
    Description: API Gateway endpoint URL
    Value: !Sub 'https://${MCPRestApi}.execute-api.${AWS::Region}.amazonaws.com/${Environment}/'
  
  ApiKeyId:
    Description: API Key ID
    Value: !Ref MCPApiKey
```

### Deployment Steps

1. Package your Lambda deployment:

```bash
# Create zip package
pip install -r requirements.txt -t ./package
cp -r ./mcp_example ./package/
cd package
zip -r ../mcp-server-package.zip .
cd ..
```

2. Create S3 bucket for deployment:

```bash
aws s3 mb s3://mcp-deployment-$(aws sts get-caller-identity --query 'Account' --output text)
aws s3 cp mcp-server-package.zip s3://mcp-deployment-$(aws sts get-caller-identity --query 'Account' --output text)/
```

3. Deploy CloudFormation stack:

```bash
aws cloudformation deploy \
  --template-file mcp-server-cloudformation.yaml \
  --stack-name mcp-server-stack \
  --parameter-overrides Environment=dev \
  --capabilities CAPABILITY_IAM
```

4. Get API Key for the deployment:

```bash
aws apigateway get-api-key \
  --api-key $(aws cloudformation describe-stacks --stack-name mcp-server-stack --query "Stacks[0].Outputs[?OutputKey=='ApiKeyId'].OutputValue" --output text) \
  --include-value
```

## AWS CDK Example

AWS CDK provides a code-based approach to defining cloud infrastructure. First, install the CDK:

```bash
npm install -g aws-cdk
```

### CDK Project Setup

1. Create a new CDK project:

```bash
mkdir mcp-cdk-deployment && cd mcp-cdk-deployment
cdk init app --language python
```

2. Install required packages:

```bash
python -m pip install -r requirements.txt
```

3. Replace `app.py` with:

```python
#!/usr/bin/env python3
import os
from aws_cdk import (
    App,
    Stack,
    Duration,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_iam as iam,
)
from constructs import Construct


class MCPServerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, environment: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB Table for result caching
        tool_results_table = dynamodb.Table(
            self, "MCPToolResultsTable",
            table_name=f"mcp-tool-results-{environment}",
            partition_key=dynamodb.Attribute(
                name="tool_name",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="params_hash",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY if environment != "prod" else RemovalPolicy.RETAIN,
            time_to_live_attribute="expires_at",
        )

        # Add GSI for time-based queries
        tool_results_table.add_global_secondary_index(
            index_name="CreatedAtIndex",
            partition_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.NUMBER
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )

        # Lambda Function
        mcp_function = lambda_.Function(
            self, "MCPServerFunction",
            function_name=f"mcp-server-{environment}",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="mcp_example.server.lambda_handler.handler",
            code=lambda_.Code.from_asset("../lambda-package"),
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "ENVIRONMENT": environment,
                "DYNAMODB_TABLE": tool_results_table.table_name,
                "ENABLE_CACHING": "true",
                "CACHE_TTL": "300",
                "LOG_LEVEL": "INFO",
            }
        )

        # Grant DynamoDB permissions to Lambda
        tool_results_table.grant_read_write_data(mcp_function)

        # API Gateway
        api = apigateway.RestApi(
            self, "MCPApi",
            rest_api_name=f"mcp-server-api-{environment}",
            description="API for Model Context Protocol server",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS
            )
        )

        # Add API Key
        api_key = api.add_api_key(
            "MCPApiKey",
            api_key_name=f"mcp-api-key-{environment}"
        )

        # Create Usage Plan
        plan = api.add_usage_plan(
            "MCPUsagePlan",
            name=f"mcp-usage-plan-{environment}",
            throttle=apigateway.ThrottleSettings(
                rate_limit=10,
                burst_limit=20
            )
        )
        plan.add_api_key(api_key)
        plan.add_api_stage(stage=api.deployment_stage)

        # Functions resource
        functions_resource = api.root.add_resource("functions")
        functions_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(mcp_function),
            api_key_required=True
        )

        # Call resource
        call_resource = functions_resource.add_resource("call")
        call_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(mcp_function),
            api_key_required=True
        )

        # Tools resource
        tools_resource = api.root.add_resource("tools")
        tools_call_resource = tools_resource.add_resource("call")
        tools_call_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(mcp_function),
            api_key_required=True
        )

        # Execute resource
        execute_resource = api.root.add_resource("execute")
        execute_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(mcp_function),
            api_key_required=True
        )


app = App()
MCPServerStack(app, "MCPServerStack", environment="dev")
app.synth()
```

### Deployment Steps

1. Package your Lambda deployment:

```bash
# Create package directory
mkdir -p lambda-package
pip install -r ../requirements.txt -t ./lambda-package
cp -r ../mcp_example ./lambda-package/
```

2. Deploy using CDK:

```bash
cdk bootstrap  # Only needed the first time using CDK
cdk deploy
```

3. View outputs to get API endpoint:

```bash
cdk deploy --outputs-file outputs.json
cat outputs.json
```

4. Get the API key:

```bash
aws apigateway get-api-keys --name-query "mcp-api-key-dev" --include-values
```

## Serverless Framework Example

[Serverless Framework](https://www.serverless.com/) is another popular option for deploying serverless applications.

Create a `serverless.yml` file:

```yaml
service: mcp-server

provider:
  name: aws
  runtime: python3.9
  stage: ${opt:stage, 'dev'}
  region: ${opt:region, 'us-west-2'}
  environment:
    ENVIRONMENT: ${self:provider.stage}
    DYNAMODB_TABLE: ${self:service}-tool-results-${self:provider.stage}
    ENABLE_CACHING: 'true'
    CACHE_TTL: '300'
    LOG_LEVEL: 'INFO'
  iam:
    role:
      statements:
        - Effect: Allow
          Action:
            - dynamodb:Query
            - dynamodb:GetItem
            - dynamodb:PutItem
            - dynamodb:DeleteItem
          Resource:
            - "arn:aws:dynamodb:${self:provider.region}:*:table/${self:provider.environment.DYNAMODB_TABLE}"
  apiGateway:
    apiKeys:
      - name: mcp-api-key-${self:provider.stage}
        description: "API key for MCP Server"

functions:
  server:
    handler: mcp_example.server.lambda_handler.handler
    events:
      - http:
          path: /functions
          method: get
          private: true
      - http:
          path: /functions/{name}
          method: get
          private: true
      - http:
          path: /functions/call
          method: post
          private: true
      - http:
          path: /tools/call
          method: post
          private: true
      - http:
          path: /execute
          method: post
          private: true

resources:
  Resources:
    ToolResultsTable:
      Type: AWS::DynamoDB::Table
      Properties:
        TableName: ${self:provider.environment.DYNAMODB_TABLE}
        BillingMode: PAY_PER_REQUEST
        AttributeDefinitions:
          - AttributeName: tool_name
            AttributeType: S
          - AttributeName: params_hash
            AttributeType: S
          - AttributeName: created_at
            AttributeType: N
        KeySchema:
          - AttributeName: tool_name
            KeyType: HASH
          - AttributeName: params_hash
            KeyType: RANGE
        GlobalSecondaryIndexes:
          - IndexName: CreatedAtIndex
            KeySchema:
              - AttributeName: created_at
                KeyType: HASH
            Projection:
              ProjectionType: ALL
        TimeToLiveSpecification:
          AttributeName: expires_at
          Enabled: true
```

### Deployment Steps

1. Install Serverless Framework:

```bash
npm install -g serverless
```

2. Deploy:

```bash
serverless deploy --stage dev
```

3. Get information about the service:

```bash
serverless info --stage dev
```

## Automated Deployment with GitHub Actions

Create a GitHub Actions workflow file at `.github/workflows/deploy.yml`:

```yaml
name: Deploy MCP Server

on:
  push:
    branches:
      - main
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        default: 'dev'
        type: choice
        options:
          - dev
          - staging
          - prod

jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      ENVIRONMENT: ${{ github.event.inputs.environment || 'dev' }}
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install aws-cdk-lib
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2
      
      - name: Package Lambda
        run: |
          mkdir -p lambda-package
          pip install -r requirements.txt -t ./lambda-package
          cp -r ./mcp_example ./lambda-package/
      
      - name: Deploy with CDK
        run: |
          cd cdk
          pip install -r requirements.txt
          cdk deploy MCPServerStack --require-approval never --parameters environment=$ENVIRONMENT
```

## Summary

These examples provide several options for deploying the MCP server to AWS:

1. **CloudFormation** - Template-based approach
2. **CDK** - Code-based approach using Python
3. **Serverless Framework** - Simplified configuration
4. **GitHub Actions** - Automated deployments

Choose the approach that best fits your team's workflow and expertise.

## References

- [AWS CloudFormation Documentation](https://docs.aws.amazon.com/cloudformation/)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [Serverless Framework Documentation](https://www.serverless.com/framework/docs/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/) 