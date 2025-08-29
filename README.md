
## test working endpoint in browser console 
``` js
// Test in browser console:
fetch("https://guppaptxm6elewgoth2erzy4qm0cfoxe.lambda-url.us-east-1.on.aws/")
  .then(r => r.json())
  .then(console.log);
```
## 5. CloudFront caching
If you recently updated files, CloudFront might be serving cached versions. Either:
• Wait 5-10 minutes
• Or invalidate CloudFront cache:
``` bash
aws cloudfront create-invalidation --distribution-id E1KPHFE6PQNOJT --paths "/*" --region us-east-1
```


# quick fixes using AWS CLI
## Quick Fix Commands:

1. Update S3 bucket policy:
bash
aws s3api put-bucket-policy --bucket k21-cloud-resume-challenge --policy file://bucket-policy.json --region us-east-1


2. Update CloudFront distribution (you'll need to get the config, modify it, and update):
bash
# Get current config
aws cloudfront get-distribution-config --id E1KPHFE6PQNOJT --region us-east-1 > distribution-config.json

# Edit the JSON to fix:
# - Change OriginPath from "/chef-website-template/*" to "/chef-website-template"  
# - Add "DefaultRootObject": "index.html"

# Update distribution
aws cloudfront update-distribution --id E1KPHFE6PQNOJT --distribution-config file://modified-config.json --if-match ETAG_VALUE --region us-east-1


## Get SSL Certificate
# Request SSL certificate in us-east-1 (required for CloudFront)
``` bash
aws acm request-certificate \
    --domain-name domain4myproject.online \
    --domain-name www.domain4myproject.online \
    --validation-method DNS \
    --region us-east-1
```

## Validate Certificate
# Get certificate details
``` bash
aws acm describe-certificate --certificate-arn YOUR_CERT_ARN --region us-east-1
```
# Add the DNS validation records to your Route 53 hosted zone
``` bash
aws route53 change-resource-record-sets --hosted-zone-id YOUR_HOSTED_ZONE_ID --change-batch file://validation-records.json
```

## Update CloudFront Distribution

# Get current distribution config
``` bash
aws cloudfront get-distribution-config --id E1KPHFE6PQNOJT --region us-east-1 > current-config.json
```
# Edit the config to add:
# - "Aliases": ["domain4myproject.online", "www.domain4myproject.online"]
# - "ViewerCertificate": {"AcmCertificateArn": "YOUR_CERT_ARN", "SSLSupportMethod": "sni-only"}

# Update distribution
``` bash
aws cloudfront update-distribution --id E1KPHFE6PQNOJT --distribution-config file://updated-config.json --if-match ETAG --region us-east-1
```

##  Create Route 53 Records
bash
# Create A record for domain4myproject.online
``` bash
aws route53 change-resource-record-sets --hosted-zone-id YOUR_HOSTED_ZONE_ID --change-batch '{
    "Changes": [{
        "Action": "CREATE",
        "ResourceRecordSet": {
            "Name": "domain4myproject.online",
            "Type": "A",
            "AliasTarget": {
                "DNSName": "d1z3vmyl06pkv4.cloudfront.net",
                "EvaluateTargetHealth": false,
                "HostedZoneId": "Z2FDTNDATAQYW2"
            }
        }
    }]
}'
```
# Create A record for www.domain4myproject.online
``` bash
aws route53 change-resource-record-sets --hosted-zone-id YOUR_HOSTED_ZONE_ID --change-batch '{
    "Changes": [{
        "Action": "CREATE",
        "ResourceRecordSet": {
            "Name": "www.domain4myproject.online",
            "Type": "A",
            "AliasTarget": {
                "DNSName": "d1z3vmyl06pkv4.cloudfront.net",
                "EvaluateTargetHealth": false,
                "HostedZoneId": "Z2FDTNDATAQYW2"
            }
        }
    }]
}'

```

### ✅ Domain & SSL
• Domain: domain4myproject.online ✅
• SSL Certificate: ISSUED and in use ✅
• HTTPS working: HTTP/2 200 ✅

### ✅ DNS Records
• A record: Points to CloudFront ✅
• AAAA record: IPv6 support ✅
• NS records: Properly configured ✅

### ✅ Infrastructure
• CloudFront: Serving content with cache hits ✅
• S3: Properly configured ✅
• Lambda: Counter working (33 views) ✅



## Issues Encountered & Solutions

### 1. Lambda Function Errors
Issue: KeyError: 'Item' - Lambda function crashed when DynamoDB item didn't exist
python
# Problem: Assumed item always exists
views = response['Item']['views']

# Solution: Added error handling
if 'Item' in response:
    views = int(response['Item']['views']) + 1
else:
    views = 1


### 2. CORS Policy Errors
Issue: Access-Control-Allow-Origin header contains multiple values '*, *'
• **Cause:** Both Lambda Function URL config AND Lambda code were setting CORS headers
• **Solution:** Removed CORS from Function URL config, kept only in Lambda code

### 3. CloudFront 403 Errors
Issue: Website not accessible via CloudFront URL
• **Problem:** Origin path was /chef-website-template/* (invalid wildcard)
• **Solution:** Changed to /chef-website-template (no asterisk)
• **Added:** DefaultRootObject: "index.html"

### 4. Lambda Function Response Format
Issue: Function URL returned raw data instead of proper HTTP response

# Problem: Return raw data
return views

# Solution: Return proper HTTP response
``` bash
return {
    'statusCode': 200,
    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
    'body': json.dumps({'views': views})
}
```

### 5. JavaScript Counter Display
Issue: Counter showed [object Object] instead of number
``` javascript
// Problem: Displaying entire object
counter.innerHTML = `👀 Views: ${data}`;

// Solution: Access views property
counter.innerHTML = `👀 Views: ${data.views}`;
```

### 6. S3 Bucket Access
Issue: CloudFront couldn't access S3 bucket
• **Solution:** Added proper S3 bucket policy for CloudFront OAC
• **Scoped access:** arn:aws:s3:::bucket/chef-website-template/*

### 7. SSL Certificate & Custom Domain
Issue: Domain not working with HTTPS
• **Solution:** 
  • Created ACM certificate in us-east-1
  • Added DNS validation CNAME record
  • Updated CloudFront with custom domain aliases
  • Added Route 53 A records pointing to CloudFront

## Key Configuration Details

### Lambda Function (Final Working Version)
``` python3

python
import json
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('resume-challenge')

def lambda_handler(event, context):
    try:
        response = table.get_item(Key={'id': '1'})
        
        if 'Item' in response:
            views = int(response['Item']['views']) + 1
        else:
            views = 1
        
        table.put_item(Item={'id': '1', 'views': views})
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'views': views})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }

```
### JavaScript Counter (Final Working Version)
``` javascript
const counter = document.querySelector(".counter-number");
async function updateCounter() {
    try {
        let response = await fetch("https://guppaptxm6elewgoth2erzy4qm0cfoxe.lambda-url.us-east-1.on.aws/");
        let data = await response.json();
        counter.innerHTML = `👀 Views: ${data.views}`;
    } catch (error) {
        counter.innerHTML = `👀 Views: Error`;
    }
}
updateCounter();
```

## Final Architecture
• **S3:** Static website hosting
• **CloudFront:** CDN with custom domain domain4myproject.online
• **Route 53:** DNS management with SSL certificate
• **Lambda:** View counter with Function URL
• **DynamoDB:** View count storage
• **ACM:** SSL certificate for HTTPS

## Lessons Learned
1. Always handle missing DynamoDB items
2. Avoid duplicate CORS headers
3. CloudFront origin paths don't use wildcards
4. Lambda Function URLs need proper HTTP response format
5. SSL certificates for CloudFront must be in us-east-1
6. Test each component individually before integration

