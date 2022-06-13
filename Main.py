import pprint
import os
import json
import time
from dataclasses import dataclass

import pandas as pd
from bs4 import BeautifulSoup
"""THIS MAIN CRAWLER"""
SearchMachines = {"Yahoo": {"url": "https://search.yahoo.com",
                            "cookie": '//button[@name="agree"]',
                            "searchfield": "#yschsp"
                            },
                  "Bing": {"url": "https://www.bing.com",
                           "cookie": None,
                           "searchfield": '#sb_form_q'
                           },
                  "Google": {"url": "https://www.google.at",
                             "cookie": '//button[@id="L2AGLb"]',
                             "searchfield": 'input[aria-label="Suche"]'
                             },
                }
@dataclass
class LongListProduction:
    def __init__(self, keywords):
        self.keywords = keywords

    ignore_domains = ["https://cc.bingj.com",
                      "https://www.youtube.com",
                      "https://video.search.yahoo.com"
                      ]
    def main(self):
        result = {}
        for key in SearchMachines:
            self.driver(key, SearchMachines[key], result=result)
        return result

    def driver(self, searchmachine, definitions, result):
        print("-----------------------")
        print(searchmachine)
        print("-----------------------")
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.firefox.launch(headless=False)
            page = browser.new_page()
            page.goto(url=definitions["url"], wait_until="networkidle")
            self.accept_cookies(page, xpath=definitions["cookie"])
            for keyword in self.keywords:
                print(f"fetch: {keyword}")
                if keyword not in result.keys():
                    result[keyword] = {"Google": None, "Bing": None, "Yahoo": None}

                content = self.search(page, keyword, xpath=definitions["searchfield"])
                if searchmachine =="Yahoo":
                    keyword_result = self.parse_yahoo(content)
                elif searchmachine == "Bing":
                    keyword_result = self.parse_bing(content)
                else:
                    keyword_result = self.parse_google(content)
                result[keyword][searchmachine] = keyword_result
                time.sleep(1)
            browser.close()




    def accept_cookies(self, page, xpath):
        if xpath:
            locator = page.locator(xpath)
            locator.click()

    def search(self, page, keyword, xpath):
        page.fill(xpath, '')
        page.type(xpath, keyword)
        page.keyboard.press('Enter')
        time.sleep(5)
        content = page.content()
        return content


    def check_for_inored_domains(self, link):
        for ig in self.ignore_domains:
            if ig in link:
                return True
        return False

    def parse_google(self, content):
        soup = BeautifulSoup(content, "lxml")
        keyword_result =[]
        mylist = soup.find_all("div", {"class": "yuRUbf"})
        rank = 1
        for item in mylist:
            link = item.find("a", href=True)
            if link and self.check_for_inored_domains(link["href"]) == False:
                #print(f"{rank}  |  {link['href']}")
                keyword_result.append({"rank": rank, "link": link["href"]})
                rank += 1

        return keyword_result

    def parse_bing(self, content):
        soup = BeautifulSoup(content, "lxml")
        keyword_result = []
        my_list = soup.find_all("li", {"class":  "b_algo"})
        rank = 1
        for item in my_list:
            link = item.find("cite").text
            if link and self.check_for_inored_domains(link) is False:
                keyword_result.append({"rank": rank, "link": link})
                rank += 1
        return keyword_result

    def parse_yahoo(self, content):

        keyword_result = []
        soup = BeautifulSoup(content, 'lxml')
        ol = soup.find("ol", {"class": "reg searchCenterMiddle"})
        my_list = ol.find_all("li")
        rank = 1
        for item in my_list:
            link = item.find("a", href=True)
            if link and self.check_for_inored_domains(link["href"]) is False:
                #print(f"rank: {rank}, link: {link['href']}")
                keyword_result.append({"rank": rank, "link": link["href"]})
                rank += 1
        return keyword_result

if __name__ == '__main__':

    """Read keywords"""
    with open("Keywords.txt", "r") as f:
        kw = f.read()
    kw = kw.split(",")
    keywords = [k.strip() for k in kw]
    file_exists = os.path.exists("json_res.json")
    print(f"File exists: {file_exists}")
    if not file_exists:
        run = LongListProduction(keywords)
        res_dict = run.main()
        with open("json_res.json", "w") as f:
            f.write(json.dumps(res_dict))

    with open("json_res.json", "r") as f:
        main_data = json.loads(f.read())
    #pprint.pprint(main_data)
    table = []
    for keyword in main_data:
        #print(keyword)
        for seachtool in main_data[keyword]:
            for res in main_data[keyword][seachtool]:

                new_dic = {"seachtool": seachtool, "keyword": keyword}
                new_dic["link"] = res["link"]
                new_dic["rank"] = res["rank"]
                table.append(new_dic)



    df = pd.DataFrame(data=table, columns=[c for c in table[0]])
    print(df)
    df.to_excel("longlist.xlsx", index=False)
