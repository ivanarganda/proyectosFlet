crypto_date_list =[]
crypto_name_list=[]
crypto_sigla_list=[]
crypto_symbol_list =[]
crypto_market_cap_list=[]
crypto_price_list =[]
crypto_circulating_supply_list=[]
crypto_pct_1hr_list=[]
crypto_pct_24hr_list=[]
crypto_pct_7day_list=[]



def scraper_data(date):
    url_base = 'https://coinmarketcap.com'+ date
    response = requests.get(url_base)
    soup = BeautifulSoup(response.text, 'html.parser')
    tr = soup.find_all('tr' , class_ ='cmc-table-row')
    count = 0
    for row in tr:
        if count== 10:
            break
        

        #Intenta asignar una fecha, la cual traemos de las varible scrape_date_lista , de lo contrario pone None
        try:
            crypto_date = date
            
        except AttributeError:
            crypto_date = None
            
        #Intenta asignar un nombre extraido de la tabla, de lo contrario pone None
        try:
            name_column = row.find('td', class_= 'cmc-table__cell cmc-table__cell--sticky cmc-table__cell--sortable cmc-table__cell--left cmc-table__cell--sort-by__name')
            crypto_name = name_column.find('a', class_= 'cmc-table__column-name--name cmc-link').text.strip()
        except AttributeError:
            crypto_name = None

        #Intenta asignar un sigla extraido de la tabla, de lo contrario pone None
        try:
            sigla_column = row.find('td', class_ ='cmc-table__cell cmc-table__cell--sticky cmc-table__cell--sortable cmc-table__cell--left cmc-table__cell--sort-by__name')
            sigla = sigla_column.find('a', class_class="cmc-table__column-name--symbol cmc-link").text.strip()
            
        except AttributeError:
            sigla = None

        try:
            crypto_symbol = row.find('td', class_ ='cmc-table__cell cmc-table__cell--sortable cmc-table__cell--left cmc-table__cell--sort-by__symbol').text.strip()
                        
        except AttributeError:
            crypto_symbol = None

        
        try:
            crypto_market_cap = row.find('td', class_ ='cmc-table__cell cmc-table__cell--sortable cmc-table__cell--right cmc-table__cell--sort-by__market-cap').text.strip()
                        
        except AttributeError:
            crypto_market_cap = None

        try:
            crypto_price = row.find('td', class_ ='cmc-table__cell cmc-table__cell--sortable cmc-table__cell--right cmc-table__cell--sort-by__price').text.strip()
                        
        except AttributeError:
            crypto_price = None

        try:
            crypto_circulating_supply = row.find('td', class_ ='cmc-table__cell cmc-table__cell--sortable cmc-table__cell--right cmc-table__cell--sort-by__circulating-supply').text.strip()
                        
        except AttributeError:
            crypto_circulating_supply = None

        try:
            crypto_pct_1hr = row.find('td', class_ ='cmc-table__cell cmc-table__cell--sortable cmc-table__cell--right cmc-table__cell--sort-by__percent-change-1-h').text.strip()
                        
        except AttributeError:
            crypto_pct_1hr = None

        try:
            crypto_pct_24hr = row.find('td', class_ ='cmc-table__cell cmc-table__cell--sortable cmc-table__cell--right cmc-table__cell--sort-by__percent-change-24-h').text.strip()
                        
        except AttributeError:
            crypto_pct_24hr = None

        try:
            crypto_pct_7d = row.find('td', class_ ='cmc-table__cell cmc-table__cell--sortable cmc-table__cell--right cmc-table__cell--sort-by__percent-change-7-d').text.strip()
                        
        except AttributeError:
            crypto_pct_7d = None

        crypto_date_list.append(crypto_date)
        crypto_name_list.append(crypto_name)
        crypto_sigla_list.append(sigla)
        crypto_symbol_list.append(crypto_symbol)
        crypto_market_cap_list.append(crypto_market_cap)
        crypto_price_list.append(crypto_price)
        crypto_circulating_supply_list.append(crypto_circulating_supply)
        crypto_pct_1hr_list.append(crypto_pct_1hr)
        crypto_pct_24hr_list.append(crypto_pct_24hr)
        crypto_pct_7day_list.append(crypto_pct_7d)
        
     
from datetime import datetime
date_format = '%Y%m%d'

star_date = datetime.strptime(scrape_date_lista[0].split('/')[-2],date_format).strftime('%Y-%m-%d')
end_date = datetime.strptime(scrape_date_lista[-1].split('/')[-2],date_format).strftime('%Y-%m-%d')
print(f'Hay {len(scrape_date_lista)} registros , Desde: {star_date} Hasta: {end_date}')


for i in range(len(scrape_date_lista)):
    scraper_data(scrape_date_lista[i])
    print(f'Completado {i+1} de un total de {len(scrape_date_lista)}' )
        
        
        
df=pd.DataFrame()

df['Date'] = crypto_date_list
df['Name'] = crypto_name_list
df['Symbol'] = crypto_symbol_list
df['Market_Cap'] = crypto_market_cap_list
df['Price'] = crypto_price_list
df['Circulating_supply'] = crypto_circulating_supply_list
df['%_1hs'] = crypto_pct_1hr_list
df['%24_hs'] = crypto_pct_24hr_list
df['%_7_days'] = crypto_pct_7day_list

df
    


df['Date'] = pd.to_datetime(df['Date'].str.split('/').str[-2], format='%Y-%m-%d')

df['Market_Cap']




df['Circulating_supply'] =df['Circulating_supply'].str.replace(r'[^\d.,]', '', regex=True)
df['Circulating_supply'] =df['Circulating_supply'].str.replace(',', '')
df['Circulating_supply']