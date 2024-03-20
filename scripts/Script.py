import csv
import requests
from datetime import datetime

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
    size = repo_node['languages']['code_lines']
    activity = repo_node['releases']['totalCount']
    maturity = calculate_age(repo_node['createdAt'])

    return {
        'Repository name': name,
        'Repository owner': owner,
        'Popularity - Stars': popularity,
        'Size': size,
        'Total releases': activity,
        'Repository age (days)': maturity,
    }

def main():
    token = TOKEN
    headers = {'Authorization': f'Bearer {token}'}
    endpoint = 'https://api.github.com/graphql'
    query = '''
    query ($after: String) {
  search(query: "stars:>1 language:Java", type: REPOSITORY, first: 1, after: $after) {
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
          languages(first: 1) {
            totalCount
            edges {
              code_lines: size
              node {
                name
              }
            }
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

    while has_next_page and repoCont < 1000:
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

        if data['data']['search']['pageInfo']['hasNextPage']:
            end_cursor = data['data']['search']['pageInfo']['endCursor']
        else:
            has_next_page = False

        repoCont += 20            

    # for info in repositories_info:
    #     print(info)
    #     print()

    with open('repositories_info.csv', 'w', newline='') as fp:
        fieldnames = repositories_info[0].keys()
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        
        writer.writeheader()
        for info in repositories_info:
            writer.writerow(info)

if __name__ == "__main__":
    main()
