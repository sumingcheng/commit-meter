# 获取你的github的仓库信息
import requests

# 你的 GitHub 用户名
user_id = 'sumingcheng'

# 你的 GitHub 个人访问令牌（Personal Access Token）
token = ''  # 在这里替换为你的 GitHub 令牌

# GitHub API URL
base_url = 'https://api.github.com'

# 请求仓库信息的 URL
url = f'{base_url}/users/{user_id}/repos'

# HTTP 请求头，带上访问令牌
headers = {
    'Authorization': f'token {token}'
}

# 每次请求返回的仓库数量，最多 100 个
per_page = 100
page = 1

# 存储所有仓库数据
repositories = []

# 循环获取所有分页的数据
while True:
    # 发起 GET 请求
    response = requests.get(url, headers=headers, params={'per_page': per_page, 'page': page})

    # 如果请求成功
    if response.status_code == 200:
        data = response.json()

        # 如果返回的数据为空，说明已获取所有仓库
        if not data:
            break

        # 将当前页面的仓库数据添加到列表
        repositories.extend(data)

        # 增加分页，获取下一页的数据
        page += 1
    else:
        print(f"Error: {response.status_code} - {response.text}")
        break

# 输出获取到的仓库信息
for repo in repositories:
    print(f"仓库名称: {repo['name']}")
    print(f"仓库地址: {repo['html_url']}")
    print(f"描述: {repo.get('description', '无描述')}")
    print(f"星标数量: {repo['stargazers_count']}")
    print('-' * 40)
