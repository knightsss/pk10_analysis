# -*- coding: utf-8 -*-
__author__ = 'shifeixiang'

from django.views.decorators.csrf import csrf_exempt    #用于处理post请求出现的错误
from django.shortcuts import render_to_response
from append_predict.models import ProbUser
from append_predict.models import KillPredict,PredictLottery
from append_predict.thread import ThreadControl
import math
#追加方式规则
from append_predict.predict_append_rule_100 import spider_predict_selenium,get_purchase_list

from append_predict.spider_pk10 import get_html_result,get_lottery_id_number,load_lottery_predict
import time
import datetime
class Singleton(object):
    def __new__(cls, *args, **kw):
        if not hasattr(cls, '_instance'):
            orig = super(Singleton, cls)
            cls._instance = orig.__new__(cls, *args, **kw)
        return cls._instance

class SingleDriver(Singleton):
    # def __init__(self, driver):
    #   self.driver = driver
    def get_driver(self):
        return self.driver
    def set_driver(self, driver):
        self.driver = driver

class SingleDriverMultiple(Singleton):
    # def __init__(self, driver):
    #   self.driver = driver
    def get_driver(self):
        return self.driver
    def set_driver(self, driver):
        self.driver = driver

#主页面
def predict_main(request):
    # ProbTotals.objects.all().delete()
    # thread_list =  ProbUser.objects.get(thread_name=th_name)
    prob_user_list =  ProbUser.objects.all()
    for prob_user in prob_user_list:
        c  = ThreadControl()
        try:
            #查看是否处于活跃状态
            status = c.is_alive(prob_user.user_name)
            if status:
                #设置状态为1
                prob_user.user_status = 1
                prob_user.save()
            else:
                #设置状态为0
                prob_user.user_status = 0
                prob_user.save()
        except:
            print prob_user.user_name, " not start"
            prob_user.user_status = 0
            prob_user.save()
    return render_to_response('append_predict_main.html',{"prob_user_list":prob_user_list})


@csrf_exempt   #处理Post请求出错的情况
def control_predict_thread(request):
    user_name = request.POST['user_name']
    control = request.POST['control']
    info_dict = {}

    #显示活跃状态
    prob_user = ProbUser.objects.get(user_name=user_name)
    if control == 'start':
        driver = spider_predict_selenium()
        info_dict["driver"] = driver
        #状态信息
        c  = ThreadControl()
        #出现错误，则线程不存在，因此启动线程
        try:
            status = c.is_alive(user_name)
            print "thread is alive? ",status
            if status:
                print "thread is alive,caonot start twice!"
            else:
                print "start ..........thread1"
                c.start(user_name, info_dict)
        except:
            print "thread is not alive start!!!"
            c.start(user_name, info_dict)
        prob_user.user_status = 1
        prob_user.save()
    if control == 'stop':
        c  = ThreadControl()
        try :
            c.stop(user_name)
            prob_user.user_status = 0
            prob_user.save()
        except:
            print "not thread alive"
    prob_user_list =  ProbUser.objects.all()
    return render_to_response('append_predict_main.html',{"prob_user_list":prob_user_list})



def spider_save_predict(interval):
    #爬取当天结果,存入objects
    html_json = get_html_result()
    if html_json == '':
        pass
    else:
        load_lottery_predict(html_json)

        #获取models predict最新值
        lottery_id, kill_predict_number, xiazhu_money = get_predict_model_value()
        print "lottery_id",lottery_id
        if lottery_id == 0:
            print "no predict record in history"
        else:
            #获取该期的开奖号码
            lottery_num,lottery_time = get_lottery_id_number(lottery_id)
            print "lottery_num:",lottery_num
            if (lottery_num):
                #计算命中率并更新models
                #print "save lottery_number"
                calculate_percisoin(lottery_id, lottery_num, kill_predict_number, lottery_time, xiazhu_money)
            else:
                print "pay interface lottery id request faild"

    get_predict_kill_and_save(interval)

