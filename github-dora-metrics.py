from flask import Flask, Response
from prometheus_client import Gauge, generate_latest
from utils import get_all_branches, get_recent_deployments, get_recent_commits, get_recent_issues, \
    get_deployment_statuses, get_pull, get_pull_origin_commits, get_repo_creation_time
from datetime import datetime, timedelta
from config import REPOS

# Инициализация метрик Prometheus с метками
deployment_frequency_gauge = Gauge('github_deployment_frequency', 'Deployment Frequency', ['repo', 'branch'])
lead_time_gauge = Gauge('github_lead_time_for_changes', 'Lead Time for Changes', ['repo', 'branch'])
change_failure_rate_gauge = Gauge('github_change_failure_rate', 'Change Failure Rate', ['repo', 'branch'])
mean_time_to_restore_gauge = Gauge('github_mean_time_to_restore', 'Mean Time to Restore', ['repo', 'branch'])

app = Flask(__name__)


def calculate_commit_frequency(commits, repo_time):
    repo_creation_dt = repo_time
    now = datetime.now()
    last_month = now - timedelta(days=30)
    deployment_dates = [datetime.strptime(c["commit"]['committer']["date"], '%Y-%m-%dT%H:%M:%SZ') for c in commits]
    recent_deployments = [d for d in deployment_dates if d > last_month]

    time = (now - repo_creation_dt).days if last_month < repo_creation_dt else 30
    deployment_frequency = len(recent_deployments) / time

    return deployment_frequency


# Здесь если на неудачный деплой заведена Issue, она может быть учитана несколько раз
def calculate_change_failure_rate(deployments, issues, failed_deployments):
    failure_issues = [issue for issue in issues if
                      'bug' in [label['name'] for label in issue['labels']] and 'deployment' in issue['title'].lower()]
    change_failure_rate = (len(failure_issues) + failed_deployments) / len(deployments) if deployments else 0
    return change_failure_rate


def calculate_mean_time_to_restore(issues):
    failure_issues = [issue for issue in issues if
                      'bug' in [label['name'] for label in issue['labels']] and 'deployment' in issue['title'].lower()]
    restoration_times = [
        datetime.strptime(issue['closed_at'], '%Y-%m-%dT%H:%M:%SZ') - datetime.strptime(issue['created_at'],
                                                                                        '%Y-%m-%dT%H:%M:%SZ') for issue
        in failure_issues]
    mean_time_to_restore = sum([r.total_seconds() for r in restoration_times]) / len(
        restoration_times) / 3600 if restoration_times else 0
    return mean_time_to_restore


def calculate_lead_time_for_changes(repo_name, repo_owner, deployment, header):
    lead_times = list()
    deployment_time = datetime.strptime(deployment['created_at'], '%Y-%m-%dT%H:%M:%SZ')
    deployment_sha = deployment['sha']

    pulls = get_pull(repo_name, repo_owner, deployment_sha, header)

    for pull in pulls:
        original_commit_times = get_pull_origin_commits(pull, header)
        for commit_time in original_commit_times:
            lead_times.append((deployment_time - commit_time).total_seconds())
    return lead_times


@app.route('/metrics/<repo_tag>')
def metrics(repo_tag):
    if repo_tag in REPOS:
        repo = REPOS[repo_tag]
        header = {
            'Authorization': f'token {repo["token"]}',
            'Accept': 'application/vnd.github.v3+json'
        }
        repo_name = repo["name"]
        repo_owner = repo["owner"]
    else:
        raise Exception("Repo not found")

    branches = get_all_branches(repo_name, repo_owner, header)
    repo_creation_dt = get_repo_creation_time(repo_name, repo_owner, header)

    for branch in branches:
        failed_deployments = 0
        lead_times = list()

        deployments = get_recent_deployments(repo_name, repo_owner, branch, header)
        commits = get_recent_commits(repo_name, repo_owner, branch, header)
        issues = get_recent_issues(repo_name, repo_owner, header)

        for deployment in deployments:
            statuses = get_deployment_statuses(repo_name, repo_owner, deployment, header)

            if any([status['state'] == "failure" for status in statuses]):
                failed_deployments += 1
            else:
                lead_times.extend(calculate_lead_time_for_changes(repo_name, repo_owner, deployment, header))

        deployment_frequency = calculate_commit_frequency(commits, repo_creation_dt)
        lead_time_for_changes = sum(lead_times) / len(lead_times) / 3600 if lead_times else 0
        change_failure_rate = calculate_change_failure_rate(deployments, issues, failed_deployments)
        mean_time_to_restore = calculate_mean_time_to_restore(issues)

        # Установка значений метрик с метками
        deployment_frequency_gauge.labels(repo=repo_name, branch=branch).set(deployment_frequency)
        lead_time_gauge.labels(repo=repo_name, branch=branch).set(lead_time_for_changes)
        change_failure_rate_gauge.labels(repo=repo_name, branch=branch).set(change_failure_rate)
        mean_time_to_restore_gauge.labels(repo=repo_name, branch=branch).set(mean_time_to_restore)

    return Response(generate_latest(), mimetype='text/plain')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
