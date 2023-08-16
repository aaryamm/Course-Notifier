from bs4 import BeautifulSoup
import requests


class Course:
    def __init__(self, crn: str, term: str):
        if len(str(crn)) != 5 or not crn.isdigit():
            raise ValueError(f'{crn} is not a valid CRN.')
        self.crn = crn
        self.term = term
        self.url = f'https://oscar.gatech.edu/bprod/bwckschd.p_disp_detail_sched?term_in={self.term}&crn_in={self.crn}'
        header = self.fetch_header()
        self.name = header.split('-')[0].strip()
        self.code = header.split('-')[2].strip()
        self.section = header.split('-')[3].strip()
        self.users = set()
        self.status = None
        self.data = None

    def fetch_header(self):
        with requests.get(self.url) as page:
            soup = BeautifulSoup(page.content, 'html.parser')
            headers = soup.find_all('th', class_="ddlabel")
            if len(headers) == 0:
                raise ValueError(f'{self.crn} is not a valid CRN.')
            return headers[0].getText()

    def fetch_data(self):
        with requests.get(self.url) as page:
            soup = BeautifulSoup(page.content, 'html.parser')
            table = soup.find('caption', string='Registration Availability').find_parent('table')
            if len(table) == 0:
                raise ValueError(f'{self.crn} is not a valid CRN.')
            self.data = [int(info.getText()) for info in table.findAll('td', class_='dddefault')]

    def update_state(self):
        if self.data is None:
            self.fetch_data()
        old_status = self.status
        # TODO: Write logic to update state.
        if old_status is None:
            return False
        return old_status != self.status
    
    def add_user(self, user):
        self.users.add(user)

    def remove_user(self, user):
        self.users.remove(user)
