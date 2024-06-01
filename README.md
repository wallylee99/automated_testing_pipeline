<!DOCTYPE html>
<html>

<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="https://stackedit.io/style.css" />
</head>

<body class="stackedit">
  <div class="stackedit__html"><h1 id="use-aws-codepipeline-cicd-to-automate-unit-test-and-deploy-lambda-function">Use AWS CodePipeline CI/CD to automate Unit Test and Deploy Lambda Function</h1>
<p>In this guide, I will walk you through setting up a Continuous Integration and Continuous Deployment (CI/CD) pipeline. This pipeline will automate unit testing and deploy your code to an AWS Lambda function using AWS CodePipeline, CodeBuild and CloudFormation.</p>
<p><img src="https://www.wallacel.com/wp-content/uploads/2024/05/cicd-pipeline-3.png" alt=""></p>
<h2 id="source-stage">Source Stage</h2>
<p>Our journey begins with a GitHub repository, which stores our source code. Any time changes are pushed to this repository, the pipeline is automatically triggered.</p>
<h2 id="build--test-stage">Build &amp; Test Stage</h2>
<p>Next, AWS CodeBuild steps in to compile the source code and run unit tests. Upon successful completion, the build artifacts are stored in an S3 bucket.</p>
<h2 id="deploy-stage">Deploy Stage</h2>
<p>Finally, AWS CloudFormation takes over, retrieving the source code from the S3 bucket and deploying the function to AWS Lambda.</p>
<h2 id="step-1-create-lambda-function">Step 1: Create Lambda Function</h2>
<p>First, I create a simple Lambda Function that takes a city name as a parameter and returns the current temperature. To fetch the weather information, I signup for a free account at  <a href="https://openweathermap.org/">OpenWeather.org</a>  to use their API. Following is the API call to get the weather data:</p>
<pre class=" language-hcl"><code class="prism  language-hcl">http://api.openweathermap.org/data/2.5/weather?q=city_name&amp;appid=api_key&amp;units=metric
</code></pre>
<p>This is my Lambda function:</p>
<p><img src="https://www.wallacel.com/wp-content/uploads/2024/05/Screenshot-2024-05-31-at-12.08.13-1024x669.png" alt=""></p>
<p>I use the following event data to test my function and get a response that shows the function is working:</p>
<pre class=" language-hcl"><code class="prism  language-hcl">{
  "city": "Vancouver"
}

</code></pre>
<p><img src="https://www.wallacel.com/wp-content/uploads/2024/05/Screenshot-2024-05-31-at-12.22.17-1024x367.png" alt=""></p>
<p>Then I upload my code to GitHub repo:</p>
<pre class=" language-hcl"><code class="prism  language-hcl">git add.; git commit -m "Add Lambda Function Python code"; git push

</code></pre>
<h2 id="step-2-create-codebuild-project">Step 2: Create CodeBuild Project</h2>
<p>To enable CodeBuild to retrieve source code from GitHub, setup a connection using OAuth and choose the source code repository. This connection allows CodeBuild to automatically fetch and build the source code whenever changes are pushed to the specified GitHub repository.</p>
<p><img src="https://www.wallacel.com/wp-content/uploads/2024/05/source.png" alt=""></p>
<p>Since my Lambda function is written in Python and there is no Python runtime available in the standard environment options, I use a standard runtime and specify my runtime in the  <code>buildspec.yml</code>  file</p>
<p><img src="https://www.wallacel.com/wp-content/uploads/2024/05/Screenshot-2024-05-31-at-12.53.21-1024x788.png" alt=""></p>
<p><img src="https://www.wallacel.com/wp-content/uploads/2024/05/Screenshot-2024-05-31-at-12.53.48-1024x495.png" alt=""></p>
<p>This setup ensures that CodeBuild uses the specified Python runtime to build and test my Lambda function code. This file is also where I add automated unit tests. Here’s how I set it up my buildspec.yml:</p>
<pre class=" language-hcl"><code class="prism  language-hcl">version: 0.2
phases:
  install:
    runtime-versions:
      python: 3.10   # Specify the Python version you need
  build:
    commands:
      - echo Testing the Lambda functon...
      - python -m unittest discover tests
artifacts:
  files:
    - '**/*'    # Include all files in the build output

