# HKS Today Repo
This repo holds all of the relevant code for producing [www.hkstoday.com](https://www.hkstoday.com), which aggregates events at the Harvard Kennedy School and allows a user to quickly add to calendar.

If you'd like to add to and / or improve the site, feel free to submit a pull request.

## website
Flask application for the actual website, deployed on AWS Elastic Beanstalk

## events_scraper
Scraper scripts, run daily as a cron job on AWS Lambda

## events_senders
Email scripts, run as cron jobs on AWS Lambda