
import datetime
import os


# 获取最近day天的日期
def get_date(day=30):
    days = []
    for i in range(day, 0, -1):
        thisday = (datetime.datetime.now() - datetime.timedelta(days=i))
        days.append(thisday.strftime("%m-%d"))
    return days


# 获取文件名中的日期作为x轴
def get_axis_x(path='../data'):
    date_name = []
    for _, _, files in os.walk(path):
        for element in files:
            date_name.append(element[4:6] + '-' + element[6:-4])
    return date_name

x = get_date()
y = get_axis_x()

print(x)
print(y)
print('end')