def get_predict_kill_and_save(interval):
    #爬取下一期predict
    driver = interval["driver"]
    predict_lottery_id,purchase_number_list,purchase_number_list_desc,predict_number_all_list_str = get_purchase_list(interval)
    if predict_lottery_id != 0:
        #更新models
        print "save:",predict_lottery_id,'  ',purchase_number_list
        #current_date = time.strftime('%Y-%m-%d',time.localtime(time.time()))

        #根据时间判断日期是否加一天
        jump_flag_date = time.strftime("%H:%M:%S", time.localtime())
        if jump_flag_date > '23:57:59' or jump_flag_date <= '00:03:00':
            current_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            current_date = time.strftime('%Y-%m-%d',time.localtime(time.time()))
        save_predict_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #基于前面开奖结果计算下注金额基础(1为基准值)
        xiazhu_money = get_xiazhu_money_base_on_history_purchase_record(purchase_number_list, current_date)

        #保存
        p = KillPredict(kill_predict_date=current_date, save_predict_time=save_predict_time, lottery_id = int(predict_lottery_id), kill_predict_number = purchase_number_list,
                            kill_predict_number_desc=purchase_number_list_desc, predict_total=0, target_total=0, predict_accuracy=0,
                            predict_number_all=predict_number_all_list_str, xiazhu_money=xiazhu_money, gain_money=0, is_xiazhu=0, input_money=0)
        p.save()

#基于历史购买记录计算本期的下注金额基数
def get_xiazhu_money_base_on_history_purchase_record(purchase_number_list, current_date,):
    xiazhu_predicts = KillPredict.objects.filter(kill_predict_date=current_date).order_by("-lottery_id")
    xiahu_money_result = 1
    gain_money_total = 0
    for xiazhu_predict in xiazhu_predicts:
        if (xiazhu_predict.is_xiazhu == 1 and xiazhu_predict.gain_money > 0):
            break
        if (xiazhu_predict.is_xiazhu == 1 and xiazhu_predict.gain_money < 0):
            print "gain_money_total sub:",gain_money_total
            gain_money_total = gain_money_total + xiazhu_predict.gain_money
    print "gain_money_total total:",gain_money_total
    current_purchase_length = 0
    for purchase_number in purchase_number_list.split(','):
        if purchase_number == '0':
            continue
        else:
            current_purchase_length = len(purchase_number.split('|'))
            break
    print "current_purchase_length:",current_purchase_length
    if current_purchase_length == 0:
        xiahu_money_result = 0
    else:
        if gain_money_total < 0:
            xiahu_money_result = math.fabs(gain_money_total/(9.9 - current_purchase_length))
        else:
            xiahu_money_result = 1
        print "xiahu_money_result:",xiahu_money_result
    print "base xiazhu:",xiahu_money_result
    xiahu_money_result = int(round(xiahu_money_result))
    print "result xiazhu:",xiahu_money_result
    return xiahu_money_result

#获取最新一期的预测值得相关信息
def get_predict_model_value():
    current_date = time.strftime('%Y-%m-%d',time.localtime(time.time()))
    predicts = KillPredict.objects.filter(kill_predict_date=current_date).order_by("-lottery_id")
    lottery_id = 0
    kill_predict_number = 0
    xiazhu_money = 0
    if len(predicts) == 0:
        print "predicts is null"
    else:
        lottery_id = predicts[0].lottery_id
        kill_predict_number = predicts[0].kill_predict_number
        xiazhu_money = predicts[0].xiazhu_money
    return lottery_id, kill_predict_number, xiazhu_money


def calculate_percisoin(lottery_id, lottery_num, kill_predict_number, lottery_time, xiazhu_money):
    #lottery_num 转数组，kill_predict_number 转二位数组
    result_data = lottery_num.split(',')

    purchase_number_list = []
    for elet in kill_predict_number.split(','):
        tmp_list = elet.split('|')
        purchase_number_list.append(tmp_list)

    if len(result_data) == len(purchase_number_list):
        all_count = 0
        target_count = 0
        for i in range(len(result_data)):
            if  '0' in purchase_number_list[i]:
                print "predict invalid!"
            else:
                print " result_data[i],purchase_number_list[i]:", str(int(result_data[i])),purchase_number_list[i]
                if str(int(result_data[i])) in purchase_number_list[i]:
                    target_count = target_count +  1
                all_count = all_count + len(purchase_number_list[i])
        print "all_count,target_count:", all_count,target_count
        if all_count == 0:
            predict_accuracy = 0
            gain_money = 0
        else:
            predict_accuracy = float(float(target_count)/float(all_count))
            gain_money = (target_count * 9.985 - all_count) * xiazhu_money
            print float(float(target_count)/float(all_count))
        try:
            p = KillPredict.objects.get(lottery_id=lottery_id)
            p.kill_predict_time = lottery_time
            p.lottery_number = lottery_num
            p.predict_total = all_count
            p.target_total = target_count
            p.predict_accuracy = predict_accuracy
            p.gain_money = gain_money
            p.input_money = all_count * xiazhu_money
            #p.is_xiazhu = 1
            p.save()
        except:
            print "the ",lottery_id," is repeat!!!"
    else:
        print 'length error'

