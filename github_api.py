import requests

# Твои данные
GITHUB_TOKEN = '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'
GITHUB_USERNAME = 'ARIIVIDERCHII'

query = """
{
  user(login: "%s") {
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
      nodes {
        name
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
              color
            }
          }
        }
      }
    }
  }
}
""" % GITHUB_USERNAME

url = 'https://api.github.com/graphql'
headers = {
    'Authorization': f'bearer {GITHUB_TOKEN}'
}

def fetch_and_process_stats():
    response = requests.post(url, json={'query': query}, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        repos = data['data']['user']['repositories']['nodes']
        
        # Словари для хранения статистики
        language_bytes = {}
        total_bytes = 0
        
        # Собираем байты со всех репозиториев
        for repo in repos:
            for edge in repo['languages']['edges']:
                lang_name = edge['node']['name']
                size = edge['size']
                
                if lang_name in language_bytes:
                    language_bytes[lang_name] += size
                else:
                    language_bytes[lang_name] = size
                
                total_bytes += size
                
        # Переводим в проценты и сортируем по убыванию
        language_percentages = {}
        if total_bytes > 0:
            for lang, size in language_bytes.items():
                percent = (size / total_bytes) * 100
                language_percentages[lang] = round(percent, 2)
                
            # Сортировка словаря от большего к меньшему
            sorted_stats = dict(sorted(language_percentages.items(), key=lambda item: item[1], reverse=True))
            
            print("--- Твоя статистика языков ---")
            for lang, percent in sorted_stats.items():
                print(f"{lang}: {percent}%")
                
            return sorted_stats
        else:
            print("Репозитории пусты или нет данных о языках.")
            return {}
            
    else:
        print(f"Ошибка запроса: {response.status_code}")
        return {}

if __name__ == "__main__":
    fetch_and_process_stats()