import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json

# Load proxy addresses from proxies.txt
with open('proxies.txt', 'r') as f:
    PROXY_LIST = [line.strip() for line in f if line.strip()]

# Load user-agent strings from user_agents.txt
with open('user_agents.txt', 'r') as f:
    USER_AGENTS = [line.strip() for line in f if line.strip()]

### CHANGE THIS AS NEEDED ##################################################
MAX_CONCURRENT_REQUESTS = 50  # Number of concurrent requests ##############
### CHANGE THIS AS NEEDED ##################################################

proxy_index = 0
ua_index = 0

def get_next_proxy():
    global proxy_index
    proxy = PROXY_LIST[proxy_index]
    proxy_index = (proxy_index + 1) % len(PROXY_LIST)
    return proxy

def get_next_user_agent():
    global ua_index
    user_agent = USER_AGENTS[ua_index]
    ua_index = (ua_index + 1) % len(USER_AGENTS)
    return user_agent

async def fetch_reddit_profile(session, semaphore, username):
    url = f"https://www.reddit.com/user/{username}/"
    headers = {"User-Agent": get_next_user_agent()}

    async with semaphore:
        async with session.get(url, headers=headers, proxy=get_next_proxy()) as response:
            text = await response.text()
    soup = BeautifulSoup(text, 'html.parser')
    return soup

def extract_data(soup):
    user_data = {}
    post_karma_elements = soup.find_all('faceplate-number', {'number': True})
    if post_karma_elements:
        user_data['post_karma'] = post_karma_elements[0]['number']
        user_data['comment_karma'] = post_karma_elements[1]['number']

    cake_day_element = soup.find('faceplate-date', {'ts': True})
    if cake_day_element:
        user_data['cake_day'] = cake_day_element['ts']

    avatar_element = soup.find('faceplate-img', {'alt': True, 'src': True})
    if avatar_element:
        user_data['user_avatar'] = avatar_element['src']

    subreddits_moderating = soup.find_all('a', {'href': True, 'class': 'flex items-center justify-start'})
    subreddit_details = []
    for subreddit in subreddits_moderating:
        subreddit_name_element = subreddit.find('span', {'class': 'text-12 font-bold text-neutral-content'})
        if subreddit_name_element:
            details = {'subreddit': subreddit_name_element.text}
            member_count_element = subreddit.find('faceplate-number')
            if member_count_element:
                details['members'] = member_count_element['number']
            subreddit_details.append(details)
    user_data['subreddits_moderating'] = subreddit_details

    return user_data

async def main():
    # Load list of usernames from usernames.txt
    with open('usernames.txt', 'r') as f:
        usernames = [line.strip() for line in f if line.strip()]

    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        tasks = [fetch_reddit_profile(session, semaphore, username) for username in usernames]
        results = await asyncio.gather(*tasks)

    user_data_list = [extract_data(soup) for soup in results]

    # Save to Output.txt
    with open('Output.txt', 'w', encoding='utf-8') as file:
        for data in user_data_list:
            file.write(json.dumps(data, ensure_ascii=False, indent=4))
            file.write("\n\n")  # Separate entries for readability

if __name__ == '__main__':
    asyncio.run(main())