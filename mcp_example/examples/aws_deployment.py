"""
AWS Deployment Example

This script demonstrates the configuration and deployment steps for running
an MCP server on AWS infrastructure using:
1. AWS Lambda for serverless function execution
2. AWS API Gateway for HTTP endpoints
3. AWS CloudFront for content delivery
4. AWS DynamoDB for persistence
5. AWS CloudWatch for monitoring

Note: This is a demonstration script and does not actually deploy resources.
It shows the configuration structure and deployment options.
"""

import json
import os
from typing import Any, Dict, List

# Sample AWS configuration
AWS_REGION = "us-west-2"
LAMBDA_MEMORY = 512
LAMBDA_TIMEOUT = 30
API_GATEWAY_STAGE = "prod"
DYNAMODB_RCU = 5
DYNAMODB_WCU = 5
LOG_RETENTION_DAYS = 14


def generate_aws_lambda_config() -> Dict[str, Any]:
    """
    Generate AWS Lambda configuration for MCP server functions.
    
    Returns:
        Lambda configuration dictionary
    """
    print("=== AWS Lambda Configuration ===")
    
    # Sample Lambda configuration
    lambda_config = {
        "FunctionName": "mcp-server",
        "Runtime": "python3.9",
        "Handler": "mcp_example.server.lambda_handler.handler",
        "MemorySize": LAMBDA_MEMORY,
        "Timeout": LAMBDA_TIMEOUT,
        "Environment": {
            "Variables": {
                "API_KEYS": "test-key:test-user",
                "LOG_LEVEL": "INFO",
                "ENABLE_CACHING": "true",
                "CACHE_TTL": "300",
                "ENABLE_CORS": "true"
            }
        },
        "Tags": {
            "Project": "MCP-Example",
            "Environment": "Production"
        }
    }
    
    print(json.dumps(lambda_config, indent=2))
    return lambda_config


def generate_api_gateway_config() -> Dict[str, Any]:
    """
    Generate AWS API Gateway configuration for MCP server API.
    
    Returns:
        API Gateway configuration dictionary
    """
    print("\n=== AWS API Gateway Configuration ===")
    
    # Sample API Gateway configuration
    api_gateway_config = {
        "Name": "mcp-server-api",
        "Description": "API for Model Context Protocol server",
        "EndpointConfiguration": "REGIONAL",
        "Stage": API_GATEWAY_STAGE,
        "Routes": [
            {
                "Path": "/api/functions",
                "Method": "GET",
                "LambdaFunction": "mcp-server",
                "Authorization": "API_KEY"
            },
            {
                "Path": "/api/functions/{name}",
                "Method": "GET",
                "LambdaFunction": "mcp-server",
                "Authorization": "API_KEY"
            },
            {
                "Path": "/api/functions/call",
                "Method": "POST",
                "LambdaFunction": "mcp-server",
                "Authorization": "API_KEY"
            },
            {
                "Path": "/api/tools/call",
                "Method": "POST",
                "LambdaFunction": "mcp-server",
                "Authorization": "API_KEY"
            },
            {
                "Path": "/api/execute",
                "Method": "POST",
                "LambdaFunction": "mcp-server",
                "Authorization": "API_KEY"
            }
        ],
        "WebSocketRoutes": [
            {
                "Route": "$connect",
                "LambdaFunction": "mcp-websocket-connect"
            },
            {
                "Route": "$disconnect",
                "LambdaFunction": "mcp-websocket-disconnect"
            },
            {
                "Route": "function-stream",
                "LambdaFunction": "mcp-websocket-function-stream"
            },
            {
                "Route": "tool-stream",
                "LambdaFunction": "mcp-websocket-tool-stream"
            }
        ]
    }
    
    print(json.dumps(api_gateway_config, indent=2))
    return api_gateway_config


def generate_dynamodb_config() -> Dict[str, Any]:
    """
    Generate AWS DynamoDB configuration for MCP server data persistence.
    
    Returns:
        DynamoDB configuration dictionary
    """
    print("\n=== AWS DynamoDB Configuration ===")
    
    # Sample DynamoDB configuration
    dynamodb_config = {
        "TableName": "mcp-tool-results",
        "AttributeDefinitions": [
            {
                "AttributeName": "tool_name",
                "AttributeType": "S"
            },
            {
                "AttributeName": "params_hash",
                "AttributeType": "S"
            },
            {
                "AttributeName": "created_at",
                "AttributeType": "N"
            }
        ],
        "KeySchema": [
            {
                "AttributeName": "tool_name",
                "KeyType": "HASH"
            },
            {
                "AttributeName": "params_hash",
                "KeyType": "RANGE"
            }
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "CreatedAtIndex",
                "KeySchema": [
                    {
                        "AttributeName": "created_at",
                        "KeyType": "HASH"
                    }
                ],
                "Projection": {
                    "ProjectionType": "ALL"
                },
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": DYNAMODB_RCU,
                    "WriteCapacityUnits": DYNAMODB_WCU
                }
            }
        ],
        "ProvisionedThroughput": {
            "ReadCapacityUnits": DYNAMODB_RCU,
            "WriteCapacityUnits": DYNAMODB_WCU
        },
        "TimeToLiveSpecification": {
            "AttributeName": "expires_at",
            "Enabled": True
        }
    }
    
    print(json.dumps(dynamodb_config, indent=2))
    return dynamodb_config


