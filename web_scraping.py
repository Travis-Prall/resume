import time
import re
import random
from random import randint
from datetime import datetime as dt

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.action_chains import ActionChains

from selenium.common.exceptions import ElementClickInterceptedException, NoAlertPresentException

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

SEARCH_DICT = {
    "id": By.ID,
    "tag_name": By.TAG_NAME,
    "name": By.NAME,
    "link_text": By.LINK_TEXT,
    "partial_link_text": By.PARTIAL_LINK_TEXT,
    "css_selector": By.CSS_SELECTOR,
    "xpath": By.XPATH
}


class Webrip:

    ###########
    # UTILITY #
    ###########

    def get_element_dict(self, text_input=None, **kwargs):
        self.log("__function__: Getting Element", level='DEBUG')
        web_element_dict = dict()
        if text_input:
            web_element_dict['text_input'] = text_input
        for key, value in kwargs.items():
            if value is not None:
                web_element_dict[key] = value
        return web_element_dict

    # def set_log(self, object):
    #     self.log = object
    #     self.log("__function__: Setting log", level='DEBUG')

    # def set_options(self, headless=None, wait=False, name=None):

    #     self.headless = headless
    #     if wait is not False:
    #         self.wait = wait
    #     if name:
    #         self.app_name = name
    #     else:
    #         self.app_name = (__name__)

##########
# DRIVER #
##########

    def check_driver(self):
        self.log("__function__: Checking Driver", level='DEBUG')
        if self.driver:
            self.log("__function__: Driver is active", level='DEBUG')
        else:
            self.log(f"__function__: Driver is {self.driver}", level='DEBUG')
            self.get_driver()

    def get_driver(self):
        self.log("__function__: Getting Driver", level='DEBUG')
        # initialize options
        options = webdriver.ChromeOptions()
        # pass in headless argument to options
        if self.headless is True:
            self.log("__function__: Making Headless", level='DEBUG')
            options.add_argument('--headless')
        options.add_argument("--no-sandbox")
        options.add_argument("disable-notifications")
        options.add_argument("disable-infobars")
        # options.add_argument('--incognito')
        options.add_argument('user-data-dir=/home/seluser/userdata')
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0'
        )
        # options.add_argument("--disable-popup-blocking")
        # options.add_argument("--disable-gpu")
        # options.add_argument("--window-size=800,600")
        options.add_argument("--disable-dev-shm-usage")
        # initialize driver
        self.log("__function__: Making Driver", level='DEBUG')
        try:
            self.driver = webdriver.Remote(
                command_executor='http://hub:4444/wd/hub',
                options=options,
                desired_capabilities=DesiredCapabilities.CHROME)
            self.driver.implicitly_wait(20)
        except Exception as Error:
            self.log(Error, level='ERROR')
            self.driver = None

#########
# LOGON #
#########

    def get_login_name(self,
                       text_input=None,
                       id=None,
                       name=None,
                       link_text=None,
                       partial_link_text=None,
                       tag=None,
                       class_name=None,
                       data=None):
        self.log("__function__: Setting Login Name", level='DEBUG')
        if data:
            user = data
        else:
            user = self.get_element_dict(text_input,
                                         id=id,
                                         name=name,
                                         tag=tag,
                                         link_text=link_text,
                                         partial_link_text=partial_link_text,
                                         class_name=class_name)
        self.log(f"Setting user Name to {user}")
        return user

    def get_login_password(self,
                           text_input=None,
                           id=None,
                           name=None,
                           link_text=None,
                           partial_link_text=None,
                           tag=None,
                           class_name=None,
                           data=None):
        self.log("__function__: Setting Login Password", level='DEBUG')
        if data:
            password = data
        else:
            password = self.get_element_dict(
                text_input,
                id=id,
                name=name,
                link_text=link_text,
                partial_link_text=partial_link_text,
                tag=tag,
                class_name=class_name)
        return password

    def get_login_button(self,
                         text_input=None,
                         id=None,
                         name=None,
                         link_text=None,
                         partial_link_text=None,
                         tag=None,
                         class_name=None,
                         data=None):
        self.log("__function__: Setting Login Button", level='DEBUG')
        if data:
            button = data
        else:
            button = self.get_element_dict(text_input,
                                           id=id,
                                           name=name,
                                           link_text=link_text,
                                           partial_link_text=partial_link_text,
                                           tag=tag,
                                           class_name=class_name)
        return button

    def login(self, login_website=None, fresh=None, submit=True):
        self.log(f"__function__: Logging on {fresh=}", level='DEBUG')
        if login_website:
            self.login_website = login_website
        else:
            if self.login_website is None:
                self.website_close()
                raise KeyError
        try:
            self.check_driver()
            if fresh:
                self.driver.get(self.login_website)
            if self.login_name:
                element = self.input_text(self.login_name)
            else:
                self.log(f'Something went wrong with {self.login_name=}',
                         level='ERROR')
                self.screenshot(pic='error')
                raise KeyError

            self.log("Starting second round", level='DEBUG')
            if self.login_password:
                self.log('__function__: Inputting Login Password',
                         level='DEBUG')
                element = self.input_text(self.login_password)
            else:
                self.log(
                    f'__function__:Something went wrong with {self.login_password=}',
                    level='ERROR')
                self.screenshot(pic='error')
                raise KeyError

            if element and self.login_submit:
                self.log("__function__: Submitting Form", level='DEBUG')
                element.submit()
            else:
                self.log(f'__function__: No Submit {element=}', level='DEBUG')

            if self.login_button:
                self.log(
                    f'__function__: Pressing Login Button {self.login_button}',
                    level='DEBUG')
                self.click_link(data=self.login_button)
            else:
                self.log(
                    f'__function__: No log on button {self.login_button=}',
                    level='DEBUG')
            self.update_web()
        except Exception as Error:
            self.log(f"__function__: There was an {Error=}", level='ERROR')
            self.screenshot(pic='error')
            self.website_close()

