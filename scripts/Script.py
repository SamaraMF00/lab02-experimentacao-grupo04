import csv
import requests
from datetime import datetime
import subprocess
import shutil
import os

def calculate_age(created_at):
    created_at_date = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
    current_date = datetime.now()
    age = current_date - created_at_date
    return age.days

def get_repository_info(repository):
    repo_node = repository['node']
    name = repo_node['name']
    owner = repo_node['owner']['login']
    popularity = repo_node['stargazers']
    activity = repo_node['releases']['totalCount']
    maturity = calculate_age(repo_node['createdAt'])

    return {
        'Repository name': name,
        'Repository owner': owner,
        'Popularity - Stars': popularity,
        'Total releases': activity,
        'Repository age (days)': maturity,
    }

def read_ck_csv(csv_file):
    metrics = {'cbo': 0, 'dit': 0, 'lcom': 0, 'loc': 0}
    with open(csv_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            for metric in metrics:
                metrics[metric] += int(row[metric])
    return metrics

def write_metric_result(metrics, output_file):
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['Metric', 'Total']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for metric, total in metrics.items():
            writer.writerow({'Metric': metric, 'Total': total})

def download_repository(repo_url):
    os.system(f"git clone {repo_url}")

def execute_ck(project_dir, output_dir):
    subprocess.run(["java", "-jar", "../ck/target/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar", project_dir, "true", "0", "true", output_dir])

def delete_repository(directory):
    shutil.rmtree(directory)


def main():
    token = 'TOKEN'
    headers = {'Authorization': f'Bearer {token}'}
    endpoint = 'https://api.github.com/graphql'
    query = '''
    query ($after: String!) {
        search(query: "stars:>1 filename:*.java", type: REPOSITORY, first: 1, after: $after) {
            pageInfo {
                endCursor
                startCursor
                hasNextPage
                hasPreviousPage
            }
            edges {
                node {
                    ... on Repository {
                        name
                        createdAt
                        updatedAt
                        owner {
                            login
                        }
                        releases {
                            totalCount
                        }
                        stargazers {
                            totalCount
                        }
                    }
                }
            }
        }
    }
'''

    repositories_info = []
    has_next_page = True
    end_cursor = ""
    variables = {}
    repoCont = 0

    # Change "while" to run once
    while has_next_page and len(repositories_info) < 1:
    # while len(repositories_info) < 2:
        if end_cursor == "":
            query_starter = query.replace(', after: $after', "")
            query_starter = query_starter.replace('($after: String!)', "")
            response = requests.post(endpoint, json={'query': query_starter}, headers=headers)
        else:
            variables['after'] = end_cursor
            response = requests.post(endpoint, json={'query': query, 'variables': variables}, headers=headers)

        data = response.json()

        for repository in data['data']['search']['edges']:           
            repository_info = get_repository_info(repository)
            repositories_info.append(repository_info) 

            # Download repository
            repo_url = f"https://github.com/{repository_info['Repository owner']}/{repository_info['Repository name']}.git"
            download_repository(repo_url)

            # Execute CK
            execute_ck(f"../lab02-experimentacao-grupo04/{repository_info['Repository name']}", f"../lab02-experimentacao-grupo04/{repository_info['Repository name']}/")

            # Read CK CSV and sum metrics
            csv_file = f"../lab02-experimentacao-grupo04/{repository_info['Repository name']}/class.csv"
            metrics = read_ck_csv(csv_file)

            # Write metric result to CSV
            output_file = f"../lab02-experimentacao-grupo04/scripts/dataset/repositories_info_ck.csv"
            write_metric_result(metrics, output_file)

            # Delete repository
            delete_repository(f"../lab02-experimentacao-grupo04/{repository_info['Repository name']}")

        if data['data']['search']['pageInfo']['hasNextPage']:
            end_cursor = data['data']['search']['pageInfo']['endCursor']
        else:
            has_next_page = False

        repoCont += 20

    # Create csv: 1000 repository list
    # with open('repositories_info_graphql.csv', 'w', newline='') as fp:
    #     fieldnames = repositories_info[0].keys()
    #     writer = csv.DictWriter(fp, fieldnames=fieldnames)
        
    #     writer.writeheader()
    #     for info in repositories_info:
    #         writer.writerow(info)
        
if __name__ == "__main__":
    main()
