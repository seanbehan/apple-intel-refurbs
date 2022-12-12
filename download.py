import pandas as pd
import matplotlib.pyplot as plt

from lxml.html import fromstring
from requests import get
from datetime import datetime

now = datetime.now()
url = 'https://www.apple.com/shop/refurbished/mac'
headers = ['date', 'time', 'url', 'text', 'price', 'ram', 'hd']

def download_detail_page(row):
    row['date'] = now.strftime('%Y-%m-%d')
    row['time'] = now.strftime('%I:%M %p')
    row['url'] = 'https://apple.com' + row['path']

    doc_ = fromstring(get(row['url']).text)
    price = [el for el in doc_.xpath('//div[@class="rf-pdp-currentprice"]/text()')][0]
    ram,hd = [el.strip() for el in doc_.xpath('//div[contains(@class, "rc-pdsection-mainpanel")]/div[@class="para-list"]/p/text()')[3:5]]

    row['price'] = price
    row['ram'] = ram
    row['hd'] = hd

    return row

doc = fromstring(get(url).text)

''' create dataframe from links and download details ''' 
df = (
    pd.DataFrame([
      {'text': a.text, 'path': a.get('href')} 
      for a in doc.xpath('//a') if 'shop/product' in a.get('href')
    ], columns=headers)
    .query("text.str.contains('intel', case=False)")
    .query("text.str.contains('book', case=False)")
    .query("text.str.contains('16')")
    .apply(download_detail_page, axis=1)
)

df.to_csv('products.csv', index=False)
df[headers].to_csv('historical.csv', index=False, header=False, mode='a')

''' read historical prices and plot ''' 
df_ = (
    pd.read_csv('historical.csv', names=headers)
    .assign(
        price = lambda x: pd.to_numeric(
            x.price.str.replace(r'[$\,]', '', regex=True),
            errors='coerce'
        )
    )
)


fig,ax = plt.subplots(figsize=(12,8))
ax.set(title='Mean price over time', ylabel='Price', xlabel='Date')
means = (df_.groupby('date')['price'].mean().reset_index(name='price'))
ax.bar(means.date.values, means.price.values)
fig.savefig('prices.jpg')


''' make markdown text for readme '''
text = '''


![Status badge](https://github.com/seanbehan/apple-intel-refurbs/actions/workflows/python-app.yml/badge.svg)


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
