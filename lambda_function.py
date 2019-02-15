import sys

sys.path.append("/opt")

import json
import requests
from bs4 import BeautifulSoup as bs
from lxml import etree
import gzip
from io import StringIO

import logging
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import dateutil.tz
import urllib.parse

import os

# Login Function
def login_function(memno, password):
    bdgc_login_url = "https://www.bdgc.com.au/security/login.msp"
    bdgc_login_form_data = {
        'action': 'login',
        'user': memno,
        'password': password,
        'Submit': 'Login'
    }
    res = requests.post(url=bdgc_login_url, data=bdgc_login_form_data)
    return res.headers['Set-Cookie']

# Search And Book Function
def check_eventlist_function(event, comments):
    event_comments = event.find('div', attrs={'class': 'event-comments'})
    book_comments = event_comments.text.strip()
    if comments:
        for comment in comments:
            if comment:
                if book_comments.find(comment) >= 0:
                    return True
            else:
                if book_comments == '':
                    return True
    else:
        return True
    
    return False

def get_only_number(str):
    regex = re.compile("\d+$")
    number = regex.search(str).group()
    return number

# Search And Book Function
def get_book_eventid(cookie_info, after_days, comments):
    bdgc_eventlist_url = "https://www.bdgc.com.au/views/members/booking/eventList.xhtml"
    bdgc_header_data = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
        'Cookie': cookie_info
    }
    res = requests.get(url=bdgc_eventlist_url, headers=bdgc_header_data)
    soup = bs(res.text, 'html.parser')
    eventlist = soup.find('div', attrs={'class': 'event-list'})
    
    local_zone = dateutil.tz.gettz(os.environ["TZ"])
    date_after_eight_days = datetime.now(tz=local_zone)
    for day_no in range(0, int(after_days)):
        date_after_eight_days = date_after_eight_days + relativedelta(days=1)
    next_book_date = date_after_eight_days.strftime('%a%d %b')
        
    book_event = None
    book_date = ''
    for event in eventlist.find_all('div', attrs={'class': 'full'}):
        # Book Date
        event_date = event.find('span', attrs={'class': 'dateColumnClass'})
        if event_date.text:
            book_date = event_date.text
        
        # Book Status
        if next_book_date == book_date:
            event_staus = event.find('span', attrs={'class': 'eventStatusOpen'})
            if event_staus:
                if event_staus.text == 'OPEN':
                    book_valid = check_eventlist_function(event, comments)
                    if book_valid:
                        book_event = event
                        break
    
    if book_event:
        book_event_fixture = book_event.find('div', attrs={'class': 'fixture-icons'})
        book_event_a_href = book_event_fixture.find('a', href=True)['href']
        return get_only_number(book_event_a_href)
    
    return ''

def get_book_rowid(cookie_info, book_eventid):
    bdgc_book_url_prefix = "https://www.bdgc.com.au/members/bookings/open/event.msp?booking_event_id="
    bdgc_book_url_suffix = "&booking_resource_id=3000000"
    bdgc_book_url = bdgc_book_url_prefix + book_eventid + bdgc_book_url_suffix
    bdgc_header_data = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        'Cookie': cookie_info
    }
    
    book_row_result = {
        'row_id': '',
        'row_time': ''
    }
    res = requests.get(url=bdgc_book_url, headers=bdgc_header_data)
    soup = bs(res.text, 'html.parser')
    book_available_groups = soup.find_all('div', attrs={'class': 'available'})
    for book_group in book_available_groups:
        cells = book_group.find_all('div', attrs={'class': 'cell'})
        taken_cells = book_group.find_all('div', attrs={'class': 'cell-taken'})
        if len(taken_cells) == 0:
            book_rowid = get_only_number(book_group['id'])
            bdgc_block_book_url = "https://www.bdgc.com.au/members/Ajax?doAction=lockResource&bookingRowId=" + book_rowid + "&text"
            block_res = requests.get(url=bdgc_block_book_url, headers=bdgc_header_data)
            if block_res.status_code == 200:
                if block_res.text != 'false':
                    book_row_result['row_id'] = book_rowid
                    book_group_headers = book_group.find_all('div', attrs={'class': 'row-heading-inner'})
                    if book_group_headers:
                        book_group_headers_h3 = book_group.find('h3')
                        book_group_headers_h4 = book_group.find('h4')
                        book_row_result['row_time'] = book_group_headers_h3.text.strip() + " " + book_group_headers_h4.text.strip()
                    return book_row_result
    
    return book_row_result

