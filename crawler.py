mport csv
import json
import sys
import time
import urllib2

import chardet


def removeCodeComment(text):
    cmtStart = []
    i = 0
    while i < len(text):
        if text[i:i + 4] == '<!--':
            cmtStart.append(i)
            i += 4
            continue
        if text[i:i + 3] == '-->' and len(cmtStart) > 0:
            text = text[0:cmtStart[-1]] + text[i + 3:-1]
            i = cmtStart[-1] + 4
            cmtStart.pop(-1)
            continue
        i += 1
    return text


def getNewsTitleAndArticalAndChannel(html):
    artical = ''
    title = ''
    channel = ''

    titleStart = html.find('<title>')
    titleEnd = html.find('</title>')
    if titleStart != -1 and titleEnd != -1:
        title = html[titleStart + 7:titleEnd][0:-13]

    articalStart = html.find('id="artibody"')
    articalEnd = -1
    if articalStart != -1:
        # 这里还要改进,因为可能会有多个img等div
        # if html[articalStart + 14:articalStart + 200].find('class="img_wrapper"') == -1:  # 200是随便写的数字,后续要改进
        #     articalEnd = html[articalStart:-1].find('</div>')
        # else:
        #     temp = html[articalStart + 14:-1].find('</div>')
        #     articalEnd = html[articalStart + 14:-1].find('</div>') + temp
        left_html = html[articalStart + 14:-1]
        div_cnt = 1
        for i in range(len(left_html)):
            if left_html[i:i + 4] == '<div':
                div_cnt += 1
            if left_html[i:i + 5] == '</div':
                div_cnt -= 1

            if div_cnt == 0:
                articalEnd = i
                break
    if articalStart != -1 and articalEnd != -1:
        artical = html[articalStart + 14:-1][0:articalEnd]
        artical = removeCodeComment(artical)

    channelCodeStart = html.find("comment_channel:")
    if channelCodeStart != -1:
        channel = html[channelCodeStart + 16:channelCodeStart + 18]
    return artical, title, channel


def readComment(url, channel):
    resultCmt = ''

    '''两种情况:数字id和doc类型'''
    id = ''
    if url.find('doc-i') != -1:
        # http://news.sina.com.cn/o/2015-12-13/doc-ifxmpnqf9642091.shtml
        id = url.split('doc-i')[1].split('.')[0]
    else:
        # http://news.sina.com.cn/c/2015-08-11/210332192308.shtml
        if len(url.split('/')) > 0 and len(url.split('/')[-1]) > 4:
            id = url.split('/')[-1][4:-1].split('.')[0]
    if len(id) > 0 and id[0].isdigit():
        commentUrl = 'http://comment5.news.sina.com.cn/page/info?format=json&channel=' + channel + '&newsid=1-1-' + id + '&group=0&compress=1&ie=gbk&oe=gbk&page=1&page_size=100&jsvar=requestId_29902459'
    else:
        commentUrl = 'http://comment5.news.sina.com.cn/page/info?format=json&channel=' + channel + '&newsid=comos-' + id + '&group=0&compress=1&ie=gbk&oe=gbk&page=1&page_size=100&jsvar=requestId_29902459'

    page = urllib2.urlopen(commentUrl)
    data = unicode(page.read(), 'gbk')
    jdata = json.loads(data)
    if jdata.has_key('result') and jdata['result'].has_key('cmntlist'):
        for cmt in jdata['result']['cmntlist']:
            resultCmt += cmt['content'] + '\n'

    return resultCmt


# fp = open("result.csv", "wb")
# writer = csv.writer(fp)
# fp.write('\xEF\xBB\xBF')
# fp.close()

reload(sys)
sys.setdefaultencoding("utf-8")

urlPrefix = "http://search.sina.com.cn/?c=news&q=%B3%C7%B9%DC&range=title&time=custom&stime=2010-01-01&etime=2011-09-13&num=10&page="

url = "http://search.sina.com.cn/?c=news&q=%B3%C7%B9%DC&range=title&time=custom&stime=2010-01-01&etime=2011-09-13&num=10&page=1"

page = 0

while page <= 654:
    fp1 = open("result.csv", "a")
    writer1 = csv.writer(fp1)

    page += 1

    # 获取搜索结果的第n页
    url = urlPrefix + str(page)

    # 获取页面内容
    try:
        wp = urllib2.urlopen(url)
        html = wp.read()
        # codeDetect = urllib2.urlopen(url).read()
        # codeOfUrl = chardet.detect(codeDetect)['encoding']
        content = html.decode('gbk').encode('utf-8')  # 将页面重新编码
        # 开始读取每一条新闻,以i为指针从头解析每个搜索结果页面(注意:这一层解析的并不是单独的新闻页面)
        i = 0
        while True:
            # 从上一条新闻结束的位置i开始寻找文字新闻
            start = content.find('<!-- 文字新闻spider begin -->', i)
            if start == -1:
                break

            # 如果找到文字新闻入口,则开始找相应新闻的url
            urlStart = content.find('<h2><a href="', start)
            urlEnd = content.find('"', urlStart + 13)
            news_url = content[urlStart + 13:urlEnd]
            print '%%%URL:', news_url

            # 打开具体新闻的URL
            newsWp = urllib2.urlopen(news_url)
            newsHtml = newsWp.read()
            newsWp.close()
            time.sleep(1)

            # 查找这条新闻正文的编码方式,如不是utf-8,则转换成utf-8
            # encodeStart = newsHtml.find('charset="')
            # encodeEnd = newsHtml[encodeStart + 9:-1].find('"')
            # code = newsHtml[encodeStart + 9:-1][0:encodeEnd]
            # if newsHtml.find('content="text/html; charset=gb2312"')!=-1:
            #     code = 'gd2312'

            # 使用chardet检测编码
            newsWp1 = urllib2.urlopen(news_url).read()
            code = chardet.detect(newsWp1)['encoding']

            if code != 'utf-8':
                newsHtml = newsHtml.decode(code).encode('utf-8')

            artical, title, channel = getNewsTitleAndArticalAndChannel(newsHtml)
            artical = artical.replace('<p>', '')
            artical = artical.replace('</p>', '\n')

            print str(page) + '###TITLE:' + title + '\n@@@ARTICLE:' + artical + '\n'

            comments = readComment(news_url, channel)
            # read comment
            print('***COMMENT' + readComment(news_url, channel) + '\n\n\n')

            writer1.writerow([page, news_url, title, artical, comments])

            i = urlEnd + 1

        time.sleep(1)
        fp1.close()

    except Exception, e:
        print str(page), 'ERROR', e
        time.sleep(1)
        fp1.close()
        continue

print 'All finished'