#删除当天的信息
def delete_kill_predict_current_date(request):

    current_date = time.strftime('%Y-%m-%d',time.localtime(time.time()))

    KillPredict.objects.filter(kill_predict_date=current_date).delete()

    obj_pro_predict = KillPredict.objects.filter(kill_predict_date=current_date)
    return render_to_response('test.html',{"obj_pro_predict":obj_pro_predict})


import json
from django.http import HttpResponse
#获取杀号预测数据接口
def get_predict(request):
    current_date = time.strftime('%Y-%m-%d',time.localtime(time.time()))
    result_info = {}
    # lotterys = KillPredict.objects.filter(lottery_date=current_date)
    #获取预测的lottery id 和预测的号码
    obj_pro_predict = KillPredict.objects.filter(kill_predict_date=current_date).order_by("-lottery_id")
    if len(obj_pro_predict) == 0:
        pass
    else:
        result_info['predict_lottery_id'] = int(obj_pro_predict[0].lottery_id)
        result_info['predict_number_list'] = obj_pro_predict[0].kill_predict_number
        result_info['predict_number_list_desc'] = obj_pro_predict[0].kill_predict_number_desc
        print obj_pro_predict[0].lottery_id
        print obj_pro_predict[0].kill_predict_number

    #获取目前最新的开奖lottery id
    # html_json = get_html_result()
    # if html_json == '':
    #     result_info['last_lottery_id'] = 999999
    #     #pass
    # else:
    #     load_lottery_predict(html_json)
    obj_pro_lottery = PredictLottery.objects.filter(lottery_date=current_date).order_by("-lottery_id")
    if len(obj_pro_lottery) == 0:
        result_info['last_lottery_id'] = 0
        pass
    else:
        result_info['last_lottery_id'] = int(obj_pro_lottery[0].lottery_id)
        result_info['lottery_number'] = obj_pro_lottery[0].lottery_number
        print obj_pro_lottery[0].lottery_id
    print "obj_pro",obj_pro_predict
    return HttpResponse(json.dumps(result_info), content_type="application/json")


#删除当天的信息
def delete_kill_predict_current_date(request):

    current_date = time.strftime('%Y-%m-%d',time.localtime(time.time()))

    KillPredict.objects.filter(kill_predict_date=current_date).delete()

    obj_pro_predict = KillPredict.objects.filter(kill_predict_date=current_date)
    return render_to_response('test.html',{"obj_pro_predict":obj_pro_predict})




import json
from django.http import HttpResponse
#获取杀号预测数据接口
def get_predict(request):
    current_date = time.strftime('%Y-%m-%d',time.localtime(time.time()))
    result_info = {}
    # lotterys = KillPredict.objects.filter(lottery_date=current_date)
    #获取预测的lottery id 和预测的号码
    obj_pro_predict = KillPredict.objects.filter(kill_predict_date=current_date).order_by("-lottery_id")
    if len(obj_pro_predict) == 0:
        pass
    else:
        result_info['predict_lottery_id'] = int(obj_pro_predict[0].lottery_id)
        result_info['predict_number_list'] = obj_pro_predict[0].kill_predict_number
        result_info['predict_number_list_desc'] = obj_pro_predict[0].kill_predict_number_desc
        result_info['xiazhu_money'] = obj_pro_predict[0].xiazhu_money
        result_info['save_predict_time'] = obj_pro_predict[0].save_predict_time
        print obj_pro_predict[0].lottery_id
        print obj_pro_predict[0].kill_predict_number

    obj_pro_lottery = PredictLottery.objects.filter(lottery_date=current_date).order_by("-lottery_id")
    if len(obj_pro_lottery) == 0:
        result_info['last_lottery_id'] = 0
        pass
    else:
        result_info['last_lottery_id'] = int(obj_pro_lottery[0].lottery_id)
        result_info['lottery_number'] = obj_pro_lottery[0].lottery_number
        print obj_pro_lottery[0].lottery_id
    print "obj_pro",obj_pro_predict
    return HttpResponse(json.dumps(result_info), content_type="application/json")