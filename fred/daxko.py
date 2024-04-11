from __future__ import annotations


# response = requests.get("https://members.daxko.com/10009?branchId=3ba37a66ae8a4da0ac087b854816bebe")
# soup = BeautifulSoup(response.content, "html.parser")
# search_input_element = soup.find(attrs={"data-reactid": "8463"})


def get_open_pools():
    return ['Indoor Pool', 'Complex Lap Pool']
