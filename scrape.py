import requests, json, re, sys
from bs4 import BeautifulSoup

sys.setrecursionlimit(4000)

main_url_list = [
    "https://www.airlinepilotforums.com/major/",
    "https://www.airlinepilotforums.com/cargo/",
    "https://www.airlinepilotforums.com/military/"
]

major_sub_forum_list = [
    'https://www.airlinepilotforums.com/alaska/',
    'https://www.airlinepilotforums.com/allegiant/',
    'https://www.airlinepilotforums.com/american/',
    'https://www.airlinepilotforums.com/delta/',
    'https://www.airlinepilotforums.com/frontier/',
    'https://www.airlinepilotforums.com/hawaiian/',
    'https://www.airlinepilotforums.com/jetblue/',
    'https://www.airlinepilotforums.com/southwest/',
    'https://www.airlinepilotforums.com/spirit/',
    'https://www.airlinepilotforums.com/sun-country/',
    'https://www.airlinepilotforums.com/united/'
]

cargo_sub_forum_list = [
    'https://www.airlinepilotforums.com/atlas-polar/',
    'https://www.airlinepilotforums.com/fedex/',
    'https://www.airlinepilotforums.com/kalitta-companies/',
    'https://www.airlinepilotforums.com/ups/'
]


def write_json_to_file(json_object, thread_url, cur_page, log_error=False):
    if "https://www.airlinepilotforums.com/major/" in thread_url:
        sub_directory = "/Major"
    elif "https://www.airlinepilotforums.com/cargo/" in thread_url:
        sub_directory = "/Cargo"
    elif "https://www.airlinepilotforums.com/military/" in thread_url:
        sub_directory = "/Military"
    elif any(sub_forum_url in thread_url
             for sub_forum_url in cargo_sub_forum_list):
        sub_directory = "/Cargo"
    elif any(sub_forum_url in thread_url
             for sub_forum_url in major_sub_forum_list):
        sub_directory = "/Major"
    else:
        sub_directory = ""

    if cur_page == 1:
        file_name = thread_url[thread_url.rfind('/') + 1:-5]
    else:
        file_name = thread_url[thread_url.rfind('/') + 1:thread_url.rfind('-')]

    if log_error:
        file_name = f"__ERROR-LOG__{file_name}.json"
    else:
        file_name = f"{file_name}.json"
    file_path = f"JSON{sub_directory}/{file_name}"

    # Open the file in write mode
    with open(file_path, "w") as f:
        # Write the JSON object to the file
        json.dump(json_object, f, indent=4)

    print(f"Saved JSON object to '{file_path}'")


def is_not_sticky_thread(thread):
    try:
        thread_icon_selector = ".right > .inlineimg"
        return "Sticky Thread" != thread.select(
            thread_icon_selector)[0].attrs["alt"]
    except IndexError:
        return True


