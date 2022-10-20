import os.path
import sys
import threading
import time
from tkinter import *
import re
import webbrowser
from Crypto.Cipher import DES
from binascii import b2a_hex
import requests
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

fn = sys.path[0] + '/woxiangxinnibuhuixiangdaozhegmingzihhahahah'
k = 'u2oh6Vu^'
agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
cookies = {}
# 存放所有课程链接
courses = []
# 存放所有作业信息
all_info = {}
# 筛选状态：0为展示未截止作业，1为展示所有
status = 0
# 筛选课程：all为展示所有课程，某课程名为展示该课程的信息
course = 'all'
course_name = {}
pool = ThreadPoolExecutor(max_workers=4)
main_width = 920
main_height = 540
workBox = {}
ButtonsL1 = {}
ButtonsL2 = {}
btnAdded = False
present = {}


def login(un, pwd):
    un = str(un)
    s = 'fid=-1&uname=' + un + '&password=' + pwd + '&refer=http%253A%252F%252Fi.chaoxing.com&t=true&forbidotherlogin=0&validate=&doubleFactorLogin=0&independentId=0'
    d = {}
    for i in s.split('&'):
        t = i.split('=')
        d[t[0]] = t[1]
    r = requests.post(url='https://passport2.chaoxing.com/fanyalogin?', data=d)
    global cookies
    cookies = r.cookies
    return check_login()


# 解析url参数
def url_param(s):
    x = s.split('?')[1].split('&')
    r = {}
    for i in x:
        t = i.split('=')
        r[t[0]] = t[1]
    res = requests.get(url=s, headers={'User-Agent': agent}, cookies=cookies)

    r['enc'] = re.search('name="workEnc" value="(.*)"', res.text).group(1)
    r['name'] = re.search('class="textHidden colorDeep" title="(.*)"', res.text).group(1)
    return r


# 获取各个课程的链接
def get_course():
    s = 'courseType=1&courseFolderId=0&baseEducation=0&superstarClass=&courseFolderSize=0'
    d = {}
    for i in s.split('&'):
        t = i.split('=')
        d[t[0]] = t[1]

    h = {
        'User-Agent': agent
    }
    gr = requests.post(url='http://mooc1-1.chaoxing.com/visit/courselistdata', cookies=cookies, data=d, headers=h)
    info = gr.text
    c = '<a {2}class="color1" href="(.*)" '
    r = re.compile(c).findall(info)
    for i in range(0, len(r)):
        r.append(r.pop(0) + '&pageHeader=8')
    return r


# 根据给的html获取作业名、作业状态、剩余时间
def get_work(s):
    l = re.findall('<li onclick="goTask\\(this\\);".*?</li>', s, flags=re.M | re.S)
    r = []
    for i in l:
        t = {}
        if 'time notOver' in i:
            t['notOver'] = 1
            t['surplus'] = re.search('剩余(.*)', i).group(1).strip()
        else:
            t['notOver'] = 0
            t['surplus'] = ''

        rt = re.search('class="overHidden2 fl">(.*?)</p>.*class="status fl">(.*?)</p>', i, re.M | re.S)
        t['name'] = rt.group(1)
        t['status'] = rt.group(2)
        r.append(t)
    print(r)
    return r

def added():
    global btnAdded
    btnAdded=True

def get_info():
    time.sleep(0.1)
    workBox.delete(0, END)
    global all_info
    for i in courses:
        pool.submit(get_single_info, i)


def get_single_info(i):
    # 存放url的参数、该课程的名称
    t = url_param(i)
    course_name[t['name']] = i
    print('正在获取：' + t['name'])
    url = 'https://mooc1.chaoxing.com/mooc2/work/list?courseId=' + \
          t['courseid'] + '&classId=' + t['clazzid'] + '&cpi=' + t['cpi'] + '&ut=s&enc=' + t['enc']
    r = requests.get(url=url, cookies=cookies, headers={
        'User-Agent': agent,
        'Referer': 'https://mooc2-ans.chaoxing.com/'
    })
    single = get_work(r.text)

    all_info[t['name']] = single
    print(t['name'] + "：已获取完毕")
    add_single_frame(single, t['name'])


def encrypt(text):
    key = k.encode('utf-8')
    cryptor = DES.new(key, DES.MODE_ECB)
    text = pkcs7_padding(text.encode('utf-8'))
    ciphertext = cryptor.encrypt(text)
    return str(b2a_hex(ciphertext)).split("'")[1]


def pkcs7_padding(s, block_size=16):
    bs = block_size
    return s + (bs - len(s) % bs) * chr(bs - len(s) % bs).encode()


def login_msg(b):
    if b:
        loginLb.place(relx=0.1, rely=0.1, relheight=0.1, relwidth=0.3)
    else:
        loginLb.place_forget()


def check_login():
    return cookies.get('vc3') is not None


def auto_login():
    if os.path.exists(fn):
        with open(fn, 'r') as r:
            a = r.read().splitlines()
            u = a[0]
            print('自动登录：')
            print('[' + u + ']')
            p = a[1]
            print('[' + p + "]")
            return login(u, p)


def hand_login():
    u = inp1.get()
    p = encrypt(inp2.get())
    print('手动登录：')
    print('[' + u + ']')
    print('[' + p + ']')
    if login(u, p):
        if CheckVar.get() == 1:
            with open(fn, 'w') as f:
                f.write(u)
                f.write('\n')
                f.write(p)
        lroot.destroy()
    else:
        login_msg(1)


def browser(event):
    # 获取选择行号
    c = workBox.curselection()[0]
    while c >= 0:
        x = workBox.get(c)
        if x[0] != ' ':
            webbrowser.open(url=course_name[x])
            break
        c -= 1


lock = Lock()


