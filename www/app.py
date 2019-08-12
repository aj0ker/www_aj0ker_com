# _*_ coding: utf-8 _*_
#! /usr/bin/env python
# @Author   : aJ0ker
# @Time     : 2019/8/9 15:25
# @File     : app.py

#创建连接池
import logging  #记录错误信息
logging.basicConfig(level=logging.INFO)     #指定info级别通知
import asyncio,os,json,time
from datetime import datetime
from aiohttp import web
import aiomysql
from math import log
from orm import Model,StringField,IntegerField

#编写处理函数
def index(request):     #该函数作用是处理URL，之后将与具体URL绑定。参数aiohttp.web.request实例包含了所有浏览器发送过来的HTTP协议里面的信息，一般不用自己构造
    return web.Response(body=b'<h1>Hello,world!</h1>',content_type='text/html')     #response反馈回服务器网页信息，网页的HTML源码就在body中
    #返回值aiohttp.web.response实例，由web.Response(body='')构造，继承自StreamResponse，功能为构造一个HTTP响应
    #类声明class aiohttp.web.Response(*,status=200,headers=None,content_type=None,body=None,text=None)
    #HTTP协议格式为：POST /PATH /1.1 /r/n Header1:Value /r/n .. /r/n HeaderN:Value /r/n Body:Data

#创建Web服务器，并将处理函数注册进其应用路径(Application.router)
@asyncio.coroutine
async def init(loop):
    app = web.Application(loop = loop)  #创建Web服务器实例app，也就是aiohttp.web.Application类的实例，该实例作用是处理URL、HTTP协议
    app.router.add_route('GET','/',index)
    #将处理函数注册到创建app.router中，router默认为UrlDispatcher实例，UrlDispatcher类中有方法add_route(method,path,handler,*,name=None,expect_handler=None),该方法将处理函数(其参数名为handler)与对应的URL（HTTP方法method,URL路径path）绑定，浏览器敲击URL时返回处理函数的内容
    app_runner = web.AppRunner(app)
    await app_runner.setup()
    srv = await loop.create_server(app_runner.server,'127.0.0.1',9000)     #用协程创建监听服务，并使用aiohttp中的HTTP协议簇(protocol_factory)
    #yield from返回一个创建好的，绑定IP、端口、HTTP协议簇的监听服务的协程，yield from的作用是使srv的行为模式和loop.create_server()一致
    logging.info('server started at http://127.0.0.1:9000..')
    return srv

'''
1.1 Application构造函数
def __init__(self,*,logger=web_logger,loop=None,router=None,handler_factory=RequestHandlerFactory,middlewares=(),debug=False):
1.2 使用app时，首先要将URLs注册进router，再用aiohttp.ResquestHandlerFactory作为协议簇创建套接字
1.3 aiohttp.RequestHandlerFactory可以用make_handler()创建，用来处理HTTP协议，接下来将会看到
'''

loop = asyncio.get_event_loop()     #创建协程，loop=asyncio.get_event_loop()，为asyncio.BaseEventLoop的对象，协程的基本单位
loop.run_until_complete(init(loop))     #运行协程，直到完成,BaseEventLoop.run_until_complete(future)
loop.run_forever()      #运行协程，直到调用stop(),BaseEventLoop.run_forever()