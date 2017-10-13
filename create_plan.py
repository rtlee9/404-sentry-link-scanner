import stripe
from os import getenv
import argparse



if __name__ == '__main__':

    # parse arguments
    parser = argparse.ArgumentParser(description='Create user')
    parser.add_argument(
        '-n', '--name', type=str, help='Plan name', required=True)
    parser.add_argument(
        '-d', '--id', type=str, help='Plan ID')
    parser.add_argument(
        '-x', '--interval', type=str, help='Plan interval', required=True)
    parser.add_argument(
        '-c', '--currency', type=str, help='Payment currency', default="usd")
    parser.add_argument(
        '-a', '--amount', type=int, help='Payment amount', required=True)
    parser.add_argument(
        '-i', '--interval-count', type=int, help='Interval count', default=1)
    parser.add_argument(
        '-t', '--trial-period', type=int, help='Number of days of trial period', default=None)
    args = parser.parse_args()
    plan_id = args.id if args.id else args.name.replace(' ', '_').strip().lower()

    # add subscription plan
    stripe.api_key = getenv("STRIPE_API_KEY")
    plan = stripe.Plan.create(
        name=args.name,
        id=plan_id,
        interval=args.interval,
        interval_count=args.interval_count,
        currency=args.currency,
        amount=args.amount,
        trial_period_days=args.trial_period,
    )
    print(plan)
