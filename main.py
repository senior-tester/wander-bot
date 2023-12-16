from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert
import logging
import random
from time import sleep
from faker import Faker


logging.basicConfig(filename='runtime.log', encoding='utf-8', level=logging.INFO)

def browser():
    options = Options()
    options.page_load_strategy = 'none'
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    driver.set_page_load_timeout(15)
    return driver


def read_file():
    with open('words.txt', encoding='utf-8') as words_file:
        words = [word.strip('\n') for word in words_file.readlines()]
    return words


def write_file(lines):
    with open('words.txt', 'w', encoding='utf-8') as words_file:
        words_file.write('\n'.join(lines))


def find_site(driver, word):
    logging.info('-' * 20)
    logging.info(f'Запуск со словом {word}')
    sleep(2)
    driver.get('https://www.google.com/')
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, 'q')))
    input_field = driver.find_element(By.NAME, 'q')
    input_field.send_keys(word)
    input_field.submit()
    WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[jsname="UWckNb"]')))
    sleep(3)
    links = driver.find_elements(By.CSS_SELECTOR, '[jsname="UWckNb"]')
    while True:
        try:
            random.choice(links).click()
            break
        except (ElementClickInterceptedException, ElementNotInteractableException):
            sleep(1)
    return driver


def click_link_on_site(driver, word, domains):
    sleep(3)
    current_url = driver.current_url
    try:
        domain = current_url.split('/')[2].replace('www.', '')
    except IndexError:
        domain = 'na'
    logging.info(f'> {domain}')
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'a')))
    except TimeoutException:
        pass
    driver.execute_script("window.stop();")
    links = driver.find_elements(By.TAG_NAME, 'a')

    def is_ok_link(url: WebElement):
        domains.extend([domain, 'mailto:', 'tel:'])
        url = url.get_attribute('href')
        if url:
            for dom in domains:
                try:
                    if dom in url:
                        return False
                except TypeError:
                    print(dom, url, '\n', domains)
            return True
        return False

    try:
        use_links = list(filter(is_ok_link, links))
    except StaleElementReferenceException:
        use_links = []
    count = 0
    if use_links:
        while count < 15 and use_links:
            try:
                link = use_links.pop(random.randrange(len(use_links)))
                link.click()
                try:
                    WebDriverWait(driver, 3).until(EC.alert_is_present())
                    alert = Alert(driver)
                    alert.dismiss()
                except TimeoutException:
                    pass
                # sleep(3)

                tabs = driver.window_handles
                for tab in tabs[:-1]:
                    driver.switch_to.window(tab)
                    driver.close()
                driver.switch_to.window(driver.window_handles[0])
                WebDriverWait(driver, 5).until_not(EC.url_contains(domain))
                return True, domain
            except (ElementClickInterceptedException, ElementNotInteractableException, TimeoutException, StaleElementReferenceException) as err:
                count += 1
    driver.quit()
    print('Цикл завершен')
    print(f'Слово было: {word}')
    print(f'Последний домен: {domain}')
    sleep(3)
    print()
    print()
    return False, None


while True:
    try:
        fake = Faker('ru_RU')
        source = random.choice(['fake', 'file'])
        match source:
            case 'file':
                words = read_file()
                if words:
                    # logging.info(str(words))
                    keyword = words.pop(random.randrange(len(words)))
                    write_file(words)
                else:
                    keyword = fake.word()

            case _:
                keyword = fake.word()

        print(f'Начало цикла по слову: {keyword}')
        sleep(3)
        after_google = find_site(browser(), keyword)
        WebDriverWait(after_google, 10).until_not(EC.url_contains('google'))
        i = 0
        worked_domains = []
        while True:
            go, domain = click_link_on_site(after_google, keyword, worked_domains)
            worked_domains.append(domain)
            if not go:
                break

    except KeyboardInterrupt:
        print('Finished')
        break
    except TimeoutException:
        continue
