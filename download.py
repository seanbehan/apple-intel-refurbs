import pandas as pd
from lxml.html import fromstring
from requests import get
import matplotlib.pyplot as plt
from datetime import datetime

now = datetime.now()
url = 'https://www.apple.com/shop/refurbished/mac'

doc = fromstring(get(url).text)
historical_headers = ['date', 'time', 'url', 'text', 'price', 'ram', 'hd']

def download_detail_page(row):
    row['date'] = now.strftime('%Y-%m-%d')
    row['time'] = now.strftime('%I:%M %p')
    url = row['url'] = 'https://apple.com' + row['path']

    doc_ = fromstring(get(url).text)
    price = [el for el in doc_.xpath('//div[@class="rf-pdp-currentprice"]/text()')][0]
    ram,hd = [el.strip() for el in doc_.xpath('//div[contains(@class, "rc-pdsection-mainpanel")]/div[@class="para-list"]/p/text()')[3:5]]

    row['price'] = price
    row['ram'] = ram
    row['hd'] = hd

    return row

df = (
    pd.DataFrame([
      {'text': a.text, 'path': a.get('href')} 
      for a in doc.xpath('//a') if 'shop/product' in a.get('href')
    ], columns=historical_headers)
    .query("text.str.contains('intel', case=False)")
    .query("text.str.contains('book', case=False)")
    .query("text.str.contains('16')")
    .apply(download_detail_page, axis=1)
)


df.to_csv('products.csv', index=False)

df[historical_headers].to_csv('historical.csv', index=False, header=False, mode='a')

historical = (
    pd.read_csv('historical.csv', names=historical_headers)
    .assign(
        price = lambda x: pd.to_numeric(
            x.price.str.replace(r'[$\,]', '', regex=True),
            errors='coerce'
        )
    )
)

means = (historical.groupby('date')['price'].mean().reset_index(name='price'))

fig,ax = plt.subplots(figsize=(12,8))
ax.set(title='Mean price over time', ylabel='Prices', xlabel='Date')

ax.bar(means.date.values, means.price.values)

fig.savefig('prices.jpg')

text = '''

# 16 Inch Refurbished Macbook Pros

This page updates once an hour with the latest refurbished products from Apple.com. 

![Prices over time](prices.jpg?raw=true "Prices")

'''

if len(df) < 1:
    text += '# No products at the moment '

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
