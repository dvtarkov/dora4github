import requests
from datetime import datetime, timedelta


def get_all_branches(repo_name, repo_owner, header):
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/branches'
    response = requests.get(url, headers=header)
    branches = response.json()
    return [branch['name'] for branch in branches]


def get_recent_deployments(repo_name, repo_owner, branch, header):
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/deployments'
    response = requests.get(url, headers=header)
    deployments = response.json()
    last_month = datetime.now() - timedelta(days=30)
    recent_deployments = [d for d in deployments if
                          datetime.strptime(d['created_at'], '%Y-%m-%dT%H:%M:%SZ') > last_month and d['ref'] == branch]
    return recent_deployments


def get_repo_creation_time(repo_name, repo_owner, header):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    response = requests.get(url, headers=header)
    repo = response.json()
    return datetime.strptime(repo['created_at'], '%Y-%m-%dT%H:%M:%SZ')


def get_recent_commits(repo_name, repo_owner, branch, header):
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/commits?sha={branch}'
    response = requests.get(url, headers=header)
    commits = response.json()
    last_month = datetime.now() - timedelta(days=30)
    recent_commits = [c for c in commits if
                      datetime.strptime(c['commit']['committer']['date'], '%Y-%m-%dT%H:%M:%SZ') > last_month]
    return recent_commits


def get_recent_issues(repo_name, repo_owner, header):
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues?state=closed'
    response = requests.get(url, headers=header)
    issues = response.json()
    last_month = datetime.now() - timedelta(days=30)
    recent_issues = [i for i in issues if datetime.strptime(i['closed_at'], '%Y-%m-%dT%H:%M:%SZ') > last_month]
    return recent_issues


def get_deployment_statuses(repo_name, repo_owner, deployment, header):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/deployments/{deployment['id']}/statuses"
    response = requests.get(url, headers=header)
    return response.json()


def get_pull(repo_name, repo_owner, sha, header):
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{sha}/pulls'
    response = requests.get(url, headers=header)
    return response.json()


def get_pull_origin_commits(pull, header):
    url = pull['commits_url']
    response = requests.get(url, headers=header)
    commits = response.json()
    return [datetime.strptime(commit['commit']['committer']['date'], '%Y-%m-%dT%H:%M:%SZ')
            for commit in commits if len(commit['parents']) == 1]
