import socket
import ssl
import datetime
import json
import os
# import fileinput
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

#Create an SNS client
sns_client = boto3.client('sns', region_name='cn-north-1')
dynamodb_client = boto3.client('dynamodb', region_name='cn-north-1')
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
DDB_TABLE_NAME = os.environ['DYNAMODB_TABLE']

def lambda_handler(event, context):
    return_str = []
    print ('Input events: {0} '.format(event))
    for item in event['Items']:
        hostname = item['hostname']
        buffer_days = item['buffer_days']
        result = ssl_expires_in(hostname,buffer_days)
        return_str.append(result)

    # ddb
    try:
        response = dynamodb_client.describe_table(TableName=DDB_TABLE_NAME)
    except dynamodb_client.exceptions.ResourceNotFoundException:
        pass
    else:
        try:
            response = dynamodb_client.scan(
                TableName=DDB_TABLE_NAME
            )
            #print(json.dumps(response['Items'], indent=4))
            for item in response['Items']:
                hostname = item['hostname']['S']
                buffer_days = item['buffer_days']['N']
                print ('DynamoDB fetched item hostname: {0} ,buffer_days: {1}'.format(hostname, buffer_days))
                result = ssl_expires_in(hostname,int(buffer_days))
                return_str.append(result)
        except ClientError as e:
            print(e)
            return {
                'statusCode': 500,
                'body': 'ddb get_item failed: ' + e.response['Error']['Message']
            }

    return {
        'statusCode': 200,
        'body': json.dumps(return_str)
    }

def ssl_expiry_datetime(hostname):
    ssl_date_fmt = r'%b %d %H:%M:%S %Y %Z'

    context = ssl.create_default_context()
    conn = context.wrap_socket(
        socket.socket(socket.AF_INET),
        server_hostname=hostname,
    )
    # 3 second timeout
    conn.settimeout(3.0)

    conn.connect((hostname, 443))
    ssl_info = conn.getpeercert()
    # parse the string from the certificate into a Python datetime object
    return datetime.datetime.strptime(ssl_info['notAfter'], ssl_date_fmt)

def ssl_valid_time_remaining(hostname):
    """Get the number of days left in a cert's lifetime."""
    expires = ssl_expiry_datetime(hostname)
    print ('SSL cert for {0} expires at {1}'.format(hostname, expires.isoformat()))
    remaining = expires - datetime.datetime.utcnow()
    print ('SSL cert remaining {0} before expires'.format(remaining))
    return remaining

def ssl_expires_in(hostname, buffer_days=14):
    """Check if `hostname` SSL cert expires is within `buffer_days`.

    Raises `AlreadyExpired` if the cert is past due
    """
    try:
        remaining = ssl_valid_time_remaining(hostname)
    except ssl.CertificateError as e:
        return f'{hostname} cert error {e}'
    except ssl.SSLError as e:
        return f'{hostname} cert error {e}'
    except socket.timeout as e:
        return f'{hostname} could not connect'
    else:
        # if the cert expires in less than two weeks, we should reissue it
        if remaining < datetime.timedelta(days=0):
            # cert has already expired - uhoh!
            send_alert("Cert expired %s days ago for host %s" % (remaining.days, hostname))
            return "Cert expired %s days ago for host %s" % (remaining.days, hostname)
        elif remaining < datetime.timedelta(days=buffer_days):
            # expires sooner than the buffer
            send_alert("The %s SSL certificate expires alert! Remaining %s " % (hostname, remaining))
            return "The %s SSL certificate expires alert! Remaining %s " % (hostname, remaining)
        else:
            # everything is fine
            return hostname + " everything is fine"

def send_alert(alert_message):
    # Publish a simple message to the specified SNS topic
    try:
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,    
            Message=alert_message,
            Subject='The SSL certificate expires alert!' 
        )
    except ClientError as e:
        print(e)
        return {
            'statusCode': 500,
            'body': 'sns publish failed: ' + e.response['Error']['Message']
        }

# if __name__ == '__main__':
#     for host in fileinput.input():
#         host = host.strip()
#         print('Testing host {0}'.format(host))
#         message = ssl_expires_in(host)
#         print(message)