
import pandas as pd
from lxml.html import fromstring
from requests import get

url = 'https://www.apple.com/shop/refurbished/mac'

doc = fromstring(get(url).text)



'''
given a url try to download the detail page
its an unordered list so we are guessing the location for similar products
'''
def download_detail_page(row):
    try:
        url = row['url']
        doc2 = fromstring(get(url).text)
        price = [el for el in doc2.xpath('//div[@class="rf-pdp-currentprice"]/text()')][0]
        ram,hd = [el.strip() for el in doc2.xpath('//div[contains(@class, "rc-pdsection-mainpanel")]/div[@class="para-list"]/p/text()')[3:5]]
        row['price'] = price
        row['ram'] = ram
        row['hd'] = hd

        return row
    except:
        return None

'''
steps:
1. make frame of title and path. note, apple decorates page w/javascript, so have to look at href values
2. reduce list to only 16-inch intel macbooks
3. download detail page for ram and harddrive info
4. publish to csv file 
'''
df = (
    pd.DataFrame([
      {'text': a.text, 'url': a.get('href')} 
      for a in doc.xpath('//a') if 'shop/product' in a.get('href')
    ])
    .query("text.str.contains('intel', case=False)")
    .query("text.str.contains('book', case=False)")
    .query("text.str.contains('16')")
    .assign(
        url = lambda x: 'https://apple.com' + x.url.astype(str),
        # details = lambda x: x.url.apply(download_detail_page),
    )
    .apply(download_detail_page, axis=1)
)

df.to_csv('products.csv', index=False)


'''
make markdown readme
'''

text = '''
# 16 Inch Refurbished Macbook Pros

This page updates once an hour with the latest refurbished products from Apple.com. 

'''
for row in df.to_dict('records'):
    text += f'''
#### {row['text']}
- {row['price']}
- {row['ram']}
- {row['hd']}
- [View on Apple.com]({row['url']})
    '''

with open('README.md', 'w') as f:
    f.write(text)
    
# finito!    