</code></pre>
<h3 id="explanation">Explanation:</h3>
<ul>
<li><strong>install phase</strong>:
<ul>
<li><code>runtime-versions</code>  specifies the Python version.</li>
</ul>
</li>
<li><strong>build phase</strong>:
<ul>
<li>Runs unit tests by automatically discover any test methods within the  <strong>tests</strong>  subfolder.</li>
</ul>
</li>
<li><strong>artifacts</strong>:
<ul>
<li>Specifies which files to include in the build output.</li>
</ul>
</li>
</ul>
<p>Here’s a simple unit test example. It checks two things: whether the function returns a success code of 200, and whether the response includes the same city name I provided along with its current temperature:</p>
<pre class=" language-hcl"><code class="prism  language-hcl">def unit_test(self):
    event={'city':'Vancouver'}
    result = lambda_function.lambda_handler(event, None)
    self.assertEqual(result['statusCode'], 200)
    self.assertEqual(result['headers']['Content-Type'], 'application/json')
    self.assertIn(event['city'], result['body'])
    self.assertIn('current_temperature', result['body'])
</code></pre>
<p>CodeBuild can save your code as a zip file in S3 bucket, which is a crucial step. Later on, CloudFormation will use this stored code as a source to deploy it to Lambda.</p>
<p><img src="https://www.wallacel.com/wp-content/uploads/2024/05/Screenshot-2024-05-31-at-13.19.47-1024x732.png" alt=""></p>
<p>You can set up webhook events to tell CodeBuild to rebuild your code whenever there’s a push request on GitHub. However, I prefer to add this to my CodePipeline instead and have it trigger CodeBuild automatically.</p>
<p><img src="https://www.wallacel.com/wp-content/uploads/2024/05/Screenshot-2024-05-31-at-13.22.34-1024x248.png" alt=""></p>
<h2 id="step-3-create-cloudformation-stack">Step 3: Create CloudFormation Stack</h2>
<p>To deploy my Python function code to AWS Lambda using CloudFormation, I need to prepare a CloudFormation template that specifies the location of the source code zip file stored in the S3 bucket. Here’s an example of how my ‘cloudformation_lambda.yml’ template looks:</p>
<pre class=" language-hcl"><code class="prism  language-hcl">Resources:
  LambdaFunction:
    Type: 'AWS::Lambda::Function'
    Properties:
      FunctionName: myWeatherLambda
      Handler: index.handler
      Runtime: python3.10
      Role: !GetAtt LambdaFunctionRole.Arn
      MemorySize: 1024
      Code: 
        S3Bucket: wallace-bucket-for-codebuild
        S3Key: myWeatherLambdaCodeBuild/codebuild.zip
                  
  LambdaFunctionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
        - Effect: Allow
          Principal:
            Service:
            - lambda.amazonaws.com
          Action:
          - sts:AssumeRole
      Path: "/"
      Policies:
      - PolicyName: AppendToLogsPolicy
        PolicyDocument:
          Version: '2012-10-17'
          Statement:
          - Effect: Allow
            Action:
            - logs:CreateLogGroup
            - logs:CreateLogStream
            - logs:PutLogEvents
            Resource: "*"
