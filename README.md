# 404 Sentry
## Link scanner API

1 out of 20 html links will break within the first year. Broken links on your website can ruin the user experience and turn users away, ultimately lowering future web traffic and related revenues. Links can break through no fault of your own and you'd never even notice. [404 Sentry](https://404sentry.com/) protects your site by scanning it for broken links (404s plus other exceptions) through automatic, recurring jobs and sends a summary of any potential errors directly to your inbox.

Use this API to self host your 404 Sentry scanner or sign up for automated, recurring scan jobs on the [404 Sentry web app](https://404sentry.com/) to make sure your content is never out of date!

## Usage
1. Set environment variables:
	* `DATABASE_URL`: URL of PostgreSQL server
	* `CONFIG`: configuration type (ProductionConfig, StagingConfig, DevelopmentConfig, TestingConfig)
	* `EMAIL_ADDRESS`: email address from which to send alerts
	* `EMAIL_PASSWORD`: email password for sending alerts
	* `TEST_USER`: username for test authentication
	* `TEST_PASSWORD`: password for test authentication
	* `STRIPE_API_KEY`: API key for [Stripe](https://stripe.com/) account
1. Set up virtualenv: `virtualenv venv && source venv/bin/activate`
1. Install requirements: `pip install -r requirements.txt`
1. Run web application: `python run.py` or `gunicorn app:app`
