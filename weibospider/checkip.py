#-*-coding: utf-8 -*-
import urllib2,socket,time
from settings import REQUEST_TIMEOUT

check_url='http://www.sina.com'

def check_proxy_helper(protocol,ip_port):
    try:
        proxy_support = urllib2.ProxyHandler({protocol:ip_port})
        opener = urllib2.build_opener(proxy_support)
        urllib2.install_opener(opener)
        header = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.48'}
        req = urllib2.Request(check_url,headers=header)
        src = urllib2.urlopen(req)
#        with open('tmp.txt','w') as f:
#            f.write(src.read())
        proxy_detected = True
    except urllib2.HTTPError,e:
        print 'Error code:',e.code
        return False
    except Exception,detail:
        print 'Error:',detail
        return False
    return proxy_detected
        
def check_proxy(protocol,ip_port):

    socket.setdefaulttimeout(REQUEST_TIMEOUT)  #设置请求超时时间
    result = check_proxy_helper(protocol,ip_port)
    if result:
        return True
    else:
        return False

if __name__ == '__main__':
    protocol = 'http'
    ip_port = '123.57.216.113:808'
    if check_proxy(protocol,ip_port):
        print "work"
    else:
        print "wrong"