def book_golf(cookie_info, book_eventid, book_rowid):
    bdgc_book_form_url_prefix = "https://www.bdgc.com.au/members/bookings/open/DefaultPartners.msp?booking_event_id="
    bdgc_book_form_url_suffix = "&booking_row_id="
    bdgc_book_form_url = bdgc_book_form_url_prefix + book_eventid + bdgc_book_form_url_suffix + book_rowid
    bdgc_header_data = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        'Cookie': cookie_info
    }
    res = requests.get(url=bdgc_book_form_url, headers=bdgc_header_data)
    soup = bs(res.text, 'html.parser')
    
    bdgc_auto_book_url = "https://www.bdgc.com.au/members/bookings/open/MakeBooking.msp?"
    bdgc_auto_book_url += "doAction=FAST_BOOK&booking_event_id=" + book_eventid + "&booking_row_id=" + book_rowid
    bdgc_auto_book_url += "&booking_group_id=&times_free="

    default_playing_group_form = soup.find('form', attrs={'name': 'defaultPlayingGroupForm'})
    auto_book_form = soup.find('form', attrs={'name': 'auto_book'})
    
    # BookLinkedEvent
    book_linked_event = default_playing_group_form.find('input', attrs={'name': 'bookLinkedEvent'})
    book_linked_event_val = {'bookLinkedEvent': ''}
    if book_linked_event:
        if book_linked_event['checked']:
            book_linked_event_val['bookLinkedEvent'] = 'y'
    bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_linked_event_val)
    
    # NumberOfHoles
    number_of_holes = default_playing_group_form.find('input', attrs={'name': 'numberOfHoles'})
    book_number_of_holes_val = {'numberOfHoles': ''}
    if number_of_holes:
        number_of_holes_val = number_of_holes.get('value')
        if number_of_holes_val:
            book_number_of_holes_val['numberOfHoles'] = number_of_holes_val
    bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_number_of_holes_val)
    
    # BackNineId
    back_nine_id = auto_book_form.find('input', attrs={'name': 'backNineId'})
    book_back_nine_id_val = {'backNineId': ''}
    if back_nine_id:
        back_nine_id_val = back_nine_id.get('value')
        if back_nine_id_val:
            book_back_nine_id_val['backNineId'] = back_nine_id_val
    bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_back_nine_id_val)
    
    # GroupName
    group_name = auto_book_form.find('input', attrs={'name': 'group_name'})
    book_group_name_val = {'group_name': ''}
    if group_name:
        group_name_val = group_name.get('value')
        if group_name_val:
            book_group_name_val['group_name'] = group_name_val
    bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_group_name_val)
    
    # Time
    book_time = auto_book_form.find('input', attrs={'name': 'time'})
    book_time_val = {'time': ''}
    if book_time:
        time_val = book_time.get('value')
        if time_val:
            book_time_val['time'] = time_val
    bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_time_val)
    
    # Title
    book_title = auto_book_form.find('input', attrs={'name': 'title'})
    book_title_val = {'title': ''}
    if book_title:
        title_val = book_title.get('value')
        if title_val:
            book_title_val['title'] = title_val
    bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_time_val)
    
    book_cells = 0
    ###### Record 0 ######
    # freeRecord.0.membership_number
    freerecode_0_mem_num = auto_book_form.find('input', attrs={'name': 'freeRecord.0.membership_number'})
    if freerecode_0_mem_num:
        book_cells = 1
        bdgc_auto_book_url += "&freeRecord.id=0&freeRecord.0.booking_record_id=0&freeRecord.0.booking_record_x_index=0"
        book_freerecode_0_mem_num_val = {'freeRecord.0.membership_number': ''}
        freerecode_0_mem_num_val = freerecode_0_mem_num.get('value')
        if freerecode_0_mem_num_val:
            book_freerecode_0_mem_num_val['freeRecord.0.membership_number'] = freerecode_0_mem_num_val
        bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_freerecode_0_mem_num_val)
    
    # freeRecord.0.full_name
    freerecode_0_full_name = auto_book_form.find('input', attrs={'name': 'freeRecord.0.full_name'})
    if book_cells >= 1:
        book_freerecode_0_full_name_val = {'freeRecord.0.full_name': ''}
        if freerecode_0_full_name:
            freerecode_0_full_name_val = freerecode_0_full_name.get('value')
            if freerecode_0_full_name_val:
                book_freerecode_0_full_name_val['freeRecord.0.full_name'] = freerecode_0_full_name_val
        bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_freerecode_0_full_name_val)
    
    # freeRecord.0.competition_round_type
    freerecode_0_compe_round_type = auto_book_form.find('input', attrs={'name': 'freeRecord.0.competition_round_type'})
    if book_cells >= 1:
        book_freerecode_0_compe_round_type_val = {'freeRecord.0.competition_round_type': ''}
        if freerecode_0_compe_round_type:
            freerecode_0_compe_round_type_val = freerecode_0_compe_round_type.get('value')
            if freerecode_0_compe_round_type_val:
                book_freerecode_0_compe_round_type_val['freeRecord.0.competition_round_type'] = freerecode_0_compe_round_type_val
        bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_freerecode_0_compe_round_type_val)
    
    ###### Record 1 ######
    # freeRecord.1.membership_number
    freerecode_1_mem_num = auto_book_form.find('input', attrs={'name': 'freeRecord.1.membership_number'})
    if freerecode_1_mem_num:
        book_cells = 2
        bdgc_auto_book_url += "&freeRecord.id=1&freeRecord.1.booking_record_id=1&freeRecord.1.booking_record_x_index=1"
        book_freerecode_1_membership_number_val = {'freeRecord.1.membership_number': ''}
        freerecode_1_mem_num_val = freerecode_1_mem_num.get('value')
        if freerecode_1_mem_num_val:
            book_freerecode_1_membership_number_val['freeRecord.1.membership_number'] = freerecode_1_mem_num_val
        bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_freerecode_1_membership_number_val)
    
    # freeRecord.1.full_name
    freerecode_1_full_name = auto_book_form.find('input', attrs={'name': 'freeRecord.1.full_name'})
    if book_cells >= 2:
        book_freerecode_1_full_name_val = {'freeRecord.1.full_name': ''}
        if freerecode_1_full_name:
            freerecode_1_full_name_val = freerecode_1_full_name.get('value')
            if freerecode_1_full_name_val:
                book_freerecode_1_full_name_val['freeRecord.1.full_name'] = freerecode_1_full_name_val
        bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_freerecode_1_full_name_val)
    
    # freeRecord.1.handicap
    freerecode_1_handicap = auto_book_form.find('input', attrs={'name': 'freeRecord.1.handicap'})
    if book_cells >= 2:
        book_freerecode_1_handicap_val = {'freeRecord.1.handicap': ''}
        if freerecode_1_handicap:
            freerecode_1_handicap_val = freerecode_1_handicap.get('value')
            if freerecode_1_handicap_val:
                book_freerecode_1_handicap_val['freeRecord.1.full_name'] = freerecode_1_handicap_val
        bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_freerecode_1_handicap_val)
    
    # freeRecord.1.gender_code
    freerecode_1_gender_code = auto_book_form.find('input', attrs={'name': 'freeRecord.1.gender_code'})
    if book_cells >= 2:
        book_freerecode_1_gender_code_val = {'freeRecord.1.gender_code': ''}
        if freerecode_1_gender_code:
            freerecode_1_gender_code_val = freerecode_1_gender_code.get('value')
            if freerecode_1_gender_code_val:
                book_freerecode_1_gender_code_val['freeRecord.1.gender_code'] = freerecode_1_gender_code_val
        bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_freerecode_1_gender_code_val)
    
    # freeRecord.1.golflink_number
    freerecode_1_golflink_number = auto_book_form.find('input', attrs={'name': 'freeRecord.1.golflink_number'})
    if book_cells >= 2:
        book_freerecode_1_golflink_number_val = {'freeRecord.1.golflink_number': ''}
        if freerecode_1_golflink_number:
            freerecode_1_golflink_number_val = freerecode_1_golflink_number.get('value')
            if freerecode_1_golflink_number_val:
                book_freerecode_1_golflink_number_val['freeRecord.1.golflink_number'] = freerecode_1_golflink_number_val
        bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_freerecode_1_golflink_number_val)
    
    # freeRecord.1.competition_round_type
    freerecode_1_compe_round_type = auto_book_form.find('input', attrs={'name': 'freeRecord.1.competition_round_type'})
    if book_cells >= 2:
        book_freerecode_1_competition_round_type_val = {'freeRecord.1.competition_round_type': ''}
        if freerecode_1_compe_round_type:
            freerecode_1_compe_round_type_val = freerecode_1_compe_round_type.get('value')
            if freerecode_1_compe_round_type_val:
                book_freerecode_1_competition_round_type_val['freeRecord.1.competition_round_type'] = freerecode_1_compe_round_type_val
        bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_freerecode_1_competition_round_type_val)
    
    ###### Record 2 ######
    # freeRecord.2.membership_number
    freerecode_2_mem_num = auto_book_form.find('input', attrs={'name': 'freeRecord.2.membership_number'})
    if freerecode_2_mem_num:
        book_cells = 3
        bdgc_auto_book_url += "&freeRecord.id=2&freeRecord.2.booking_record_id=2&freeRecord.2.booking_record_x_index=2"
        book_freerecode_2_membership_number_val = {'freeRecord.2.membership_number': ''}
        freerecode_2_mem_num_val = freerecode_2_mem_num.get('value')
        if freerecode_2_mem_num_val:
            book_freerecode_2_membership_number_val['freeRecord.2.membership_number'] = freerecode_2_mem_num_val
        bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_freerecode_2_membership_number_val)
    
    # freeRecord.2.full_name
    freerecode_2_full_name = auto_book_form.find('input', attrs={'name': 'freeRecord.2.full_name'})
    if book_cells >= 3:
        book_freerecode_2_full_name_val = {'freeRecord.2.full_name': ''}
        if freerecode_2_full_name:
            freerecode_2_full_name_val = freerecode_2_full_name.get('value')
            if freerecode_2_full_name_val:
                book_freerecode_2_full_name_val['freeRecord.2.full_name'] = freerecode_2_full_name_val
        bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_freerecode_2_full_name_val)
    
    # freeRecord.2.handicap
    freerecode_2_handicap = auto_book_form.find('input', attrs={'name': 'freeRecord.2.handicap'})
    if book_cells >= 3:
        book_freerecode_2_handicap_val = {'freeRecord.2.handicap': ''}
        if freerecode_2_handicap:
            freerecode_2_handicap_val = freerecode_2_handicap.get('value')
            if freerecode_2_handicap_val:
                book_freerecode_2_handicap_val['freeRecord.2.full_name'] = freerecode_2_handicap_val
        bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_freerecode_2_handicap_val)
    
    # freeRecord.2.gender_code
    freerecode_2_gender_code = auto_book_form.find('input', attrs={'name': 'freeRecord.2.gender_code'})
    if book_cells >= 3:
        book_freerecode_2_gender_code_val = {'freeRecord.2.gender_code': ''}
        if freerecode_2_gender_code:
            freerecode_2_gender_code_val = freerecode_2_gender_code.get('value')
            if freerecode_2_gender_code_val:
                book_freerecode_2_gender_code_val['freeRecord.2.gender_code'] = freerecode_2_gender_code_val
        bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_freerecode_2_gender_code_val)
    
    # freeRecord.2.golflink_number
    freerecode_2_golflink_number = auto_book_form.find('input', attrs={'name': 'freeRecord.2.golflink_number'})
    if book_cells >= 3:
        book_freerecode_2_golflink_number_val = {'freeRecord.2.golflink_number': ''}
        if freerecode_2_golflink_number:
            freerecode_2_golflink_number_val = freerecode_2_golflink_number.get('value')
            if freerecode_2_golflink_number_val:
                book_freerecode_2_golflink_number_val['freeRecord.2.golflink_number'] = freerecode_2_golflink_number_val
        bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_freerecode_2_golflink_number_val)
    
    # freeRecord.2.competition_round_type
    freerecode_2_compe_round_type = auto_book_form.find('input', attrs={'name': 'freeRecord.2.competition_round_type'})
    if book_cells >= 3:
        book_freerecode_2_competition_round_type_val = {'freeRecord.2.competition_round_type': ''}
        if freerecode_2_compe_round_type:
            freerecode_2_compe_round_type_val = freerecode_2_compe_round_type.get('value')
            if freerecode_2_compe_round_type_val:
                book_freerecode_2_competition_round_type_val['freeRecord.2.competition_round_type'] = freerecode_2_compe_round_type_val
        bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_freerecode_2_competition_round_type_val)
    
    ###### Record 3 ######
    # freeRecord.3.membership_number
    freerecode_3_mem_num = auto_book_form.find('input', attrs={'name': 'freeRecord.3.membership_number'})
    if freerecode_3_mem_num:
        book_cells = 4
        bdgc_auto_book_url += "&freeRecord.id=3&freeRecord.3.booking_record_id=3&freeRecord.3.booking_record_x_index=3"
        book_freerecode_3_membership_number_val = {'freeRecord.3.membership_number': ''}
        freerecode_3_mem_num_val = freerecode_3_mem_num.get('value')
        if freerecode_3_mem_num_val:
            book_freerecode_3_membership_number_val['freeRecord.3.membership_number'] = freerecode_3_mem_num_val
        bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_freerecode_3_membership_number_val)
    
    # freeRecord.3.full_name
    freerecode_3_full_name = auto_book_form.find('input', attrs={'name': 'freeRecord.3.full_name'})
    if book_cells >= 4:
        book_freerecode_3_full_name_val = {'freeRecord.3.full_name': ''}
        if freerecode_3_full_name:
            freerecode_3_full_name_val = freerecode_3_full_name.get('value')
            if freerecode_3_full_name_val:
                book_freerecode_3_full_name_val['freeRecord.3.full_name'] = freerecode_3_full_name_val
        bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_freerecode_3_full_name_val)
    
    # freeRecord.3.handicap
    freerecode_3_handicap = auto_book_form.find('input', attrs={'name': 'freeRecord.3.handicap'})
    if book_cells >= 4:
        book_freerecode_3_handicap_val = {'freeRecord.3.handicap': ''}
        if freerecode_3_handicap:
            freerecode_3_handicap_val = freerecode_3_handicap.get('value')
            if freerecode_3_handicap_val:
                book_freerecode_3_handicap_val['freeRecord.3.full_name'] = freerecode_3_handicap_val
        bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_freerecode_3_handicap_val)
    
    # freeRecord.3.gender_code
    freerecode_3_gender_code = auto_book_form.find('input', attrs={'name': 'freeRecord.3.gender_code'})
    if book_cells >= 4:
        book_freerecode_3_gender_code_val = {'freeRecord.3.gender_code': ''}
        if freerecode_3_gender_code:
            freerecode_3_gender_code_val = freerecode_3_gender_code.get('value')
            if freerecode_3_gender_code_val:
                book_freerecode_3_gender_code_val['freeRecord.3.gender_code'] = freerecode_3_gender_code_val
        bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_freerecode_3_gender_code_val)
    
    # freeRecord.3.golflink_number
    freerecode_3_golflink_number = auto_book_form.find('input', attrs={'name': 'freeRecord.3.golflink_number'})
    if book_cells >= 4:
        book_freerecode_3_golflink_number_val = {'freeRecord.3.golflink_number': ''}
        if freerecode_3_golflink_number:
            freerecode_3_golflink_number_val = freerecode_3_golflink_number.get('value')
            if freerecode_3_golflink_number_val:
                book_freerecode_3_golflink_number_val['freeRecord.3.golflink_number'] = freerecode_3_golflink_number_val
        bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_freerecode_3_golflink_number_val)
    
    # freeRecord.3.competition_round_type
    freerecode_3_compe_round_type = auto_book_form.find('input', attrs={'name': 'freeRecord.3.competition_round_type'})
    if book_cells >= 4:
        book_freerecode_3_competition_round_type_val = {'freeRecord.3.competition_round_type': ''}
        if freerecode_3_compe_round_type:
            freerecode_3_compe_round_type_val = freerecode_3_compe_round_type.get('value')
            if freerecode_3_compe_round_type_val:
                book_freerecode_3_competition_round_type_val['freeRecord.3.competition_round_type'] = freerecode_3_compe_round_type_val
        bdgc_auto_book_url += "&" + urllib.parse.urlencode(book_freerecode_3_competition_round_type_val)

    response_str = ''
    auto_book_res = requests.get(url=bdgc_auto_book_url, headers=bdgc_header_data)
    if auto_book_res.status_code == 200:
        auto_book_soup = bs(auto_book_res.text, 'html.parser')
        error_contain = auto_book_soup.find('div', attrs={'class': 'errorContain'})
        if error_contain:
            book_header = auto_book_soup.find('h1')
            if book_header:
                response_str = 'Golf Title: ' + book_header.text.strip().replace('\xc2\xa0', ' ') + '(RowID: ' + str(book_rowid) + ').\n'
            error_items = error_contain.find_all('div', attrs={'class': 'errorItem'})
            for error_item in error_items:
                error_name = error_item.find('div', attrs={'class': 'errorName'})
                error_reason = error_item.find('div', attrs={'class': 'errorReason'})
                response_str += error_name.text.strip() + ': ' + error_reason.text.strip() + '.\n'
            
            book_fix_url = "https://www.bdgc.com.au/views/members/booking/makeBooking.xhtml?booking_row_id=" + book_rowid + "&compactView=false"
            book_fix_res = requests.get(url=book_fix_url, headers=bdgc_header_data)
            
            parser = etree.HTMLParser()
            book_fix_tree = etree.parse(StringIO(book_fix_res.text), parser)
            book_fix_crossover_select = book_fix_tree.xpath('//div[@id="bookForm:crossoverSelect"]')
            book_fix_confirm_button = book_fix_crossover_select[0].xpath('.//a/@id')
            if book_fix_confirm_button:
                book_fix_form_data = {
                    'javax.faces.partial.ajax': 'true',
                    'javax.faces.partial.execute': '@all',
                    'javax.faces.partial.render': 'bookForm:messages bookForm'
                }
                book_fix_confirm_button_id = book_fix_confirm_button[0]
                book_fix_form_data['javax.faces.source'] = book_fix_confirm_button_id
                book_fix_form_data[book_fix_confirm_button_id] = book_fix_confirm_button_id
                book_fix_book_form = book_fix_tree.xpath('//form[@id="bookForm"]')
                book_fix_book_form_inputs = book_fix_book_form[0].xpath('.//input[@type="hidden" or @type="text"]')
                input_name = ''
                for book_fix_book_form_input in book_fix_book_form_inputs:
                    if input_name != book_fix_book_form_input.get('name'):
                        input_name = book_fix_book_form_input.get('name')
                        if  book_fix_book_form_input.get('value') is None:
                            book_fix_book_form_input_value = ''
                        else:
                            book_fix_book_form_input_value =  book_fix_book_form_input.get('value')
                        book_fix_form_data[book_fix_book_form_input.get('name')] = book_fix_book_form_input_value
                book_fix_book_form_selects = book_fix_book_form[0].xpath('.//select')
                for book_fix_book_form_select in book_fix_book_form_selects:
                    book_fix_book_form_selected = book_fix_book_form_select.xpath('.//option[@selected="selected"]')
                    if book_fix_book_form_selected[0].get('value') is None:
                        book_fix_book_form_selected_value = ''
                    else:
                        book_fix_book_form_selected_value = book_fix_book_form_selected[0].get('value')
                    book_fix_form_data[book_fix_book_form_select.get('name')] = book_fix_book_form_selected_value
                bdgc_confirm_booking_url = "https://www.bdgc.com.au/views/members/booking/makeBooking.xhtml"
                book_confirm_res = requests.post(url=bdgc_confirm_booking_url, data=book_fix_form_data, headers=bdgc_header_data)
                response_str = "Confirm Booking.\n" + response_str
            else:
                response_str = "Booking has failed as you are the only player in your team. More than one team member is required.\n" + response_str
        else:
            response_str = 'Booking is done successfully.\n'
            auto_main_content = auto_book_soup.find('div', attrs={'class': 'main-content'})
            member_id = 0
            continue_flag = True
            while continue_flag:
                member_cell = auto_main_content.find('div', attrs={'id': book_rowid + '_' + str(member_id)})
                if member_cell:
                    response_str += member_cell.text.strip() + '\n'
                else:
                    continue_flag = False
                member_id = member_id + 1
    
    return response_str
    