</code></pre>
<p>The ‘<strong>S3Bucket</strong>  ‘ parameter specifies the S3 bucket name and the ‘<strong>S3Key</strong>‘ parameter indicates where the Lambda function code zip file is stored. The template also creates a Lambda function role that grants the Lambda function permission to write logs.</p>
<p>I use this template and create my CloudFormation stack:</p>
<p><img src="https://www.wallacel.com/wp-content/uploads/2024/05/Screenshot-2024-05-31-at-13.55.07-1024x860.png" alt=""></p>
<h2 id="stage-4-create-service-role-for-codepipeline">Stage 4: Create Service role for CodePipeline</h2>
<p>A service role is needed to grant permission to CodePipeline to access the S3 bucket, deploy CloudFormation stacks, create Lambda function role and other necessary actions. Here’s how to create the IAM role:</p>
<p><img src="https://www.wallacel.com/wp-content/uploads/2024/05/Screenshot-2024-05-31-at-22.26.42.png" alt=""></p>
<p>Edit the trust relationships to change the service from ‘<strong><a href="http://ec2.amazonaws.com">ec2.amazonaws.com</a></strong>‘ to ‘<strong><a href="http://cloudformation.amazonaws.com">cloudformation.amazonaws.com</a></strong>‘</p>
<p><img src="https://www.wallacel.com/wp-content/uploads/2024/05/Screenshot-2024-05-31-at-22.28.10.png" alt=""></p>
<p>For permission, create an inline policy using the following:</p>
<pre class=" language-hcl"><code class="prism  language-hcl">{
	"Statement": [
		{
			"Action": [
				"s3:GetObject",
				"s3:GetObjectVersion",
				"s3:GetBucketVersioning",
				"s3:PutObject",
				"iam:CreateRole",
				"iam:DeleteRolePolicy",
				"iam:GetRole",
				"iam:GetRolePolicy",
				"iam:PassRole",
				"iam:DetachRolePolicy",
				"iam:DeleteRolePolicy",
				"iam:DeleteRole",
				"iam:AttachRolePolicy",
				"iam:PutRolePolicy",
				"lambda:GetFunction",
				"lambda:GetFunctionConfiguration",
				"lambda:CreateFunction",
				"lambda:DeleteFunction"
			],
			"Resource": [
				"arn:aws:s3:::*",
				"arn:aws:iam::*:role/*",
				"arn:aws:lambda:ca-central-1:339713082608:function*"
			],
			"Effect": "Allow"
		},
		{
			"Action": [
				"codedeploy:CreateDeployment",
				"codedeploy:GetApplicationRevision",
				"codedeploy:GetDeployment",
				"codedeploy:GetDeploymentConfig",
				"codedeploy:RegisterApplicationRevision"
			],
			"Resource": "*",
			"Effect": "Allow"
		},
		{
			"Action": [
				"cloudwatch:*",
				"s3:*",
				"cloudformation:*",
				"iam:PassRole"
			],
			"Resource": "*",
			"Effect": "Allow"
		},
		{
			"Action": [
				"lambda:InvokeFunction",
				"lambda:ListFunctions"
			],
			"Resource": "*",
			"Effect": "Allow"
		},
		{
			"Action": [
				"cloudformation:CreateStack",
				"cloudformation:DeleteStack",
				"cloudformation:DescribeStacks",
				"cloudformation:UpdateStack",
				"cloudformation:CreateChangeSet",
				"cloudformation:DeleteChangeSet",
				"cloudformation:DescribeChangeSet",
				"cloudformation:ExecuteChangeSet",
				"cloudformation:SetStackPolicy",
				"cloudformation:ValidateTemplate",
				"iam:PassRole"
			],
			"Resource": "*",
			"Effect": "Allow"
		},
		{
			"Action": [
				"codebuild:BatchGetBuilds",
				"codebuild:StartBuild"
			],
			"Resource": "*",
			"Effect": "Allow"
		}
	],
	"Version": "2012-10-17"
}
</code></pre>
<h2 id="stage-5-create-codepipeline">Stage 5: Create CodePipeline</h2>
<p>Now, the final step is to integrate all the components by creating a CodePipeline. Here’s how to set it up:</p>
<p>Set the source provider to GitHub and specify the repository that contains the source code.</p>
<p><img src="https://www.wallacel.com/wp-content/uploads/2024/05/source-2.png" alt=""></p>
<p>A git push to the repository will trigger the pipeline:</p>
<p><img src="https://www.wallacel.com/wp-content/uploads/2024/05/Screenshot-2024-05-31-at-22.42.39.png" alt=""></p>
<p>To configure the build stage, use AWS CodeBuild as the build provider with the project created in Step 2.</p>
<p><img src="https://www.wallacel.com/wp-content/uploads/2024/05/build.png" alt=""></p>
<p>Use AWS CloudFormation as the deploy provider and specify the CloudFormation template prepared in Step 3.</p>
<p><img src="https://www.wallacel.com/wp-content/uploads/2024/05/Screenshot-2024-05-31-at-22.52.09.png" alt=""></p>
<p>For the role name, use the IAM service role created in Step 4.</p>
<p><img src="https://www.wallacel.com/wp-content/uploads/2024/05/Screenshot-2024-05-31-at-22.52.26.png" alt=""></p>
<p>With the CodePipeline set up, push a change to the GitHub repository to see the pipeline in action.</p>
<p><img src="https://www.wallacel.com/wp-content/uploads/2024/05/codepipeline-699x1024.png" alt=""></p>
<p><img src="https://www.wallacel.com/wp-content/uploads/2024/05/Screenshot-2024-05-31-at-22.58.03.png" alt=""></p>
<p>Once the pipeline executes, go to the Lambda console to verify if the Lambda function has been created successfully.</p>
<p><img src="https://www.wallacel.com/wp-content/uploads/2024/05/Screenshot-2024-05-31-at-22.59.23.png" alt=""></p>
</div>
</body>

</html>
