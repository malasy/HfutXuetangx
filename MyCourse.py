#coding:utf-8
import urllib.request,urllib.parse,urllib.error
import re
import time
import datetime
import random
import base64
import http.cookiejar
import os

global user_agent
global cookie
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'

#不需要带cookie的请求
def get_response(url):
    page = urllib.request.urlopen(url)
    res = page.read()
    return res.decode('utf-8')

#带cookie的请求
def request_with_cookies(url):
    req = urllib.request.Request(url)
    req.add_header('User-Agent',user_agent)
    req.add_header('Cookie',cookie)
    page = urllib.request.urlopen(req)
    res = page.read()
    return res.decode('utf-8')


#获取term_id
def get_term_id():
    term_url = 'https://hfut.xuetangx.com/api/v1/plat_term?plat_id=369'
    term_content = get_response(term_url)
    pattern = re.compile(r'"term_id":\d+')
    result = pattern.findall(term_content)
    term_id = 0
    for str1 in result:
        arr = str1.split(':')
        if(arr[1]=='0'):
            continue
        term_id = arr[1]
    return term_id

#匹配课程名称,课程号，班级号
#course_name  course_id   class_id
def get_course_class(term_id):
    url = 'https://hfut.xuetangx.com/mycourse_list?running_status=&term_id='+term_id+'&search=&page_size=10&page=1'
    string = request_with_cookies(url)
    #正则匹配，保存到list
    pattern = re.compile(r'"course_name":"[^"]+"')
    res_course_name = pattern.findall(string)

    pattern = re.compile(r'"course_id":\d+')
    res_course_id = pattern.findall(string)

    pattern = re.compile(r'"class_id":\d+')
    res_class_id = pattern.findall(string)

    course_name_list=[]
    course_id_list = []
    class_id_list = []
    course_count = len(res_course_id);
	
    for i in range(course_count):
    	course_name_list.append(res_course_name[i].replace('"','').split(':')[1])
    	course_id_list.append(res_course_id[i].split(':')[1])
    	class_id_list.append(res_class_id[i].split(':')[1])
    	
    print('找到课程'+str(course_count)+'个:')
    #打印课程名称
    for i in range(course_count):
    	print(str(i+1)+':'+course_name_list[i])
    #选择课程
    select = input('输入编号:')
    index = int(select) - 1
    res = [course_id_list[index],class_id_list[index]]
    return res

#获取unit_id和course_id,每个视频对应一个unit_id和course_id
def get_unit_item(course_id,class_id):
    cw_url = 'https://hfut.xuetangx.com/server/api/v1/course/'+course_id+'/courseware?class_id='+class_id
    cw_content = get_response(cw_url)
    pattern = re.compile(r'"unit_id":"[-\w]+","item_id":"\d+"')
    result = pattern.findall(cw_content)
    dict = {}
    for item in result:
       item = item.replace('"','')
       temp = item.split(',')
       unit_id = temp[0].split(':')
       item_id = temp[1].split(':')
       dict[unit_id[1]] = item_id[1]
    return dict
	
#获取视频时长
def get_video_length(video_id,class_id):
    url = 'https://hfut.xuetangx.com/server/api/class_videos/?video_id='+str(video_id)+'&class_id='+str(class_id)
    res = request_with_cookies(url)
    pattern = re.compile(r'"duration":\d+')
    duration = pattern.findall(res)[0].split(':')[1]
    return int(duration)

def get_page(video_id):
    return video_id+'rhtb'
	
def get_end(ts):
    ts2 = int(str(ts)[0:6]+'0000000')
    ts2 = ts2+random.randint(0,6666666)
    return ts2

#获取播放记录
def get_record(course_id):
    url = 'https://hfut.xuetangx.com/video_point/get_video_watched_record?cid='+course_id+'&vtype=rate'
    res = request_with_cookies(url)
    video_list = re.findall(r'"\d+":{"rate":[\d],',res)
    count = len(video_list)
    for i in range(count):
        video_list[i] = video_list[i].replace('"','').split(':')[0]
    return video_list

#播放视频，视频播放时发送一个et=play的请求，之后每隔5秒发送一个et=heartbeat的请求
#结束时发送一个et=videoend的请求
def start_video(param):
    
    t = time.time()	
    et = 'play'		#请求动作
    cp = param['cp']	#上次播放时长记录
    ts = int(round(t*1000))	#时间戳
    u = param['user_id']	#user_id
    c = param['course_id']	#course_id
    v = param['item_id']	#video_id(即item_id)
    d = param['duration']	#视频时长
    sp=1
    pg = get_page(v)		#页面标记，随机产生的
    sq = 1  			#请求序号，每发送一次请求自动加1
    end = get_end(ts)	#随机产生，每发送一次加1
    beat = d/5		#计算et=heartbeat请求的次数
	
	#et=play
    url = 'https://hfut.xuetangx.com/heartbeat?i=5&et='+et+'&p=web&cp='+str(cp)+'&fp=0&tp=0&sp='+str(sp)+'&ts='+str(ts)+'&u='+str(u)+'&c='+str(c)+'&v='+str(v)+'&cc='+str(v)+'&d='+str(d)+'&pg='+pg+'&sq='+str(sq)+'&_='+str(end)
    request_with_cookies(url)
    #et=heartbeat
    while(1):
        et = 'heartbeat'
        cp=cp+5
        ts = ts+50
        if cp>d:
            break
        sq= sq+1
        end = end+1
        url = 'https://hfut.xuetangx.com/heartbeat?i=5&et='+et+'&p=web&cp='+str(cp)+'&fp=0&tp=0&sp=1&ts='+str(ts)+'&u='+str(u)+'&c='+str(c)+'&v='+str(v)+'&cc='+str(v)+'&d='+str(d)+'&pg='+pg+'&sq='+str(sq)+'&_='+str(end)
        request_with_cookies(url)
	#et=videoend
    et = 'videoend'
    cp = d
    sq= sq+1
    end = end+1
    url = 'https://hfut.xuetangx.com/heartbeat?i=5&et='+et+'&p=web&cp='+str(cp)+'&fp=0&tp=0&sp=1&ts='+str(ts)+'&u='+str(u)+'&c='+str(c)+'&v='+str(v)+'&cc='+str(v)+'&d='+str(d)+'&pg='+pg+'&sq='+str(sq)+'&_='+str(end)
    request_with_cookies(url)