def generate_cloudwatch_config() -> Dict[str, Any]:
    """
    Generate AWS CloudWatch configuration for MCP server monitoring.
    
    Returns:
        CloudWatch configuration dictionary
    """
    print("\n=== AWS CloudWatch Configuration ===")
    
    # Sample CloudWatch configuration
    cloudwatch_config = {
        "LogGroups": [
            {
                "LogGroupName": "/aws/lambda/mcp-server",
                "RetentionInDays": LOG_RETENTION_DAYS
            },
            {
                "LogGroupName": "/aws/lambda/mcp-websocket-connect",
                "RetentionInDays": LOG_RETENTION_DAYS
            },
            {
                "LogGroupName": "/aws/lambda/mcp-websocket-disconnect",
                "RetentionInDays": LOG_RETENTION_DAYS
            },
            {
                "LogGroupName": "/aws/lambda/mcp-websocket-function-stream",
                "RetentionInDays": LOG_RETENTION_DAYS
            },
            {
                "LogGroupName": "/aws/lambda/mcp-websocket-tool-stream",
                "RetentionInDays": LOG_RETENTION_DAYS
            }
        ],
        "Alarms": [
            {
                "AlarmName": "mcp-server-errors",
                "MetricName": "Errors",
                "Namespace": "AWS/Lambda",
                "Dimensions": [
                    {
                        "Name": "FunctionName",
                        "Value": "mcp-server"
                    }
                ],
                "Period": 300,
                "EvaluationPeriods": 1,
                "Threshold": 5,
                "ComparisonOperator": "GreaterThanThreshold"
            },
            {
                "AlarmName": "mcp-server-throttles",
                "MetricName": "Throttles",
                "Namespace": "AWS/Lambda",
                "Dimensions": [
                    {
                        "Name": "FunctionName",
                        "Value": "mcp-server"
                    }
                ],
                "Period": 300,
                "EvaluationPeriods": 1,
                "Threshold": 5,
                "ComparisonOperator": "GreaterThanThreshold"
            }
        ],
        "Dashboards": [
            {
                "DashboardName": "MCP-Server-Dashboard",
                "Widgets": [
                    "Lambda Invocations",
                    "Lambda Errors",
                    "Lambda Duration",
                    "API Gateway Requests",
                    "API Gateway Latency",
                    "DynamoDB Read Capacity",
                    "DynamoDB Write Capacity"
                ]
            }
        ]
    }
    
    print(json.dumps(cloudwatch_config, indent=2))
    return cloudwatch_config


def generate_deployment_steps() -> List[str]:
    """
    Generate a list of deployment steps for MCP server on AWS.
    
    Returns:
        List of deployment steps
    """
    print("\n=== AWS Deployment Steps ===")
    
    deployment_steps = [
        "1. Package MCP server code",
        "   - pip install -r requirements.txt -t ./package",
        "   - cp -r mcp_example ./package/",
        "   - cd package && zip -r ../mcp-server.zip .",
        
        "2. Create AWS DynamoDB table",
        "   - aws dynamodb create-table --cli-input-json file://dynamodb-config.json",
        
        "3. Create AWS Lambda function",
        "   - aws lambda create-function --cli-input-json file://lambda-config.json --zip-file fileb://mcp-server.zip",
        
        "4. Create AWS API Gateway",
        "   - aws apigateway create-rest-api --name mcp-server-api",
        "   - aws apigateway create-resource --rest-api-id <api-id> --parent-id <parent-id> --path-part api",
        "   - ... (additional resource and method creation steps)",
        
        "5. Create WebSocket API for streaming",
        "   - aws apigatewayv2 create-api --name mcp-websocket-api --protocol-type WEBSOCKET --route-selection-expression '$request.body.action'",
        "   - ... (WebSocket route creation steps)",
        
        "6. Deploy API Gateway",
        "   - aws apigateway create-deployment --rest-api-id <api-id> --stage-name prod",
        
        "7. Set up CloudWatch monitoring",
        "   - aws cloudwatch put-metric-alarm --cli-input-json file://cloudwatch-alarms.json",
        
        "8. Create CloudWatch dashboard",
        "   - aws cloudwatch put-dashboard --dashboard-name MCP-Server-Dashboard --dashboard-body file://dashboard.json",
        
        "9. Test deployment",
        "   - curl -X GET https://<api-id>.execute-api.<region>.amazonaws.com/prod/api/functions -H 'X-API-Key: test-key'",
        
        "10. Set up CI/CD for future updates",
        "    - Create GitHub Actions workflow or AWS CodePipeline"
    ]
    
    for step in deployment_steps:
        print(step)
    
    return deployment_steps


def main() -> None:
    """Main function to generate AWS deployment configurations."""
    print("Generating AWS deployment configurations for MCP server\n")
    
    # Generate each configuration component
    lambda_config = generate_aws_lambda_config()
    api_gateway_config = generate_api_gateway_config()
    dynamodb_config = generate_dynamodb_config()
    cloudwatch_config = generate_cloudwatch_config()
    
    # Generate deployment steps
    deployment_steps = generate_deployment_steps()
    
    # Create a full deployment package
    full_config = {
        "Region": AWS_REGION,
        "Lambda": lambda_config,
        "ApiGateway": api_gateway_config,
        "DynamoDB": dynamodb_config,
        "CloudWatch": cloudwatch_config,
        "DeploymentSteps": deployment_steps
    }
    
    # Save to a JSON file
    output_dir = "deployment"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, "aws-deployment-config.json"), "w") as f:
        json.dump(full_config, f, indent=2)
    
    print("\nFull AWS deployment configuration saved to deployment/aws-deployment-config.json")
    print("\nNOTE: This is a demonstration script. To perform an actual deployment,")
    print("you would need to customize these configurations and use deployment tools")
    print("like AWS CloudFormation, Terraform, AWS CDK, or the AWS CLI.")


if __name__ == "__main__":
    main() 