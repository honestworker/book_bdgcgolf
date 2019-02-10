import sys

sys.path.append("/opt")

import json
import requests
from bs4 import BeautifulSoup as bs
import logging
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time

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
def get_book_eventid(cookie_info, comments):
    bdgc_eventlist_url = "https://www.bdgc.com.au/views/members/booking/eventList.xhtml"
    bdgc_header_data = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
        'Cookie': cookie_info
    }
    res = requests.get(url=bdgc_eventlist_url, headers=bdgc_header_data)
    soup = bs(res.text, 'html.parser')
    eventlist = soup.find('div', attrs={'class': 'event-list'})
    
    date_after_eight_days = datetime.now() + relativedelta(days=8)
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
        'Cookie': cookie_info
    }
    
    res = requests.get(url=bdgc_book_url, headers=bdgc_header_data)
    soup = bs(res.text, 'html.parser')
    book_available_groups = soup.find_all('div', attrs={'class': 'available'})
    for book_group in book_available_groups:
        taken_cells = book_group.find_all('div', attrs={'class': 'cell-taken'})
        if len(taken_cells) == 0:
            return get_only_number(book_group['id'])
    
    return result

def book_golf(cookie_info, book_eventid, book_rowid):
    bdgc_book_form_url_prefix = "https://www.bdgc.com.au/members/bookings/open/DefaultPartners.msp?booking_event_id="
    bdgc_book_form_url_suffix = "&booking_row_id="
    bdgc_book_form_url = bdgc_book_form_url_prefix + book_eventid + bdgc_book_form_url_suffix + book_rowid
    bdgc_header_data = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
        'Cookie': cookie_info
    }
    res = requests.get(url=bdgc_book_form_url, headers=bdgc_header_data)
    soup = bs(res.text, 'html.parser')
    
    auto_book_form = soup.find('form', attrs={'name': 'auto_book'})
    auto_book_form_data = {
        'doAction': 'FAST_BOOK',
        'booking_event_id': book_eventid,
        'booking_row_id': book_rowid,
        'booking_group_id': '',
        'times_free': 4,
        'times_free': 4,
        'bookLinkedEvent': 'n',
        'numberOfHoles': '',
        'backNineId': '',
        'group_name': '',
        'time': '',
        'title': '',
        'freeRecord.id': 0,
        'freeRecord.0.booking_record_id': 0,
        'freeRecord.0.booking_record_x_index': 0,
        'freeRecord.0.membership_number': '',
        'freeRecord.0.full_name': '',
        'freeRecord.0.competition_round_type': '',
        'freeRecord.id': 1,
        'freeRecord.1.booking_record_id': 1,
        'freeRecord.1.booking_record_x_index': 1,
        'freeRecord.1.membership_number': '',
        'freeRecord.1.full_name': '',
        'freeRecord.1.handicap': '',
        'freeRecord.1.gender_code': '',
        'freeRecord.1.golflink_number': '',
        'freeRecord.1.competition_round_type': '',
        'freeRecord.id': 2,
        'freeRecord.2.booking_record_id': 2,
        'freeRecord.2.booking_record_x_index': 2,
        'freeRecord.2.membership_number': '',
        'freeRecord.2.full_name': '',
        'freeRecord.2.handicap': '',
        'freeRecord.2.gender_code': '',
        'freeRecord.2.golflink_number': '',
        'freeRecord.2.competition_round_type': '',
        'freeRecord.id': 3,
        'freeRecord.3.booking_record_id': 3,
        'freeRecord.3.booking_record_x_index': 3,
        'freeRecord.3.membership_number': '',
        'freeRecord.3.full_name': '',
        'freeRecord.3.handicap': '',
        'freeRecord.3.gender_code': '',
        'freeRecord.3.golflink_number': '',
        'freeRecord.3.competition_round_type': '',
    }
    
    default_playing_group_form = soup.find('form', attrs={'name': 'defaultPlayingGroupForm'})
    
    # BookLinkedEvent
    book_linked_event = default_playing_group_form.find('input', attrs={'name': 'bookLinkedEvent'})
    if book_linked_event:
        if book_linked_event['checked']:
            auto_book_form_data['bookLinkedEvent'] = 'y'
    
    # NumberOfHoles
    number_of_holes = default_playing_group_form.find('input', attrs={'name': 'numberOfHoles'})
    if number_of_holes:
        number_of_holes_val = number_of_holes.get('value')
        if number_of_holes_val:
            auto_book_form_data['numberOfHoles'] = number_of_holes_val
    
    # BackNineId
    back_nine_id = auto_book_form.find('input', attrs={'name': 'backNineId'})
    if back_nine_id:
        back_nine_id_val = back_nine_id.get('value')
        if back_nine_id_val:
            auto_book_form_data['backNineId'] = back_nine_id_val
    
    # GroupName
    group_name = auto_book_form.find('input', attrs={'name': 'group_name'})
    if group_name:
        group_name_val = group_name.get('value')
        if group_name_val:
            auto_book_form_data['group_name'] = group_name_val
    
    # Time
    book_time = auto_book_form.find('input', attrs={'name': 'time'})
    if book_time:
        book_time_val = book_time.get('value')
        if book_time_val:
            auto_book_form_data['time'] = book_time_val
    
    # Title
    book_title = auto_book_form.find('input', attrs={'name': 'title'})
    if book_title:
        book_title_val = book_title.get('value')
        if book_title_val:
            auto_book_form_data['title'] = book_title_val
    
    ###### Record 0 ######
    # freeRecord.0.membership_number
    freerecode_0_mem_num = auto_book_form.find('input', attrs={'name': 'freeRecord.0.membership_number'})
    if freerecode_0_mem_num:
        freerecode_0_mem_num_val = freerecode_0_mem_num.get('value')
        if freerecode_0_mem_num_val:
            auto_book_form_data['freeRecord.0.membership_number'] = freerecode_0_mem_num_val
    
    # freeRecord.0.full_name
    freerecode_0_full_name = auto_book_form.find('input', attrs={'name': 'freeRecord.0.full_name'})
    if freerecode_0_full_name:
        freerecode_0_full_name_val = freerecode_0_full_name.get('value')
        if freerecode_0_mem_num_val:
            auto_book_form_data['freeRecord.0.full_name'] = freerecode_0_full_name_val
    
    # freeRecord.0.competition_round_type
    freerecode_0_compe_round_type = auto_book_form.find('input', attrs={'name': 'freeRecord.0.competition_round_type'})
    if freerecode_0_compe_round_type:
        freerecode_0_compe_round_type_val = freerecode_0_compe_round_type.get('value')
        if freerecode_0_compe_round_type_val:
            auto_book_form_data['freeRecord.0.competition_round_type'] = freerecode_0_compe_round_type_val
    
    ###### Record 1 ######
    # freeRecord.1.membership_number
    freerecode_1_mem_num = auto_book_form.find('input', attrs={'name': 'freeRecord.1.membership_number'})
    if freerecode_1_mem_num:
        freerecode_1_mem_num_val = freerecode_1_mem_num.get('value')
        if freerecode_1_mem_num_val:
            auto_book_form_data['freeRecord.1.membership_number'] = freerecode_1_mem_num_val
    
    # freeRecord.1.full_name
    freerecode_1_full_name = auto_book_form.find('input', attrs={'name': 'freeRecord.1.full_name'})
    if freerecode_1_full_name:
        freerecode_1_full_name_val = freerecode_1_full_name.get('value')
        if freerecode_1_full_name_val:
            auto_book_form_data['freeRecord.1.full_name'] = freerecode_1_full_name_val
    
    # freeRecord.1.handicap
    freerecode_1_handicap = auto_book_form.find('input', attrs={'name': 'freeRecord.1.handicap'})
    if freerecode_1_handicap:
        freerecode_1_handicap_val = freerecode_1_handicap.get('value')
        if freerecode_1_handicap_val:
            auto_book_form_data['freeRecord.1.handicap'] = freerecode_1_handicap_val
    
    # freeRecord.1.gender_code
    freerecode_1_gender_code = auto_book_form.find('input', attrs={'name': 'freeRecord.1.gender_code'})
    if freerecode_1_gender_code:
        freerecode_1_gender_code_val = freerecode_1_gender_code.get('value')
        if freerecode_1_gender_code_val:
            auto_book_form_data['freeRecord.1.gender_code'] = freerecode_1_gender_code_val
    
    # freeRecord.1.golflink_number
    freerecode_1_golflink_number = auto_book_form.find('input', attrs={'name': 'freeRecord.1.golflink_number'})
    if freerecode_1_golflink_number:
        freerecode_1_golflink_number_val = freerecode_1_golflink_number.get('value')
        if freerecode_1_golflink_number_val:
            auto_book_form_data['freeRecord.1.golflink_number'] = freerecode_1_golflink_number_val
    
    # freeRecord.1.competition_round_type
    freerecode_1_compe_round_type = auto_book_form.find('input', attrs={'name': 'freeRecord.1.competition_round_type'})
    if freerecode_1_compe_round_type:
        freerecode_1_compe_round_type_val = freerecode_1_compe_round_type.get('value')
        if freerecode_1_compe_round_type_val:
            auto_book_form_data['freeRecord.1.competition_round_type'] = freerecode_1_compe_round_type_val
    
    ###### Record 2 ######
    # freeRecord.2.membership_number
    freerecode_2_mem_num = auto_book_form.find('input', attrs={'name': 'freeRecord.2.membership_number'})
    if freerecode_2_mem_num:
        freerecode_2_mem_num_val = freerecode_2_mem_num.get('value')
        if freerecode_2_mem_num_val:
            auto_book_form_data['freeRecord.2.membership_number'] = freerecode_2_mem_num_val
    
    # freeRecord.2.full_name
    freerecode_2_full_name = auto_book_form.find('input', attrs={'name': 'freeRecord.2.full_name'})
    if freerecode_2_full_name:
        freerecode_2_full_name_val = freerecode_2_full_name.get('value')
        if freerecode_2_full_name_val:
            auto_book_form_data['freeRecord.2.full_name'] = freerecode_2_full_name_val
    
    # freeRecord.2.handicap
    freerecode_2_handicap = auto_book_form.find('input', attrs={'name': 'freeRecord.2.handicap'})
    if freerecode_2_handicap:
        freerecode_2_handicap_val = freerecode_2_handicap.get('value')
        if freerecode_2_handicap_val:
            auto_book_form_data['freeRecord.2.handicap'] = freerecode_2_handicap_val
    
    # freeRecord.2.gender_code
    freerecode_2_gender_code = auto_book_form.find('input', attrs={'name': 'freeRecord.2.gender_code'})
    if freerecode_2_gender_code:
        freerecode_2_gender_code_val = freerecode_2_gender_code.get('value')
        if freerecode_2_gender_code_val:
            auto_book_form_data['freeRecord.2.gender_code'] = freerecode_2_gender_code_val
    
    # freeRecord.2.golflink_number
    freerecode_2_golflink_number = auto_book_form.find('input', attrs={'name': 'freeRecord.2.golflink_number'})
    if freerecode_2_golflink_number:
        freerecode_2_golflink_number_val = freerecode_2_golflink_number.get('value')
        if freerecode_2_golflink_number_val:
            auto_book_form_data['freeRecord.2.golflink_number'] = freerecode_2_golflink_number_val
    
    # freeRecord.2.competition_round_type
    freerecode_2_compe_round_type = auto_book_form.find('input', attrs={'name': 'freeRecord.2.competition_round_type'})
    if freerecode_2_compe_round_type:
        freerecode_2_compe_round_type_val = freerecode_2_compe_round_type.get('value')
        if freerecode_2_compe_round_type_val:
            auto_book_form_data['freeRecord.2.competition_round_type'] = freerecode_2_compe_round_type_val
    
    ###### Record 3 ######
    # freeRecord.3.membership_number
    freerecode_3_mem_num = auto_book_form.find('input', attrs={'name': 'freeRecord.3.membership_number'})
    if freerecode_3_mem_num:
        freerecode_3_mem_num_val = freerecode_3_mem_num.get('value')
        if freerecode_3_mem_num_val:
            auto_book_form_data['freeRecord.3.membership_number'] = freerecode_3_mem_num_val
    
    # freeRecord.3.full_name
    freerecode_3_full_name = auto_book_form.find('input', attrs={'name': 'freeRecord.3.full_name'})
    if freerecode_3_full_name:
        freerecode_3_full_name_val = freerecode_3_full_name.get('value')
        if freerecode_3_full_name_val:
            auto_book_form_data['freeRecord.3.full_name'] = freerecode_3_full_name_val
    
    # freeRecord.3.handicap
    freerecode_3_handicap = auto_book_form.find('input', attrs={'name': 'freeRecord.3.handicap'})
    if freerecode_3_handicap:
        freerecode_3_handicap_val = freerecode_3_handicap.get('value')
        if freerecode_3_handicap_val:
            auto_book_form_data['freeRecord.3.handicap'] = freerecode_3_handicap_val
    
    # freeRecord.3.gender_code
    freerecode_3_gender_code = auto_book_form.find('input', attrs={'name': 'freeRecord.3.gender_code'})
    if freerecode_3_gender_code:
        freerecode_3_gender_code_val = freerecode_3_gender_code.get('value')
        if freerecode_3_gender_code_val:
            auto_book_form_data['freeRecord.3.gender_code'] = freerecode_3_gender_code_val
    
    # freeRecord.3.golflink_number
    freerecode_3_golflink_number = auto_book_form.find('input', attrs={'name': 'freeRecord.3.golflink_number'})
    if freerecode_3_golflink_number:
        freerecode_3_golflink_number_val = freerecode_3_golflink_number.get('value')
        if freerecode_3_golflink_number_val:
            auto_book_form_data['freeRecord.3.golflink_number'] = freerecode_3_golflink_number_val
    
    # freeRecord.3.competition_round_type
    freerecode_3_compe_round_type = auto_book_form.find('input', attrs={'name': 'freeRecord.3.competition_round_type'})
    if freerecode_3_compe_round_type:
        freerecode_3_compe_round_type_val = freerecode_3_compe_round_type.get('value')
        if freerecode_3_compe_round_type_val:
            auto_book_form_data['freeRecord.3.competition_round_type'] = freerecode_3_compe_round_type_val
    
    response_str = ''
    bdgc_auto_book_url = "https://www.bdgc.com.au/members/bookings/open/MakeBooking.msp"
    res = requests.get(url=bdgc_auto_book_url, headers=bdgc_header_data, data=auto_book_form_data)
    if res.status_code == 200:
        soup = bs(res.text, 'html.parser')
        members_content = soup.find('div', attrs={'class': 'members-content'})
        error_contains = members_content.find('div', attrs={'class': 'errorContain'})
        for error_item in error_contains:
            error_name = error_item.find('div', attrs={'class': 'errorName'})
            error_reason = error_item.find('div', attrs={'class': 'errorReason'})
            response_str += error_name.text + ': ' + error_reason.text + '. '
    
    return response_str
    
def book_handler(event, context):
    # TODO implement
    cookie_info = login_function(event['memno'], event['password'])
    book_eventid = get_book_eventid(cookie_info, event['comments'])
    
    while book_eventid == '':
        book_eventid = get_book_eventid(cookie_info, event['comments'])
        time.sleep(30)
    
    if book_eventid:
        book_rowid = get_book_rowid(cookie_info, book_eventid)
        
    result = ''
    if book_rowid:
        result = book_golf(cookie_info, book_eventid, book_rowid)
       
    #now_date = datetime.now()
    #now_date_str = now_date.strftime('%a %d %b %I:%M:%S %p')
    
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }