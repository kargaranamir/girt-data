# -*- coding: utf-8 -*-

# Import Libraries
from github import Github
from github import BadCredentialsException, RateLimitExceededException, UnknownObjectException
import base64
import os
import json
import requests
from lxml import html
from lxml.etree import tostring
import csv
from glob import glob
import time
from tqdm import tqdm
import calendar


# multi-proceesing
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

# using an access token
# https://github.com/settings/tokens
# Token
username = "USER_NAME"
personal_token = "YOUR_PERSONAL_TOKEN"

# Authentication
pyg_session = Github(personal_token)
gh_session = requests.Session()
gh_session.auth = (username, personal_token)


# Get a single file
def get_file(content_obj, dir_name):
    coded_string = content_obj.content
    name = content_obj.name
    contents = base64.b64decode(coded_string)
    with open(os.path.join(dir_name, name), 'w') as f:
        f.write(contents.decode('utf-8'))

# Write files
def write_files(github_dir, dir_name):
    os.makedirs(dir_name, exist_ok=True)
    if isinstance(github_dir, list):
        # means that the dir is a floder not an item
        for item in github_dir:
            get_file(item, dir_name)


# Get Issue Templates for one repository
def get_issue_templates(repo, new_dir_name):
    try:
        # use contents api
        content_path = repo.get_contents(".github/ISSUE_TEMPLATE")
        write_files(content_path, new_dir_name)
        return True
    except:
        return False

# Get repository characteristics (PYGitHub)
def get_repo_features_1(repo):
    repo_dictionary = {
        "full_name": repo.full_name,
        "is_fork": repo.fork,
        "has_issues": repo.has_issues,
        "created_at": str(repo.created_at),
        "last_modified": str(repo.last_modified),
        "pushed_at": str(repo.pushed_at),
        "main_language": repo.language,
        "total_issues_count": repo.get_issues(state="all").totalCount,
        "open_issues_count": repo.get_issues(state='open').totalCount,
        "closed_issues_count": repo.get_issues(state='closed').totalCount,
        "total_pull_requests_count": repo.get_pulls(state="all").totalCount,
        "open_pull_requests_count": repo.get_pulls(state='open').totalCount,
        "closed_pull_requests_count": repo.get_pulls(state='closed').totalCount,
        "size": repo.size,
        "topics": repo.get_topics(),
        "stargazers_count": repo.stargazers_count,
        "subscribers_count": repo.subscribers_count,
        "forks_count": repo.forks_count,
        "commits_count": repo.get_commits().totalCount,
        "assignees_count": repo.get_assignees().totalCount,
        "branches_count": repo.get_branches().totalCount,
        "releases_count": repo.get_releases().totalCount,
        "is_archive": repo.archived,
        "has_wiki": repo.has_wiki
    }
    return repo_dictionary


# Get repository characteristics (XPath Query)
def get_repo_features_2(repo, request_obj):
    """
    NOTICE: This function may be affected by changes to the GitHub UI, so please check it beforehand and update the Xpath query accordingly.
    """
    repo_dictionary = {}

    # contributors count
    r = request_obj.get('https://github.com/' + repo.full_name)
    xpath = '//*[@id="repo-content-pjax-container"]/div/div/div[3]/div[2]/div/*/div/h2/a'
    xpath_result = [x.text_content() for x in html.fromstring(r.text).xpath(xpath)]

    for x in xpath_result:
        if 'Contributors' in x:
            repo_dictionary["contributors_count"] = int(
                x.replace('Contributors', '').replace('\n', '').replace(',', '').strip())

    # default 1
    repo_dictionary["contributors_count"] = repo_dictionary.get("contributors_count", 1)

    # issue count
    r = request_obj.get('https://github.com/' + repo.full_name + '/issues')
    xpath = '//*[@id="repo-content-pjax-container"]/div/*/div/*/text()'
    xpath_result = html.fromstring(r.text).xpath(xpath)

    for x in xpath_result:
        if 'Open' in x:
            repo_dictionary["open_issues_countv2"] = int(
                x.replace('\n', '').replace('Open', '').replace(',', '').strip())
        if 'Closed' in x:
            repo_dictionary["closed_issues_countv2"] = int(
                x.replace('\n', '').replace('Closed', '').replace(',', '').strip())

    repo_dictionary["total_issues_countv2"] = repo_dictionary["open_issues_countv2"] + repo_dictionary[
        "closed_issues_countv2"]

    return repo_dictionary


# Merge repository characteristics
def get_repo_features(repo, new_dir_name, issue_template_exist, request_obj):
    try:
        dict1 = get_repo_features_1(repo)
    except:
        dict1 = {}

    try:
        dict2 = get_repo_features_2(repo, request_obj)
    except:
        dict2 = {}

    repo_dictionary_merged = {**dict1, **dict2}
    # add has_issue_template
    repo_dictionary_merged['has_IRT'] = issue_template_exist

    # save
    with open(new_dir_name + ".json", "w") as fj:
        json.dump(repo_dictionary_merged, fj, indent=4)


def wait_rate_limit(core_rate_limit):
    reset_timestamp = calendar.timegm(core_rate_limit.reset.timetuple())
    # add 10 seconds to be sure the rate limit has been reset
    sleep_time = reset_timestamp - calendar.timegm(time.gmtime()) + 10
    print(f"waiting for {sleep_time}s")
    time.sleep(sleep_time)


def run(username_reponame, issue_dir, feature_dir, pygithub_obj, request_obj):
    try:
        repo = pygithub_obj.get_repo(username_reponame)

        # make directories
        issue_dir = issue_dir.rstrip('/')
        feature_dir = feature_dir.rstrip('/')

        os.makedirs(issue_dir, exist_ok=True)
        os.makedirs(feature_dir, exist_ok=True)


        # issue template
        issue_template_dir_name = issue_dir + '/' + username_reponame.replace('/', '@')
        issue_template_exist = get_issue_templates(repo, issue_template_dir_name)

        # repo features (e.g, stars)
        repo_feature_dir_name = feature_dir + '/' + username_reponame.replace('/', '@')
        get_repo_features(repo, repo_feature_dir_name, issue_template_exist, request_obj)

        return 1

    except RateLimitExceededException as re:
        print(re)
        core_rate_limit = pygithub_obj.get_rate_limit().core
        wait_rate_limit(core_rate_limit)
        run(username_reponame, issue_dir, feature_dir, pygithub_obj, request_obj)

    except UnknownObjectException as ue:
        print(ue)
        print("The input repo can not be reached")
        return 0

    except BadCredentialsException as be:
        print(be)
        print("Bad credentials, trying without token....")
        sub_pygithub_obj = Github()
        sub_request_obj = requests.Session()
        run(username_reponame, issue_dir, feature_dir, sub_pygithub_obj, sub_request_obj)
        return 1

    except Exception as e:
        print(e)
        return 0

# Your target repositories
target_repos = ['keras-team/keras', 'tensorflow/tensorflow', 'user_name/repo_name']

print("start_main")
start = time.time()
with ThreadPoolExecutor(max_workers=1) as executor:
    results = executor.map(
        partial(
            run,
            issue_dir = './IRTs',
            feature_dir='./characteristics',
            pygithub_obj = pyg_session,
            request_obj = gh_session
        ),
        target_repos,
    )

end = time.time()

print("Time Taken using multithreading:{}".format(end - start))
