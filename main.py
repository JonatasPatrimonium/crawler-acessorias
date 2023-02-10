import json
import time

from selenium import webdriver
from selenium.webdriver.common.by import By

import requests
from bs4 import BeautifulSoup

URL = "https://app.acessorias.com/respdptos.php?geraR&fieldFilters=Atv_S,Dpt_8,Dpt_2,Dpt_1,Dpt_20,Dpt_3&modo=VNT"
USERAGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.5304.63 Safari/537.36"
COOKIE_FILE = "cookie.txt"
OUTFILE = 'data.json'  # arquivo de saida de dados
INFILE = 'ResponsaveisDptos.xls'  # arquivo de entrada de dados


def get_cookie():
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")

        browser = webdriver.Chrome(chrome_options=options)
        browser.get("https://app.acessorias.com/index.php")
        time.sleep(3)
        username = browser.find_element(by=By.NAME, value="mailAC")
        password = browser.find_element(by=By.NAME, value="passAC")

        username.send_keys("atendimento@patrimoniumcontabilidade.com.br")
        password.send_keys("#Patri2020")

        time.sleep(2)
        browser.find_element(by=By.CLASS_NAME, value="btn-enviar").click()
        time.sleep(5)

        cookies = browser.get_cookies()
        final_cookie = ''

        for cookie in cookies:
            final_cookie += '{}={};'.format(cookie['name'], cookie['value'])

        browser.close()
        return final_cookie


    except Exception as e:
        print(e)
        return False


def write_file(data, file):
    try:
        with open(file, 'wt') as outfile:
            outfile.write(data)

        return True
    except Exception as e:

        return False


def read_file(file):
    try:
        with open(file, 'rt') as outfile:
            data = outfile.read()

        return data

    except Exception as e:
        return False


def get_html(url, cookie):
    header = {"User-Agent": USERAGENT, "Cookie": cookie}

    try:
        response = requests.post(url, headers=header)
        if response.status_code == 200:
            if response.text.find("expirada") != -1:
                return False

            return response

        else:
            return False

    except:
        return False


# função que trabalha o HTML para conversão
def work_html(html):
    lista = []  # Lista de empresas
    titulo_rep = []  # Lista dos titulos de representantes

    # Extrai todas as tags 'tr' do html
    try:
        soup = BeautifulSoup(html, 'html.parser')
        tr_list = soup.find_all('tr')

        for tr in tr_list:
            tr_text = str(tr)
            # Extrai todas as tags 'td' contidas em 'tr' referentes aos titulos dos responsaveis
            tds_titulo = tr.find_all('td', {'rowspan': '2'})
            for td_titulo in tds_titulo:
                titulo = str(td_titulo.text)
                titulo = titulo.replace('\xa0', '')
                titulo_rep.append(titulo)

            if tr_text.find("rowspan") == -1 and tr_text.find("<strong>") == -1:

                # Extrai todas as tags 'td' contidas em 'tr' referentes ao conteudo
                tr_soup = BeautifulSoup(tr_text, 'html.parser')
                td_list = tr_soup.find_all('td')
                i_td = 0
                responsaveis = dict()
                nome = ''
                id = ''
                for i, td in enumerate(td_list):
                    td_str = str(td)
                    dicionario = dict()
                    # Armazena o nome dos responsaveis em um dicinario (responsaveis) dentro do objeto empresa
                    if td_str.find("colspan") == -1:
                        responsaveis[titulo_rep[i_td]] = td.text
                        i_td += 1
                        if i_td >= 16:
                            i_td = 0

                    # Armazena o nome e o id (cnpj) no objeto empresa
                    elif td_str.find('align="left"') == -1:
                        nome = td_str.replace(
                            '<td colspan="2" style="width:30%;">', '')
                        fim_nome = nome.find('[')
                        nome = nome[:fim_nome - 1]
                        id = td.small.text

                if id:
                    dicionario['id'] = id
                    dicionario['nome'] = nome
                    dicionario['responsaveis'] = responsaveis
                    lista.append(dicionario)

        return lista
    except:
        return False


if __name__ == '__main__':
    try:
        ops_sim = ['sim', 'SIM', 'Sim', 's', 'S', 'Yes',
                   'yes', 'y', 'Y', 'SIm', 'siM', 'sIM', 'sIm']
        print('[    WEB CRAWLER - ACESSORIAS    ]\n\n')

        while True:

            data = False
            op = ''

            print(
                '[      Iniciando a captura de dados...     ]\n\nDeseja usar um arquivo local? [ Padrão: NÃO ]')
            op = input('SIM (S) ou NÃO (N): ')

            if op in ops_sim:

                while not data:

                    file_name = input(
                        'Relatorio de Responsáveis [ Padrão: {} ]\nInsira o nome do arquivo: '.format(INFILE)) or INFILE
                    data = read_file(file_name)

            else:

                cookie = read_file(COOKIE_FILE)

                if not cookie:
                    write_file(' ', COOKIE_FILE)
                    cookie = ' '

                while not data:

                    print('[    Realizando a requisição...     ]')
                    response = get_html(URL, cookie)

                    if not response:
                        print(
                            '[    Sessão expirada!    ]\n\n[      Renovando os Cookies - Aguarde...      ]\n')
                        cookie = get_cookie()
                        write_file(cookie, COOKIE_FILE)
                        continue

                    data = response.text

            if data:
                print('[    Extraindo dados...  ]')
                lista_empresas = work_html(data)
                if lista_empresas:
                    print('[    Gerando arquivo de dados...    ]')
                    json_empresas = json.dumps(lista_empresas)
                    resp = write_file(json_empresas, OUTFILE)
                    if resp:
                        print('[    Arquivo {} gerado com sucesso!  ]\n[    EMPRESAS LISTADAS: {}   ]'.format(
                            OUTFILE, len(lista_empresas)))
                    else:
                        print('Falha ao tentar gerar o arquivo de dados!')
                else:
                    print('Falha ao tentar extrair os dados!')
            else:
                print('Falha ao tentar realizar a requisição!')

            print('Deseja reiniciar o programa? [ Padrão: NÃO ]')
            fim = input('SIM (S) ou NÃO (N): ')
            if fim in ops_sim:
                continue
            else:
                break

    except KeyboardInterrupt:
        print('\n\nPrograma finalizado!')

    except Exception as e:
        print('Ocorreu um erro:\n{}'.format(e))

    print('[    FIM! :)    ]')