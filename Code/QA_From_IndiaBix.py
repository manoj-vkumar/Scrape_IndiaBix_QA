from bs4 import BeautifulSoup
### Read URL - HTTP
import urllib
### Read URL - HTTPS
from urllib.request import Request, urlopen
import pymongo
import re
        

### Global variables
no_content = ''
json_names_qa = ['question', 'options', 'answer', 'answer_explanation']
json_names_q_options = ['option_name', 'option_value']

### Get Soup of given URL
def get_soup_for_http(url, is_https):
    try:
        if is_https:
            ### Read URL - HTTPS website
            hdr = {'User-Agent': 'Mozilla/5.0'}
            req = Request(url, headers = hdr)
            html = urlopen(req)
            # html = requests.get(url).text
            return BeautifulSoup(html, "html.parser")
        else:
            ### Read URL - HTTP website
            html = urllib.request.urlopen(url).read()
            return BeautifulSoup(html, "html.parser")
    except Exception as e:
        print("get_soup : ", e)
        return None

### Get Soup of given path
def get_soup_from_path(file_path):
    try:
        ### Read from file
        # file_path = "d:/Projects/NLP/ScrapContentFromWebsites/Data/Website.HTML"
        with open(file_path, encoding = "utf-8") as f:
            html = f.read()
            return BeautifulSoup(html, 'html.parser')
    except Exception as e:
        print("get_soup : ", e)
        return None

### Connect mongo db
def connect_mongo_db(port, client, db):
    try:
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        mydb = myclient[client]
        mycol = mydb[db]
        return mycol
    except Exception as e:
        print("connect_mongo_db : ", e)
        return None

### Insert into db
def insert_into_db(db, json):
    try:
        port = 27017
        client = 'IndiaBix'
        mycol = connect_mongo_db(port, client, db)
        # print(json)
        result = mycol.insert_many(json)
        print("result.. ", result, '\n')
    except Exception as e:
        print("insert_into_db : ", e)

### Assign - empty json
def return_empty_json(json_names):
    try:
        json_qa = {}
        if len(json_names) > 0:
            for json_name in json_names:
                json_qa[json_name] = ''
            return json_qa
        else:
            return ''
    except Exception as e:
        print("assign_json_empty : ", e)
        return ''

### Scrape - question
def scrape_question(html):
    try:
        return html.find('td', {'class': 'bix-td-qtxt'}).find('p').get_text().strip()
    except Exception as e:
        print("scrape_question : ", e)
        return ''

### Scrape - question options
def scrape_question_options(html):
    try:
        options = []
        options_tag_table = html.find('table', {'class': 'bix-tbl-options'})
        options_tag_tr = options_tag_table.find_all('tr')
        for option_tag in options_tag_tr:
            if option_tag is not None:
                option_td = option_tag.findNext('td').extract()
                if option_td is not None:
                    option_name = option_td.get_text().replace('.', '').strip()
                option_td = option_tag.findNext('td')
                if option_td is not None:
                    option_value = option_td.get_text().strip()
                options.append({ 'option_name': option_name, 'option_value': option_value })
        return options
    except Exception as e:
        print("scrape_question_options : ", e)
        return return_empty_json(json_names_q_options)

### Scrape - answer
def scrape_answer(html, options):
    try:
        q_answer_option_name = html.find('div', {'class': 'bix-div-answer mx-none'}).findNext('p').find_all('span')[1].get_text().strip()
        q_answer = {}
        for option in options:
            if option['option_name'] == q_answer_option_name:
                q_answer = {'option_name': option['option_name'], 'option_value': option['option_value']}
                break
        return q_answer
    except Exception as e:
        print("scrape_answer : ", e)
        return return_empty_json(json_names_q_options)

### Scrape - answer explanation
def scrape_answer_explanation(html):
    try:
        return html.find('div', {'class': 'bix-ans-description'}).get_text().strip()
    except Exception as e:
        print("scrape_answer_explanation : ", e)
        return ''

### Scrape - question, options and answer from container
def scrape_qa(table_qa):
    try:
        question = scrape_question(table_qa)
        options = scrape_question_options(table_qa)
        q_answer = scrape_answer(table_qa, options)
        answer_explanation = scrape_answer_explanation(table_qa)

        ### Define a json
        return { 'question': question, 'options': options, 'answer': q_answer, 'answer_explanation': answer_explanation }
    except Exception as e:
        print("scrape_qoae : ", e)
        return return_empty_json(json_names_qa)

