import os
from utilities.common import utc_now_ts_ms as nowms


#this function take sendnumber clr size note username and filename
#will check if it clr or bw (1 or 0)
def download_naming(sendnumber, clr, size, note, username, filename):
    filename, file_ext = os.path.splitext(filename)
    if clr == '1':
        clr = 'Color'
    else:
        clr = 'BW'
    #for readability eg.'A1'
    size = f'A{size}'

    if note == '':
        note = 'nonote'
    else:
        note = 'NOTE'

    #this will output this name sendnumber_clr_size_note_username.pdf
    new_filename = f'{sendnumber}_{clr}_{size}_{note}_{username}_{nowms()()}{file_ext}'

    return new_filename

def name_tag(to_store,id):
    name_tag = f'T{to_store}{id}'
    return name_tag
