import re

VALID_TAGS = ['a','img','strong','em','p','ul','li','ol','br','b','i','div']
VALID_ATTR = ['href','src','alt']

remove_empty_P = re.compile(r'<p>( |\t|\n|\r|\&nbsp;)*</p>', re.I|re.S|re.M)
double_br_to_P = re.compile(r'<br\/?><br\/?>', re.I|re.S|re.M)

def clean_html(html) :

        from BeautifulSoup import BeautifulSoup, Tag

        html = double_br_to_P.sub('<p>', html)
        #import codecs
        #OFD = codecs.open('/dev/stdout','w','utf-8')
        #print >>OFD, html

        soup = BeautifulSoup('<div>%s</div>'%html)

        for tag in soup.findAll('span', style='font-weight: bold;') :
            tag.name = 'b'
        for tag in soup.findAll('span', style='font-style: italic;') :
            tag.name = 'i'
        for tag in soup.findAll('span', style='text-decoration: underline;') :
            tag.name = 'u'

        for tag in soup.findAll(True) :
            if tag.name not in VALID_TAGS :
                tag.hidden = True
            else :
                for attr in tag._getAttrMap().keys() :
                    if attr not in VALID_ATTR :
                        del tag[attr]
            if tag.name == 'a' :
                tag['rel'] = 'nofollow'
                href = tag['href']
                if not href.startswith('http://') :
                    tag['href'] = 'http://' + href
        
        text = soup.renderContents()
        return remove_empty_P.sub('', text)

if __name__ == '__main__' :
    #body = """tea <span style="font-weight: bold;">bold <foo>foo tag showme</foo></span> <span style="font-style: italic;">italic here</span> fasdfasdfasdf<br>"""
    body = """test1<div>test2</div><div>test3</div><div><br></div>"""

    print clean_html(body)