### Scrape - question, options, answer and answer explanation
def get_qa_from_container(soup):
    try:
        json_qa = []
        for table_qa in soup.find_all('table', {'class': 'bix-tbl-container'}):
            try:
                if table_qa is not None:
                    json_qa.append(scrape_qa(table_qa))
            except Exception as e:
                print("table_qa : ", e)
        # print(json_qa, '\n')
        return json_qa
    except Exception as e:
        print("get_qa_from_container : ", e)
        return []

### Scrape - question, options, answer and answer explanation and insert into db
def scrape_insert_qa(primary_url, page_url, db):
    try:
        ### Get soup
        url = primary_url +'/'+ page_url
        soup = get_soup_for_http(url, True)
        ### Get qa
        json_qa = get_qa_from_container(soup)
        ### Insert into db
        if len(json_qa) > 0:
            insert_into_db(db, json_qa)

        condition = True
        while condition:
            page_container = soup.find('div', {'class', 'mx-pager-container'})
            if page_container is not None:
                current_span = page_container.find('span', {'class': 'mx-pager-current'})
                if current_span is not None:
                    next_page = current_span.findNext('a')
                    if next_page is not None:
                        if next_page.findNext('span', {'class': 'mx-pager-no'}) is not None:
                            next_page_url = next_page.get('href')
                            ### Get soup
                            url = primary_url +'/'+ next_page_url
                            soup = get_soup_for_http(url, True)
                            ### Get qa
                            json_qa = get_qa_from_container(soup)
                            ### Insert into db
                            if len(json_qa) > 0:
                                insert_into_db(db, json_qa)
                        else:
                            condition = False
                            break
                    else:
                        condition = False
                        break
                else:
                    condition = False
                    break
            else:
                condition = False
                break
    except Exception as e:
        print("scrape_insert_qa : ", e)
        return return_empty_json(json_names_qa)

### Scrape - questions sections
def scrape_question_section(primary_url, qa_section, qa_tag):
    try:
        ### Get soup
        url = primary_url +'/'+ qa_section +'/'+ qa_tag
        soup = get_soup_for_http(url, False)
        topics_containers = soup.find_all('div', {'class': 'div-topics-index'})
        for topics_container in topics_containers:
            topics = topics_container.find_all('li')
            for topic in topics:
                if topic is not None:
                    topic = topic.findNext('a')
                    if topic is not None:
                        topic = topic.get('href')
                        if topic is not None:
                            for topic_split in (topic_split for topic_split in topic.split('/') if topic_split is not ''):
                                topic = topic_split
                            topic = topic.replace('/', '')
                            print('qa_section: '+ qa_section +' topic : '+ topic)
                            page_url = qa_section +'/'+ topic
                            db = qa_section.replace('-', '_') +'_'+ topic.replace('-', '_')
                            # print(primary_url +'/'+ page_url, ' ', db)
                            scrape_insert_qa(primary_url, page_url, db)

    except Exception as e:
        print("scrape_question_section : ", e)

### Scrape - questions section list
def scrape_question_section_list(primary_url):
    try:
        qa_section = 'aptitude'
        qa_tag = 'questions-and-answers'
        ### Get soup
        soup = get_soup_for_http(primary_url, False)
        qa_section_containers = soup.find_all('ul', {'class': 'ques-ans'})
        for qa_section_container in qa_section_containers:
            qa_sections = qa_section_container.find_all('li')
            for qa_section in qa_sections:
                if qa_section is not None:
                    qa_section = qa_section.findNext('a')
                    if qa_section is not None:
                        qa_section = qa_section.get('href')
                        if qa_section is not None:
                            if qa_tag in qa_section:
                                for qa_section_split in (qa_section_split for qa_section_split in qa_section.split('/') if qa_section_split is not ''):
                                    topic = qa_section_split
                                qa_section = qa_section.replace(qa_tag, '').replace('/', '')
                                scrape_question_section(primary_url, qa_section, qa_tag)

    except Exception as e:
        print("scrape_question_section_list : ", e)

### define a main funtion
def main():
    try:
        primary_url = 'https://www.indiabix.com'
        
        scrape_question_section_list(primary_url)
    except Exception as e:
        print("main : ", e)

### Call main
main()