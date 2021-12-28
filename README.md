# ASW Lambda Scripts
Booking(AWS Lambda) of BDGC Golf
https://www.bdgc.com.au/


## Description
Please read this reference link.
https://towardsdatascience.com/introduction-to-amazon-lambda-layers-and-boto3-using-python3-39bd390add17
https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html
https://medium.com/the-cloud-architect/getting-started-with-aws-lambda-layers-for-python-6e10b1f9a5d


## AWS CloudWatch Events
cron(0 11 ? * TUE *)
cron(0 11 ? * FRI *)


## ChangeLog

1.4 2019/03/01
	Fix Some Bugs.

1.3 2019/02/15
	If the row will be blocked, then the script will try to book at the next row.

1.2 2019/02/14
	Add "Confirm Booking" function.

1.1 2019/02/12
	Fix Book Function.

1.0 2019/02/11
	Initial Production Versioin.