#删除已经播放过的
def remove_played(unit_item,played_list):
    res_dict = {}
    for unit in unit_item:
        flag = True
        for i in range(len(played_list)):
            if unit_item[unit]==played_list[i]:
                flag = False
        if flag:
            res_dict[unit] = unit_item[unit]
    return res_dict


#处理视频参数
def process_every_video(unit_item,course_id,class_id,user_id):
    total = len(unit_item)
    print('该门课程共'+str(total)+'个视频')
    #获取记录
    played_list = get_record(course_id)
    print(str(len(played_list))+'个视频已观看')
    unit_item = remove_played(unit_item,played_list)
    total = len(unit_item)
    print('开始观看'+str(total)+'个视频')
    print('以下过程网络请求频繁，可能会出现异常；忽略或重试即可')
    for unit in unit_item:
        item_id = unit_item[unit]
        param = {}
        param['course_id'] = course_id
        param['class_id'] = class_id
        param['item_id'] =  item_id
        param['user_id'] = user_id
        param['duration'] = get_video_length(item_id,class_id)
        param['cp'] = 0
        try:
            start_video(param)
        except Exception as err:
            print('Exception:')
            print(err)
        total = total-1
        print('还剩'+str(total)+'个视频')
    print('finish')


#保存验证码图片
def save_picture(pic_str):
    f = open('captcha.jpg','wb')
    f.write(base64.b64decode(pic_str))
    f.close()
    
#获取验证码图片和key
def get_captcha():
    url = 'https://hfut.xuetangx.com/api/v1/code/captcha'
    res = get_response(url)
    pic_str = re.findall(r'"img":"[^"]+"',res)[0]
    pic_str = pic_str.replace('"','').split(':')[1]
    cap_key = re.findall(r'"captcha_key":"[\w]+"',res)[0]
    cap_key = cap_key.replace('"','').split(':')[1]
    save_picture(pic_str)
    return cap_key

#登录
def login():
    url = 'https://hfut.xuetangx.com/api/v1/oauth/number/login'
    user_name = input('输入用户名:')
    password = input('输入密码:')
    cap_key = get_captcha()
    print('验证码图片已存储在该程序目录中')
    cap = input('输入验证码:')
    #设置登录请求
    payload = {'login':user_name,'password':password,'captcha':cap,'captcha_key':cap_key,'is_alliance':0}
    data = urllib.parse.urlencode(payload).encode()
    headers={'User-Agent':user_agent,'Connection':'keep-alive'}

    #保存Cookie到文件
    cookie_file = 'cookie.txt'
    cookie_aff = http.cookiejar.MozillaCookieJar(cookie_file)
    handler = urllib.request.HTTPCookieProcessor(cookie_aff)
    opener = urllib.request.build_opener(handler)
    request = urllib.request.Request(url,data,headers)
    try:
        response = opener.open(request)
    except urllib.error.URLError as e:
        print(e.reason)
        print('请确认用户名，密码及验证码正确')
        return False

    cookie_aff.save(ignore_discard=True, ignore_expires=True)
    return True

#将cookie文件中的内容转换为字符串
def get_cookie():
    cookie_str = ''
    with open('cookie.txt','r') as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            line_list = line.split('\t')
            s = len(line_list)
            if s>2:
                cookie_str=cookie_str+line_list[s-2]+'='+line_list[s-1]+'; '
    cookie_str = cookie_str.strip(' ')
    cookie_str = cookie_str.strip(';')
    return cookie_str
	
def get_user_id():
    url = 'https://hfut.xuetangx.com/header_ajax'
    string = request_with_cookies(url)
    user_id = re.findall(r'"user_id":\d+',string)[0].split(':')[1]
    real_name = re.findall(r'"real_name":"[^"]+"',string)[0].split(':')[1].strip('"')
    print('当前登录用户:'+real_name)
    return user_id

if __name__ == "__main__":
    is_login = False
    #查看是否有cookie
    flag = os.path.exists('cookie.txt')
    if flag:
        use_log = input('有登录记录，是否直接使用Y/N:')
        if use_log=='Y':
            is_login = True
        else:
            is_login = False
        
    #账号登录，获取cookies
    while(not is_login):
        is_login = login()
        
    cookie = get_cookie()
    print('登录成功')
    #获取user_id
    user_id = get_user_id()
	
    term_id = get_term_id()
    flag = 'Y'
    while(flag=='Y'):
        flag = 'N'
        course_class = get_course_class(term_id)
        course_id = course_class[0]
        class_id = course_class[1]
        unit_item = get_unit_item(course_id,class_id)
        process_every_video(unit_item,course_id,class_id,user_id)
        flag = input('输入Y继续')
    os.system('pause')
	
	
