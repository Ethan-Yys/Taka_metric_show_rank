import sys

from django.shortcuts import render

# Create your views here.
import json
from random import randrange

from django.http import HttpResponse
from rest_framework.views import APIView

from pyecharts.charts import Line
from pyecharts import options as opts
from pyecharts import options as opts
from pyecharts.charts import Bar, Timeline

from jinja2 import Environment, FileSystemLoader
from pyecharts.globals import CurrentConfig

import pandas as pd
from pathlib import Path
import time
import datetime
import os
from Taka_metric_show_rank.settings import BASE_DIR


# Create your views here.
def response_as_json(data):
    json_str = json.dumps(data)
    response = HttpResponse(
        json_str,
        content_type="application/json",
    )
    response["Access-Control-Allow-Origin"] = "*"
    return response


def json_response(data, code=200):
    data = {
        "code": code,
        "msg": "success",
        "data": data,
    }
    return response_as_json(data)


def json_error(error_string="error", code=500, **kwargs):
    data = {
        "code": code,
        "msg": error_string,
        "data": {}
    }
    data.update(kwargs)
    return response_as_json(data)


JsonResponse = json_response
JsonError = json_error

CurrentConfig.GLOBAL_ENV = Environment(
    loader=FileSystemLoader("./demo/templates"))

global_data = {
    'df': None
}

Taka_group = ['A_0_499', 'B_500_999', 'C_1000_1499', 'D_1500_1999',
              'E_2000_2499', 'F_2500_2999', 'G_3000_3499', 'H_3500_3999',
              'I_4000_4499', 'J_4500_4999', 'K_5000_5499', 'L_5500_5999',
              'M_6000_6499', 'N_6500_6999', 'O_7000_7499', 'P_7500_7999',
              'Q_8000_8499', 'R_8500_8999', 'S_9000_9499', 'T_9500_9999', 'avg']

selectItem = 'finish rate'


def get_color():
    color = []
    for i in range(len(Taka_group)):
        if Taka_group[i] == 'G_3000_3499':
            color.append('#FF0000')
        elif Taka_group[i] == 'avg':
            color.append('#68F709')
        elif Taka_group[i] == 'H_3500_3999':
            color.append('#F79709')
        else:
            color.append('#5CACEE')
    return color


def convert_percent(value):
    """
    转换字符串百分数为float类型小数
    - 移除 %
    - 除以100转换为小数
    """
    new_value = value.replace('%', '')
    return float(new_value)


def get_data(selectItem):
    """
    读取获取路径内所有的csv文件为dataframe
    """
    df = []
    # 记录需要去除百分号的几个指标
    object_type = [
        'play rate',
        'finish rate',
        'share rate',
        'like rate',
        'download rate',
        'comment rate']
    files = Path(os.path.join(BASE_DIR, 'data')).glob('*.csv')  # get all csvs in your dir.
    for index, file in enumerate(files):
        df.append(pd.read_csv(file, index_col=0))
        for column in object_type:
            df[index][column] = pd.to_numeric(
                df[index][column].apply(convert_percent), errors='coerce')
        df[index] = df[index].drop(['total'])
        df[index] = df[index].append(df[index].mean().rename('avg'))
        df[index] = df[index][[selectItem]]
    return df


# 获取最近day天的日期
def get_date(day=30):
    days = []
    for i in range(day, 0, -1):
        thisday = (datetime.datetime.now() - datetime.timedelta(days=i))
        days.append(thisday.strftime("%m-%d"))
    return days


# 获取文件名中的日期作为x轴
def get_axis_x(path=os.path.join(BASE_DIR, 'data')):
    date_name = []
    for _, _, files in os.walk(path):
        for element in files:
            date_name.append(element[4:6] + '-' + element[6:-4])
    return date_name


# 提取group_name组,metric_name指标的指标值
def filter_data(df, group_name, metric_name='finish rate'):
    value = []
    for i in range(len(df)):
        temp = df[i].loc[group_name].loc[metric_name]
        value.append(temp)
    return value


def get_task_data(df, selectItem):
    Taka_data = []
    for index in Taka_group:
        Taka_data.append(filter_data(df, index, metric_name=selectItem))
    return Taka_data


def timeline_base(selectItem) -> Timeline:
    df = get_data(selectItem)
    for i in range(len(df)):
        df[i] = df[i].reset_index()
        df[i]['color'] = get_color()

    tl = Timeline()
    x = get_axis_x()

    for i in range(len(df)):
        df_sub = df[i].sort_values(by=selectItem)
        cats_list = list(df_sub['index'])
        value_list = list(df_sub[selectItem])
        color_list = list(df_sub['color'])
        y = []
        for j in range(21):
            y.append(
                opts.BarItem(
                    name=cats_list[j],
                    value=value_list[j],
                    itemstyle_opts=opts.ItemStyleOpts(color=color_list[j])
                )
            )

        bar = (
            Bar(init_opts=opts.InitOpts())
                .add_xaxis(xaxis_data=cats_list)
                .add_yaxis(series_name='', y_axis=y, label_opts=opts.LabelOpts(position="right", font_weight="bold"),
                           category_gap=20)
                .reversal_axis()
                .set_global_opts(
                title_opts=opts.TitleOpts("{}指标排名（时间：{}）".format(selectItem, x[i]), pos_left=350, padding=[30, 20]),
                xaxis_opts=opts.AxisOpts(min_='dataMin')
            )
        )
        tl.add(bar, "{}".format(x[i]))
        tl.add_schema(play_interval=600, is_loop_play=False)
    c = tl.dump_options_with_quotes()
    return c


class ChartView(APIView):
    def post(self, request, *args, **kwargs):
        selectItem = request.data['selectItem']
        # print(type(selectItem))
        return JsonResponse(json.loads(timeline_base(selectItem)))


class IndexView(APIView):
    def get(self, request, *args, **kwargs):
        return HttpResponse(content=open("./templates/index.html").read())