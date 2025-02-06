import requests
import os
import time
import re
from DrissionPage import ChromiumPage, ChromiumOptions
from crossref_commons.retrieval import get_publication_as_json
els_api_key= ""

def journal_publisher(doi):

    try:
        publisher = get_publication_as_json(doi)['publisher']
        if 'elsevier' in publisher.lower():
        #     pdf_url='https://api.elsevier.com/content/article/doi/' + doi + '?view=FULL'
            return 'elsevier'# , pdf_url
        elif 'wiley' in publisher.lower():
                # pdf_url='https://onlinelibrary.wiley.com/doi/epdf/' + doi
                return 'wiley'# , pdf_url
        elif 'springer' in publisher.lower():
                # pdf_url= 'https://link.springer.com/content/pdf/' + doi + '.pdf'
                return 'springer'# , pdf_url
        elif 'rsc' in publisher.lower():        
                # pdf_url= crossref_commons.retrieval.get_publication_as_json(doi)['link'][0]['URL']
                return 'rsc'# , pdf_url
        elif 'informa' in publisher.lower():
                # pdf_url= crossref_commons.retrieval.get_publication_as_json(doi)['link'][0]['URL']
                return 'taylor & francis'# , pdf_url
        elif 'iop' in publisher.lower():
                # pdf_url= crossref_commons.retrieval.get_publication_as_json(doi)['link'][1]['URL']
                return 'iop'# , pdf_url
        elif 'aaas' in publisher.lower():
        #      pdf_url = 'https://pubs.acs.org/doi/epdf/' + doi
             return 'aaas'#,  pdf_url
        elif 'acs' in publisher.lower():
                # pdf_url = 'https://pubs.acs.org/doi/epdf/' + doi
                return 'acs'# , pdf_url
        else:
            return 'out of publishers' # []
    except Exception as e:
        print(e)
        pass 

    


def get_content(doi):
    co = ChromiumOptions().set_browser_path('C:\Program Files\Google\Chrome\Application\chrome.exe')
    page = ChromiumPage(addr_or_opts=co)
    experimental_keywords = ['experimental', 'materials and methods', 'experiment', 'experimental section', 'methods']
    if journal_publisher(doi) == 'springer':
        doi = doi.split('/')[-1]
        page.get(f'https://www.nature.com/articles/{doi}')
        time.sleep(3)  

        try:
            button = page('t:button@@text:Methods')
            if button:
                button.click()
                time.sleep(2)  
        except:
            content = "can not get content"

        try:
            content = page('css:.c-article-section#Sec[0-9]* h2:contains("Methods"), .c-article-section#methods').next().text
        except:
            try:
                section = page('css:.c-article-section:contains("Methods")')
                content = section.text
            except:
                try:
                    content = page('xpath://section[contains(.//h2, "Methods")]').text
                except:
                    content = "can not get content"

    elif journal_publisher(doi) == 'acs':
        page.get(f'https://pubs.acs.org/doi/full/{doi}')
        time.sleep(3) 

        content = ""
        try:
            for i in range(1, 6):  
                section = page(f'css:#sec{i}')
                if section:
                    title = section('css:h2').text.lower()
                    if any(keyword in title.lower() for keyword in experimental_keywords):
                        content = section.text
                        break
                    
            if not content:
                content = "can not get content"

        except Exception as e:
            # print(f"error: {e}")
            content = "can not get content"

    elif journal_publisher(doi) == 'wiley':
        page.get(f'https://onlinelibrary.wiley.com/doi/full/{doi}')
        time.sleep(3) 

        content = ""

        sections = page.eles('css:.article-section__title.section__title')
        for section in sections:
            title = section.text.lower()
            if any(keyword in title.lower() for keyword in experimental_keywords):
                content_section = section.next('css:.article-section__sub-content')
                if content_section:
                    content = content_section.text
                break

    elif journal_publisher(doi) == 'elsevier':
        def extract_sections(text):
            pattern = r'1\s+Introduction.*?(?:References|REFERENCES)'

            matches = re.search(pattern, text, re.DOTALL)

            if matches:
                matched_text = matches.group(0)
                sections = {}
                section_pattern = r'(\d+(?:\.\d+)?)\s+([^\d\n]+)'
                for match in re.finditer(section_pattern, matched_text):
                    number = match.group(1)
                    title = match.group(2).strip()
                    sections[number] = title
                return sections
            return None

        def extract_experimental_section(text, match_title, match_title_1):
            first_pos = text.find(match_title)
            if first_pos != -1:
                second_pos = text.find(match_title, first_pos + 1)
                if second_pos != -1:
                    text_from_second = text[second_pos:]
                    end_pos = text_from_second.find(match_title_1)
                    if end_pos != -1:
                        return text_from_second[:end_pos].strip()
            return None

        pdf_url = 'https://api.elsevier.com/content/article/doi/' + doi
        headers = {
            'X-ELS-APIKEY': els_api_key,
            'Accept': 'application/json'
        }

        try:
            response = requests.get(pdf_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                result = extract_sections(data['full-text-retrieval-response']['originalText'])
                match_title = ''
                match_title_1 = ''
                for number, title in result.items():
                    if '.' not in number:
                        if any(keyword in title.lower() for keyword in experimental_keywords):
                            match_title = number+ ' ' + title
                            match_title_1 = str(int(number) + 1)+ ' ' + result[str(int(number) + 1)]
                            # print(match_title)
                            # print(match_title_1)
                            break
                        
                if match_title and match_title_1:
                    content = extract_experimental_section(
                        data['full-text-retrieval-response']['originalText'],
                        match_title,
                        match_title_1
                    )

                if not content:
                    content = "can not get content"
            else:
                content = f"API requests fail，status code：{response.status_code}"
        except Exception as e:
            content = "can not get content"

    elif journal_publisher(doi) == 'rsc':
        page.get(f'https://doi.org//{doi}')
        time.sleep(3) 
        content = ""
        try:
            headings = page.eles('css:.h--heading2')
            for i, heading in enumerate(headings):
                if any(keyword in heading.text.lower() for keyword in experimental_keywords):
                    Headings = heading.nexts()
                    ele_p = []
                    for ele in Headings:
                        if ele.tag == 'p':
                            ele_p.append(ele)
                        if ele.tag == 'h2':
                            break
                    for section in ele_p:
                        content += section.text + "\n"
                    break
                
        except Exception as e:
            # print(f"error: {e}")
            content = "get content error"
    
    page.quit()
        
    sanitized_doi = doi.replace('/', '_')

    return content, sanitized_doi