def book_handler(event, context):
    # TODO implement
    os.environ["TZ"] = 'Australia/NSW'
    if event['after_days'] is None:
        after_days = '8'
    else:
        after_days = '' + event['after_days']
    
    cookie_info = login_function(event['memno'], event['password'])
    book_eventid = get_book_eventid(cookie_info, after_days, event['comments'])
    
    loop_count = 0
    while book_eventid == '':
        book_eventid = get_book_eventid(cookie_info, after_days, event['comments'])
        loop_count = loop_count + 1
        if loop_count >= 5:
            break
        time.sleep(3)
    
    book_row_result = {
        'row_id': '',
        'row_time': ''
    }
    book_loop_count = 0
    if book_eventid:
        while book_row_result['row_id'] == '':
            book_row_result = get_book_rowid(cookie_info, book_eventid)
            if book_loop_count >= 20:
                break
            time.sleep(3)
    
    result = ''
    if book_row_result['row_id']:
        result = book_golf(cookie_info, book_eventid, book_row_result['row_id'])
    
    local_zone = dateutil.tz.gettz(os.environ["TZ"])
    now_date = datetime.now(tz=local_zone)
    now_date_str = now_date.strftime('%a %d %b %I:%M:%S %p')
    
    date_after_eight_days = now_date
    for day_no in range(0, int(after_days)):
        date_after_eight_days = date_after_eight_days + relativedelta(days=1)
    next_book_date_str = date_after_eight_days.strftime('%a %d %b')
    book_header_str = "\nName: " + event['name'] + ", Date: " + next_book_date_str + ", Time: " + book_row_result['row_time'] + ", Booking Result(" + now_date_str +"):\n"
    
    result = book_header_str + result
    
    print(result)
    
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }