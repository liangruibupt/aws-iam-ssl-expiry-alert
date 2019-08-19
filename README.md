# ssl-expiry-alert
This is a sample lambda function to check SSL Certification expire and send SNS alert.
Below is a brief explanation of what we have generated for you:

```
README.md                   <-- This instructions file
package.json                <-- package file
ssl-expiry-alert.py         <-- Source code for a lambda function
serverless.yml              <-- Serverless Framework Template
test-data.json              <-- Sample Testing data
```
## Requirements

* AWS CLI already installed and create a profile name cn-north-1, if you using other profile name, you need update the sls command to using your own one.
* [Python 3 installed](https://www.python.org/downloads/)
* [Docker installed](https://www.docker.com/community-edition)
* [Serverless Framework has been installed](https://serverless.com/framework/docs/providers/aws/)
* Create your own SNS topic to receive the email alarm and update the topic ARN in serverless.yml SNS_TOPIC_ARN environment variable for lambda

## Setup process

### Deploy Lambda Function
```
sls create --template aws-python3 --name ssl-expiry-alert --path ssl-expiry-alert --aws-profile cn-north-1 --region cn-north-1
sls plugin install -n serverless-python-requirements
# If your sls version has not been include the merge https://github.com/serverless/serverless/pull/6127, then you need run
npm i serverless-plugin-aws-cn-principal -D
# To fix the China Region Serverless Framework usage issue
# https://forum.serverless.com/t/using-serverless-framework-for-deployment-in-china-region/3468 . But the fix has been merged https://github.com/serverless/serverless/pull/6127. 
# If you upgrade the sls to latest version, then you can just uninstall the plugin by
npm uninstall serverless-plugin-aws-cn-principal -D

sls deploy -v --aws-profile cn-north-1 --region cn-north-1
```

### Resource created

* Lambda Function
* DynamoDB table ${self:provider.stage}-SSLCertInfo
* CloudWatch Event rule to trigger Lambda Function
* SNS alert when certification will expired within check time

If you want to manually trigger the Lambda Function you need define the event sample as
```
{
  "Items": [
    {
      "hostname": "aws.amazon.com",
      "buffer_days": 10
    },
    {
      "hostname": "github.com",
      "buffer_days": 10
    }
  ]
}

The hostname is check url which SSL certification attached
The buffer_days defined the alert condition: when expiration time <= buffer_days, alert sent
```

You can also use DynamoDB table ${self:provider.stage}-SSLCertInfo to store your check items
```
{
      "hostname": "amazonaws-china.com",
      "buffer_days": 10
}
{
      "hostname": "www.amazonaws.cn",
      "buffer_days": 10
}
```

### Invoke Function
```
sls invoke -f ssl-expiry-alert -l --aws-profile cn-north-1 --region cn-north-1 --path test-data.json
```

Sample output:
```
{
    "statusCode": 200,
    "body": "[\"aws.amazon.com everything is fine\", \"github.com everything is fine\", \"The amazonaws-china.com SSL certificate expires alert! Remaining 124 days, 4:17:42.737673 \", \"www.amazonaws.cn everything is fine\"]"
}
--------------------------------------------------------------------
START RequestId: dab9e864-c3f5-4a92-970f-34c502eb574a Version: $LATEST
Input events: {'Items': [{'hostname': 'aws.amazon.com', 'buffer_days': 10}, {'hostname': 'github.com', 'buffer_days': 10}]}
SSL cert for aws.amazon.com expires at 2019-12-18T12:00:00
SSL cert remaining 124 days, 4:17:44.709106 before expires
SSL cert for github.com expires at 2020-06-03T12:00:00
SSL cert remaining 292 days, 4:17:44.258118 before expires
DynamoDB fetched item hostname: amazonaws-china.com ,buffer_days: 300
SSL cert for amazonaws-china.com expires at 2019-12-18T12:00:00
SSL cert remaining 124 days, 4:17:42.737673 before expires
DynamoDB fetched item hostname: www.amazonaws.cn ,buffer_days: 300
SSL cert for www.amazonaws.cn expires at 2020-07-28T12:00:00
SSL cert remaining 347 days, 4:17:42.158686 before expires
END RequestId: dab9e864-c3f5-4a92-970f-34c502eb574a
REPORT RequestId: dab9e864-c3f5-4a92-970f-34c502eb574a  Duration: 3109.88 ms    Billed Duration: 3200 ms    Memory Size: 128 MB Max Memory Used: 35 MB
```

Sample Alert:
```
The SSL certificate expires alert!

The amazonaws-china.com SSL certificate expires alert! Remaining 124 days, 4:21:33.147710
```

To Check the logs for debug
```
sls logs -f ssl-expiry-alert -t --aws-profile cn-north-1 --region cn-north-1
```

### Update Function
```
sls deploy function -f ssl-expiry-alert -v --aws-profile cn-north-1 --region cn-north-1
```

# Cleanup
```
sls remove --aws-profile cn-north-1 --region cn-north-1
```

# reference
[serverless framework guide](https://serverless.com/blog/flask-python-rest-api-serverless-lambda-dynamodb/#using-the-quick-start-template)
[serverless python packaging](https://serverless.com/blog/serverless-python-packaging/)