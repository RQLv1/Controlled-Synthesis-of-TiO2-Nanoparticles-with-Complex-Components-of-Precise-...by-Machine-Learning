import requests
from bs4 import BeautifulSoup
import os
from tqdm import tqdm
import fitz
import re
import os
import shutil
import pytesseract
from PIL import Image
from tqdm import tqdm

##########################################pdf download############################
path = "F:\\liter_downloads\\"   
doi_path = ''
if os.path.exists(path) == False:
	os.mkdir(path)  
f = open(doi_path, "r", encoding="utf-8")  
head = {\
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'\
            }  
for line in tqdm(f.readlines()):
	line = line[:-1] 
	url = "https://www.sci-hub.wf/" + line + "#" 
	try:
		download_url = ""  
		r = requests.get(url, headers = head)
		r.raise_for_status()
		r.encoding = r.apparent_encoding
		soup = BeautifulSoup(r.text, "html.parser")
		try:
			if soup.iframe == None:  
				download_url = "https:" + soup.embed.attrs["src"]
			else:
				download_url = soup.iframe.attrs["src"]  
		except:
			continue
			
			
		# print(line + " is downloading...\n  --The download url is: " + download_url)
		download_r = requests.get(download_url, headers = head)
		download_r.raise_for_status()
		with open(path + line.replace("/","_") + ".pdf", "wb+") as temp:
			temp.write(download_r.content)
	except:
		with open("error.txt", "a+") as error:
			error.write(line + " occurs error!\n")
			if "https://" in download_url:
				error.write(" --The download url is: " + download_url + "\n\n")
	else:
		download_url = ""  
		# print(line + " download successfully.\n")
f.close()

##########################################pdf ocr############################

file_path = r'E:\Users\downloads' # PDF filepath
to_path = r'E:\Users\to_liter'
os.chdir(file_path)

flag_word_counts = {'Diameter': 0, 'Size': 0, 'Pore': 0, 'dimension': 0}
not_word_counts = {'Pore size': 0, 'Pore diameter': 0}

for file_name in tqdm(os.listdir()):
    source_file = os.path.join(file_path, file_name)

    try:          
        checkIM = r"/Subtype(?= */Image)"
        pdf = fitz.open(file_name)
        lenXREF = pdf.xref_length()
        
        flag = False
      
        for i in range(1, lenXREF):
            text = pdf.xref_object(i)
            isImage = re.search(checkIM, text)

            if not isImage:
                continue
           
            pix = fitz.Pixmap(pdf, i)
            pix.save('img.png')
                      
            img = Image.open('img.png').convert('RGB')
           
            text_2 = pytesseract.image_to_string(img, lang='eng')
            flag_words = ['Diameter', 'Size', 'Pore', 'dimension']
            not_words = ['Pore size', 'Pore diameter']

            for flag_word in flag_words:
                flag_word_counts[flag_word] += text_2.lower().count(flag_word.lower())

            for not_word in not_words:
                not_word_counts[not_word] += text_2.lower().count(not_word.lower())

            if any(flag_word.lower() in text_2.lower() for flag_word in flag_words) and any(not_word.lower() not in text_2.lower() for not_word in not_words):
                # print("Found 'Diameter' and 'Size' in PDF, but 'Pore' is not in the text.")
                flag = True
                pdf.close()
                shutil.move(source_file, to_path)
                # print(f'{file_name} move successfully')
                break    
            pix = None
  
        img.close()
        pdf.close()
        os.remove('img.png')

        if not flag:       
            continue         
                # os.remove(file_name)
                # print(f"No match found in {file_name}. Deleting the file.")
    except Exception as e:
        continue
            # print(f"Error processing {file_name}: {str(e)}")

print("Keyword Occurrences:")
for word, count in flag_word_counts.items():
    print(f"{word}: {count}")

print("Exclusion Word Occurrences:")
for word, count in not_word_counts.items():
    print(f"{word}: {count}")