def scrape_thread(thread_url, thread_title, cur_page, messages_json={}):
    try:
        response = requests.get(thread_url)
        # Check if last page has already been reached.
        if response.url != thread_url:
            write_json_to_file(messages_json, thread_url, cur_page)
            return messages_json

        print(f"Scraping thread: '{thread_url}'")
        cur_html = response.content.decode("windows-1250")
        soup = BeautifulSoup(cur_html, 'html.parser')

        page_count_selector = ".pagenav > .vbmenu_control"
        one_page_thread = soup.select(page_count_selector) == []
        if not one_page_thread:
            page_count = int(
                soup.select(page_count_selector)[0].text.split("of ")[1])
        else:
            page_count = 1
        print(f"Page '{cur_page}' of '{page_count}'\n")

        post_selector = ".tpost"
        messages_array = []
        for post in soup.select(post_selector):
            timestamp_selector = ".trow-group > .trow > .tcell"
            timestamp_text = post.select(
                timestamp_selector)[0].getText().lstrip().rstrip()
            if timestamp_text != "":
                message_selector = ".trow-group > .trow"
                message_text = str(
                    post.select(message_selector)[1].select(".tcell")
                    [1]).split("<!-- message -->")[1].split(
                        "<!-- / message -->")[0].split(
                            "</div>")[-2].lstrip().rstrip()

                message_text = message_text.replace("<br/>",
                                                    "").lstrip().rstrip()
                if ("<label>Quote:</label>" in message_text
                        and len(message_text.split(">")) > 1):
                    message_text = message_text.split(">")[1].lstrip()
                if ("post_message" in message_text
                        and len(message_text.split(">")) > 1):
                    message_text = message_text[message_text.index(">") +
                                                1:].lstrip()
                message_text = re.sub(r"<[^>]*>", "", message_text)
                messages_array.append({
                    "timestamp": timestamp_text,
                    "message_text": message_text
                })
        # print(f"messages_array: '{messages_array}'")
        messages_json[f"{cur_page}"] = messages_array
        if cur_page == 1:
            next_page_url = f"{thread_url[:-5]}-{cur_page+1}{thread_url[-5:]}"
        else:
            last_hyphen_index = thread_url.rfind('-')
            next_page_url = f"{thread_url[:last_hyphen_index+1]}{cur_page+1}{thread_url[-5:]}"

        scrape_thread(next_page_url, thread_title, cur_page + 1, messages_json)
    except Exception as e:
        print(f"Exception: {e}")
        write_json_to_file({"Exception": f"{e}"},
                           thread_url,
                           cur_page,
                           log_error=True)
        return cur_page


def scrape_forum(forum_url, cur_page):
    response = requests.get(forum_url)

    # Check if last page has already been reached.
    if response.url != forum_url:
        return 0

    print(f"Scraping Forum: '{forum_url}'")
    print(f"response.apparent_encoding: '{response.apparent_encoding}'\n")
    if response.apparent_encoding != "windows-1250":
        raise Exception(
            f"\n\tEncoding mismatch : response.apparent_encoding \"{response.apparent_encoding}\" != \"windows-1250\""
        )
    cur_html = response.content.decode("windows-1250")
    soup = BeautifulSoup(cur_html, 'html.parser')

    thread_selector = "#threadslist > .trow-group > .trow.text-center"
    for thread in soup.select(thread_selector):
        if is_not_sticky_thread(thread):
            thread_title_selector = ".text-left > div > h4 > a"
            thread_title = thread.select(thread_title_selector)[0].getText()
            thread_url = thread.select(thread_title_selector)[0].attrs["href"]
            print("#" * 100)
            print(f"thread_title: '{thread_title}'")
            try:
                scrape_thread(thread_url,
                              thread_title,
                              cur_page=1,
                              messages_json={"thread_url": thread_url})
            except Exception as e:
                print(f"Exception: {e}")
                # proceed_in = input("Continue?")
                # if proceed_in.lower() != "y":
                #     exit(-1)
            print("#" * 100)

    last_forward_slash_index = forum_url.rfind("/")
    next_page_url = f"{forum_url[:last_forward_slash_index+1]}index{cur_page+1}.html"
    scrape_forum(next_page_url, cur_page + 1)


def main():
    print(f"main_url_list: '{main_url_list}'\n")

    for main_url in main_url_list:
        scrape_forum(main_url, 1)

        print(f"\nGetting sub-forums for URL: '{main_url}'")
        cur_html = requests.get(main_url).text
        soup = BeautifulSoup(cur_html, 'html.parser')

        # Get links to all Sub-Forums
        sub_forum_url_list = []
        sub_forum_link_selector = "#main-content > .tbox > .trow-group > .trow > .text-left > div > h2 > a"
        for link in soup.select(sub_forum_link_selector):
            sub_forum_url_list.append(link.attrs['href'])
        print(sub_forum_url_list)
        for sub_forum_url in sub_forum_url_list:
            scrape_forum(sub_forum_url, cur_page=1)


if __name__ == "__main__":
    main()