def add_single_frame(t, name):
    global present
    lock.acquire()
    workBox.insert(END, name)
    for j in t:
        if int(j['notOver']) or status:
            # temp = '    ' + j['name'] + '    [' + j['status'] + ']    ' + j['surplus']
            temp = '    [' + j['status'] + ']    ' + j['name'] + '    ' + j['surplus']
            workBox.insert(END, temp)
    workBox.insert(END, ' ')

    cBtn = Button(present, text=name, command=lambda c=name: {
        change_course(c),
        add_frame()
    }, font={'黑体', 12}, bg='lightgreen', fg='purple', relief=GROOVE)
    cBtn.pack(side=LEFT)
    ButtonsL1.update()
    now = ButtonsL1.winfo_width()
    if main_width - now < 0:
        if present is not ButtonsL2:
            present = ButtonsL2
            cBtn.destroy()
            cBtn = Button(present, text=name, command=lambda c=name: {
                change_course(c),
                add_frame()
            }, font={'黑体', 12}, bg='lightgreen', fg='purple', relief=GROOVE)
            cBtn.pack(side=LEFT)

    lock.release()


def add_frame():
    workBox.delete(0, END)
    workBox.bind('<<ListboxSelect>>', browser)
    workBox.insert(END)
    if course != 'all':
        workBox.insert(END, course)
        for j in all_info[course]:
            if int(j['notOver']) or status:
                temp = '    [' + j['status'] + ']    ' + j['name'] + '    ' + j['surplus']
                workBox.insert(END, temp)
    else:
        for i in all_info:
            t = all_info[i]
            workBox.insert(END, i)
            for j in t:
                if int(j['notOver']) or status:
                    # temp = '    ' + j['name'] + '    [' + j['status'] + ']    ' + j['surplus']
                    temp = '    [' + j['status'] + ']    ' + j['name'] + '    ' + j['surplus']
                    workBox.insert(END, temp)
            workBox.insert(END, ' ')


def logout():
    root.destroy()
    global cookies, courses
    cookies.clear()
    courses.clear()
    login_gui()

    if not check_login():
        exit()
    courses = get_course()
    # 获取信息
    get_info()
    main_gui()


def change_status(s: int):
    global status
    status = s


def change_course(c: str):
    global course
    course = c


def login_gui():
    # if not auto_login():
    global lroot, CheckVar, loginLb, inp2, inp1
    lroot = Tk()
    CheckVar = IntVar()
    loginLb = Label(lroot, text='用户名或密码错误', fg='red')
    inp1 = Entry(lroot)
    inp2 = Entry(lroot, show='*')

    lroot.title('hello')
    lroot.geometry('400x240')  # 这里的乘号不是 * ，而是小写英文字母 x

    lb1 = Label(lroot, text='用户名')
    lb1.place(relx=0.1, rely=0.2, relwidth=0.1, relheight=0.15)
    inp1.place(relx=0.3, rely=0.2, relwidth=0.5, relheight=0.15)
    lb1 = Label(lroot, text='密码')
    lb1.place(relx=0.1, rely=0.4, relwidth=0.1, relheight=0.15)
    inp2.place(relx=0.3, rely=0.4, relwidth=0.5, relheight=0.15)
    rememberme = Checkbutton(lroot, text='记住我', variable=CheckVar, onvalue=1, offvalue=0)
    rememberme.pack()
    btn1 = Button(lroot, text='确定', command=hand_login)
    btn1.place(relx=0.4, rely=0.6, relwidth=0.2, relheight=0.1)
    lroot.mainloop()


def main_gui():
    global workBox
    global root
    global ButtonsL1, ButtonsL2, present
    root = Tk()
    root.title('快去写作业！')
    root.geometry(str(main_width) + 'x' + str(main_height) + '+260+100')

    wkList = Frame(root, relief=RAISED)
    wkList.place(relx=0.0, rely=0.1)

    rButtons = Frame(root, relief=GROOVE)
    rButtons.place(relx=0.67, rely=0.2)

    ButtonsL1 = Frame(root, relief=GROOVE)
    ButtonsL1.place(relx=0, rely=0,height=30)
    ButtonsL2 = Frame(root, relief=GROOVE)
    ButtonsL2.place(relx=0, rely=0.05,height=30)
    present = ButtonsL1

    Button(ButtonsL1, text='所有', command=lambda c='all': {
        change_course(c),
        add_frame()
    }, font={'黑体', 12}, bg='lightgreen', fg='purple', relief=GROOVE).pack(side=LEFT)
    workBox = Listbox(wkList, width=75, height=28, font=('黑体', 12))
    workBox.pack()
    # add_frame()

    btn1 = Button(rButtons, text='待提交作业（时间升序）', command=lambda: {
        change_status(0),
        add_frame()
    }, width=40, relief=GROOVE)
    btn1.pack(fill=X)

    btn2 = Button(rButtons, text='显示所有作业', command=lambda: {
        change_status(1),
        add_frame()
    }, relief=GROOVE)
    btn2.pack(fill=X)

    btn3 = Button(rButtons, text='刷新数据', command=lambda: {
        added(),
        get_info(),
        # add_frame(),
    }, relief=GROOVE)
    btn3.pack(fill=X)

    space = Label(rButtons, text='')
    space.pack(fill=X)
    logoutBtn = Button(rButtons, text='注销', command=logout, relief=GROOVE)
    logoutBtn.pack(fill=X)

    root.mainloop()


lroot = {}

CheckVar = {}
loginLb = {}
inp1 = {}
inp2 = {}

if not auto_login():
    login_gui()

if not check_login():
    exit()

courses = get_course()
# 获取信息

threading.Thread(target=get_info).start()
# get_info(courses)
root = {}

main_gui()
