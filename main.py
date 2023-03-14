import os
import sys
import json
import time
import datetime
from ftplib import FTP


import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By


sys.dont_write_bytecode = True
sys.dont_write_bytecode = True
sys.dont_write_bytecode = True


URL = "https://app.acessorias.com/respdptos.php?geraR&fieldFilters=Atv_S,Dpt_8,Dpt_2,Dpt_1,Dpt_20,Dpt_3&modo=VNT"
USERAGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.5304.63 Safari/537.36"
PATH = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Crawler')
COOKIE_FILE = "cookie.txt"
OUTFILE = 'data.json'
LOGFILE = 'log.csv'
EMAIL = "atendimento@patrimoniumcontabilidade.com.br"
FTP_PATH = 'ftp.patrimoniumcontabilidade.com.br'



def rename_ftp_file(ftp, filename):
    try:
        file_exists = False
        for f in ftp.nlst():
            if f == filename:
                file_exists = True
                break
        
        if file_exists:
            ftp.rename(filename, filename + '.bak')
            return True
        else:
            return False
    except Exception as e:
        #print(e)
        return False

def send_ftp(filename, filepath):
    try:
        ftp = FTP(FTP_PATH)
        ftp.login(user=EMAIL, passwd=']6GI;Q1ZFX$YL!G')
        rename_ftp_file(ftp, filename)
        with open(filepath, 'rb') as f:
            ftp.storbinary('STOR {}'.format(filename), f)

        ftp.quit()
        return True
    except Exception as e:
        #print(e)
        return False


def get_cookie():
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")

        browser = webdriver.Chrome(chrome_options=options)
        if browser:
            browser.get("https://app.acessorias.com/index.php")
            time.sleep(3)
            username = browser.find_element(by=By.NAME, value="mailAC")
            password = browser.find_element(by=By.NAME, value="passAC")

            if username and password:

                username.send_keys(EMAIL)
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
        
        return False

    except Exception as e:
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
        log = dict()
        qtd_try = 0
        data = False
        
        log['date'] = datetime.datetime.now().strftime('%d/%m/%Y')
        log['time'] = datetime.datetime.now().strftime('%H:%M:%S')

        # Lê arquivo de cookies
        cookie = read_file(os.path.join(PATH, COOKIE_FILE))

        # Caso o arquivo não exista, cria ele com vazio
        if not cookie:
            write_file(' ', os.path.join(PATH, COOKIE_FILE))
            cookie = ' '

        log['session'] = 'A sessao ainda e valida'
        # Verifica se a requisição foi bem sucedida, caso contrario renova os cookies e tenta 3 vezes
        for i in range(4):
            response = get_html(URL, cookie)
            if not response:
                log['session'] = 'A sessao expirou'
                cookie = get_cookie()
                write_file(cookie, os.path.join(PATH, COOKIE_FILE))
            else:
                data = response.text
                break

        log['companies'] = ''
        # Continua caso a requisição tenha sido bem sucedida
        if data:
            lista_empresas = work_html(data)
            if lista_empresas:
                json_empresas = json.dumps(lista_empresas)
                resp = write_file(json_empresas, os.path.join(PATH, OUTFILE))
                if resp:
                    if send_ftp(OUTFILE, os.path.join(PATH, OUTFILE)):
                        log['message'] = 'O arquivo foi gerado e enviado com sucesso!'
                        log['status'] = '1'
                    else:
                        log['message'] = 'O arquivo foi gerado, mas não foi enviado!'
                        log['status'] = '0'

                    log['companies'] = '{}'.format(len(lista_empresas))
                else:
                    log['message'] = 'Falha ao tentar gerar o arquivo de dados!'
                    log['status'] = '0'
            else:
                log['message'] = 'Falha ao tentar extrair os dados!'
                log['status'] = '0'
        else:
            log['message'] = "Falha na requisição!"
            log['status'] = '0'

        #   Grava os logs em um arquivo
        header_log = 'Status; Data; Hora; Sessao; Mensagem; Empresas;\n'

        log_text = '{}; {}; {}; {}; {}; {};\n'.format(log['status'], log['date'], log['time'], log['session'], log['message'], log['companies'])

        log_file = read_file(os.path.join(PATH, LOGFILE))
 
        if log_file:
            log_text = log_file + log_text
        else:
            log_text = header_log + log_text
        
        write_file(log_text, os.path.join(PATH, LOGFILE))
        send_ftp(LOGFILE, os.path.join(PATH, LOGFILE))
        
        
    except Exception as e:
        print('Ocorreu um erro:\n{}'.format(e))
