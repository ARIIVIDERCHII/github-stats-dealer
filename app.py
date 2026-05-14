import os
import time
import requests
from flask import Flask, make_response, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_USERNAME = os.getenv('GITHUB_USERNAME')


CACHE = {"data": None, "timestamp": 0}
CACHE_TTL = 14400 

def get_github_data():
    current_time = time.time()
    if CACHE["data"] and (current_time - CACHE["timestamp"] < CACHE_TTL):
        return CACHE["data"]


    query = """
    {
      user(login: "%s") {
        repositories(ownerAffiliations: OWNER, isFork: false, first: 100, orderBy: {field: PUSHED_AT, direction: DESC}) {
          totalCount
          nodes {
            stargazerCount
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges { size, node { name } }
            }
          }
        }
        contributionsCollection { totalCommitContributions }
      }
    }
    """ % GITHUB_USERNAME

    headers = {'Authorization': f'bearer {GITHUB_TOKEN}'}
    response = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    
    if response.status_code != 200:
        return [], 0, 0, 0

    data = response.json().get('data', {}).get('user', {})
    repos_data = data.get('repositories', {})
    total_repos = repos_data.get('totalCount', 0)
    
    language_bytes = {}
    total_bytes = 0
    total_stars = 0
    
    for repo in repos_data.get('nodes', []):
        total_stars += repo.get('stargazerCount', 0)
        for edge in repo.get('languages', {}).get('edges', []):
            lang_name = edge['node']['name']
            size = edge['size']
            language_bytes[lang_name] = language_bytes.get(lang_name, 0) + size
            total_bytes += size

    top_langs = []
    if total_bytes > 0:
        language_percentages = {lang: round((size / total_bytes) * 100, 1) for lang, size in language_bytes.items()}
        top_langs = sorted(language_percentages.items(), key=lambda x: x[1], reverse=True)[:3]

    while len(top_langs) < 3:
        top_langs.append(("N/A", 0))

    total_commits = data.get('contributionsCollection', {}).get('totalCommitContributions', 0)

    CACHE["data"] = (top_langs, total_repos, total_commits, total_stars)
    CACHE["timestamp"] = current_time

    return CACHE["data"]

@app.route('/api/stats')
def github_stats_svg():
    top_langs, total_repos, total_commits, total_stars = get_github_data()
    
    
    template_data = {
        "lang_1_name": top_langs[0][0], "lang_1_percent": top_langs[0][1],
        "lang_2_name": top_langs[1][0], "lang_2_percent": top_langs[1][1],
        "lang_3_name": top_langs[2][0], "lang_3_percent": top_langs[2][1],
        "stat_1_title": "Repos", "stat_1_value": total_repos,
        "stat_2_title": "Commits", "stat_2_value": total_commits,
        "stat_3_title": "Stars", "stat_3_value": total_stars,
    }

    svg_content = render_template('dealer.svg', **template_data)
    
    response = make_response(svg_content)
    response.content_type = 'image/svg+xml'
    response.headers['Cache-Control'] = 'public, max-age=14400'
    
    return response

if __name__ == '__main__':
    app.run(debug=True)