#############
# FUNCTIONS #
#############

    def change_website(self, url, target=None):
        self.log(f'__function__: Getting website {url}', level='DEBUG')
        self.check_driver()

        try:
            self.log(f'__function__:Trying {url}', level='DEBUG')
            self.driver.get(url)
            self.title = self.driver.title
        except Exception as Error:
            self.log(Error)
            self.screenshot(pic='error')
        if self.login_trigger:
            if self.login_trigger in self.title:
                self.log(
                    f"self.log(f'__function__:log in Triggered {self.login_trigger} is in {self.title}"
                )
                self.login()
            else:
                self.update_web()
        else:
            self.update_web()

    def input_text(self, data):
        self.log(f"__function__: Inputting Text: {data}", level='DEBUG')
        element = self.get_element(**data)
        if element:
            self.log("__function__: Sending Keys", level='DEBUG')
            element.send_keys(data['text_input'])
            return element
        self.log(f"__function__: Something went wrong {element=}",
                 level='ERROR')
        self.screenshot(pic='error')
        return None

    def move_click(self, web_element):
        self.log("__function__: Moving to Element to click", level='DEBUG')
        ActionChains(
            self.driver).move_to_element(web_element).click().perform()

    def click_link(self, target=None, movement=None, data=None, **kwargs):
        self.log(f"__function__: Clicking Link: {kwargs}", level='DEBUG')
        if data:
            web_element = self.get_element(clickalbe=True, **data)
        else:
            web_element = self.get_element(clickalbe=True, **kwargs)
        # web_element.click()
        # self.update_web(target=target)
        if web_element:
            self.log("__function__: Got Link", level='DEBUG')
            try:
                if movement:
                    self.log("__function__: Moving to Link", level='DEBUG')
                    ActionChains(self.driver).move_to_element(
                        web_element).click().perform()
                else:
                    self.log("__function__: Clicking Link", level='DEBUG')
                    web_element.click()
            except ElementClickInterceptedException as Error:
                self.log(Error, level='ERROR')
                try:
                    self.handle_popup(msg=Error.msg, web_element=web_element)
                except Exception as Error:
                    self.log(Error, level='ERROR')
            except Exception as Error:
                self.log(f"Click failed {Error}", level='ERROR')
                self.screenshot(pic='error')
            self.update_web(target=target)
        else:
            self.log(f"__function__:    Something went wrong {web_element=}")
            return None

    def run_java_script(self, java):
        self.log(f"__function__: Running {java}", level='DEBUG')
        try:
            javascript = self.driver.execute_script(java)
        except Exception as e:
            self.log(e, level='ERROR')
            self.screenshot(pic='error')
        self.update_web()
        return javascript

    def get_table(self, header, body, table=None):
        self.log(f"__function__: Getting {table=} {header=} {body=}",
                 level='DEBUG')
        try:
            if table:
                all_table = self.get_element(**table)
                table_header = all_table.find_element_by_tag_name(header)
                table_body = all_table.find_element_by_tag_name(body)
                return table_header, table_body
            table_header = self.get_element(**header)
            table_body = self.get_element(**body)
            return table_header, table_body
        except Exception as e:
            self.log(e, level='ERROR')
            self.screenshot(pic='error')
            return None

    def get_element(self, wait=10, clickalbe=False, **kwargs):
        self.log(f"__function__: Getting element {kwargs}", level='DEBUG')
        self.check_driver()
        for key, value in kwargs.items():
            self.log(f"__function__: Checking {value=} for {key=}",
                     level='DEBUG')
            # search = key.upper()
            if key in SEARCH_DICT:
                if clickalbe is True:
                    try:
                        element = WebDriverWait(self.driver, wait).until(
                            EC.element_to_be_clickable(
                                (SEARCH_DICT[key], value)))
                        self.log(f"__function__: Returning {key} for {value}",
                                 level='DEBUG')
                        return element
                    except Exception as Error:
                        self.log(f"__function__: {key} failed {Error=}",
                                 level='ERROR')
                        self.screenshot(pic='error')
                else:
                    try:
                        element = WebDriverWait(self.driver, wait).until(
                            EC.presence_of_element_located(
                                (SEARCH_DICT[key], value)))
                        self.log(f"__function__: Returning {key} for {value}",
                                 level='DEBUG')
                        return element
                    except Exception as Error:
                        self.log(f"__function__: {key} failed {Error=}",
                                 level='ERROR')
                        self.screenshot(pic='error')
            else:
                self.log(f'__function__: {key} is not retrievable',
                         level='DEBUG')
        self.log('__function__: Something went wrong', level='ERROR')

    def update_web(self, wait=None, target=None):
        self.log('__function__: Updating Web Data', level='DEBUG')
        if wait is not None:
            self.log(f"__function__: waiting for {wait} seconds",
                     level='DEBUG')
            time.sleep(wait)
        elif self.wait is not None:
            wait = randint(5, 10)
            self.log(f"__function__: waiting for {wait} seconds",
                     level='DEBUG')
            time.sleep(wait)
        else:
            self.log(f'__function_: {wait=}', level='DEBUG')
        self.title = self.driver.title
        self.website = self.driver.current_url
        if target:
            if target in self.title:
                self.log(f"__function__: {target=} is in {self.title}",
                         level='DEBUG')
                self.screenshot()
            else:
                self.screenshot(pic='error')
        else:
            self.screenshot()
        self.log(f"__function__: {self.title=} at {self.website}",
                 level='DEBUG')

    def website_close(self):
        self.log("__function__: Closing Website", level='DEBUG')
        if self.driver is not None:
            self.log("__function__: Closing driver", level='DEBUG')
            try:
                self.driver.quit()
                self.driver = None
                self.title = None
                self.website = None
                self.log("__function__: driver closed", level='DEBUG')
            except Exception as Error:
                self.log(f'__function__: driver is {self.driver}{Error=}',
                         level='WARNING')

    def screenshot(self, pic='name'):
        self.log("__function__: Taking Picture", level='DEBUG')
        now = dt.now().strftime("%d-%b-%Y (%H:%M:%S.%f)")
        if pic == 'error':
            self.log("__function__: Error Message", level='DEBUG')
            file = f"/conf/screenshots/{now}_{self.scrap_app_name}_error_.png"
        else:
            file = f"/conf/screenshots/{self.scrap_app_name}.png"

        try:
            self.driver.save_screenshot(file)
            self.log("__function__: Saved a Screen Shot", level='DEBUG')
        except Exception as Error:
            self.log(f"__function__: Failed to save a screenshot {Error=}",
                     level='WARNING')

    def nap(self, duration='short'):
        self.log("__function__: Starting", level='DEBUG')
        if duration in ('m', 'micro', 'Micro'):
            number = round(random.uniform(0.25, 1.00), 2)
        elif duration in ('S', 'short', 'Short'):
            number = round(random.uniform(1.00, 5.00), 2)
        elif duration in ('M', 'medium', 'Medium'):
            number = round(random.uniform(5.00, 10.00), 2)
        elif duration in ('L', 'long', 'Long'):
            number = round(random.uniform(10.00, 30.00), 2)
        self.log(f"__function__: Napping for {number} seconds", level='DEBUG')
        time.sleep(number)
