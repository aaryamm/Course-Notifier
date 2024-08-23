from __future__ import annotations
import requests
from collections.abc import Awaitable, MutableSet, Set
from typing import Optional
from dataclasses import dataclass
from enum import Enum

from bs4 import BeautifulSoup


@dataclass
class CourseInfo:
    crn: str
    term: str
    name: str
    code: str
    section: str
    url: str


@dataclass
class CourseStatus:
    seats: int
    taken: int
    vacant: int
    waitlist: WaitlistStatus

    @dataclass
    class WaitlistStatus:
        seats: int
        taken: int
        vacant: int


class Course:
    
    ## Static Definitions
    class _State(Enum):
        CLOSED = 0
        OPEN = 1
    
    ## Public Interface

    def __init__(
        self,
        crn: str,
        term: str,
        waitlist_notif: Awaitable[Course],
        seat_notif: Awaitable[Course],
        initial_users: Optional[Set[str]] = None,
    ):
        self._init_vars()
        self._info = self._create_course_info(crn, term)
        self._waitlist_notifier = waitlist_notif
        self._seat_notifier = seat_notif

        if initial_users is not None:
            self._users = initial_users

    def __str__(self) -> str:
        c = self._info
        s = self._status

        out = ''
        if c is not None:
            out += f'CRN {c.crn}: {c.code} "{c.name}"'

        if s is not None:
            out += f'''
            Vacant Seats: {s.vacant}/{s.seats} 
            Vacant Waitlist Seats: {s.waitlist.vacant}/{s.waitlist.seats}'''

        return out

    def add_user(self, user):
        self._users.add(user)

    def has_user(self, user) -> bool:
        return user in self._users

    def remove_user(self, user):
        self._users.remove(user)

    def user_mentions(self) -> str:
        return "".join(self._users)

    def crn(self):
        return self._info.crn

    async def update(self):
        '''Updates state and sends notifications'''

        self._update_status()

        # State transitions
        if (
            self._waitlist_state == self._State.CLOSED
            and self._status.waitlist.vacant > 0
        ):
            # waitlist just opened
            await self._waitlist_notifier(self)
            self._waitlist_state = self._State.OPEN

        elif (
            self._waitlist_state == self._State.OPEN
            and self._status.waitlist.vacant <= 0
        ):
            # waitlist just closed
            self._waitlist_state = self._State.CLOSED

        if self._seat_state == self._State.CLOSED and self._status.vacant > 0:
            # course just opened
            await self._seat_notifier(self)
            self._seat_state = self._State.OPEN

        elif self._seat_state == self._State.OPEN and self._status.vacant <= 0:
            # course just closed
            self._seat_state = self._State.CLOSED

    ## Private Members
    
    def _init_vars(self):
        self._info: CourseInfo = None
        self._status: CourseStatus = None
        self._users: MutableSet[str] = set()
        self._waitlist_notifier: Awaitable[Course]
        self._seat_notifier: Awaitable[Course]
        self._waitlist_state: self._State = self._State.CLOSED
        self._seat_state: self._State = self._State.CLOSED


    def _update_status(self):
        self._status = self._fetch_update(self._info)

    ## Helper methods

    @staticmethod
    def _create_course_info(crn: str, term: str) -> CourseInfo:
        '''Fetches course info from the web'''

        if len(str(crn)) != 5 or not crn.isdigit():
            raise ValueError(f'{crn} is not a valid CRN.')

        url = f'https://oscar.gatech.edu/bprod/bwckschd.p_disp_detail_sched?term_in={term}&crn_in={crn}'

        with requests.get(url) as page:
            print(page)
            # Find header using soup
            soup = BeautifulSoup(page.content, 'html.parser')
            headers = soup.find_all('th', class_="ddlabel")

            # Ensure header/course exists
            if len(headers) == 0:
                raise ValueError(f'Could not find CRN {crn}.')

            # Parse into useful data
            data = headers[0].getText().split('-')

            return CourseInfo(
                crn=crn,
                term=term,
                url=url,
                name=data[0].strip(),
                code=data[2].strip(),
                section=data[3].strip(),
            )

    @staticmethod
    def _fetch_update(info: CourseInfo) -> CourseStatus:
        '''Fetches course status from the web'''

        with requests.get(info.url) as page:
            # Find table using soup
            soup = BeautifulSoup(page.content, 'html.parser')
            table = soup.find(
                'caption', string='Registration Availability'
            ).find_parent('table')

            # Ensure table/course exists
            if len(table) == 0:
                raise ValueError(f'Could not find CRN {info.crn}.')

            # Parse table
            data = [
                int(info.getText()) for info in table.findAll('td', class_='dddefault')
            ]

            # Just in case
            if len(data) < 6:
                raise ValueError(f'Error loading data for CRN {info.crn}.')

            # Map parsed table to data class
            return CourseStatus(
                seats=int(data[0]),
                taken=int(data[1]),
                vacant=int(data[2]),
                waitlist=CourseStatus.WaitlistStatus(
                    seats=int(data[3]), taken=int(data[4]), vacant=int(data[5])
                ),
            )
