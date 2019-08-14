# _*_ coding: utf-8 _*_
#! /usr/bin/env python
# @Author   : aJ0ker
# @Time     : 2019/8/9 15:25
# @File     : app.py

'''
async web application.
'''

import logging  #记录错误信息
logging.basicConfig(level=logging.INFO)     #指定info级别通知

import asyncio,os,json,time
import orm

from datetime import datetime
from aiohttp import web
from jinja2 import Environment,FileSystemLoader
from coroweb import add_routes,add_static
from models import Blog
from config import configs


#编写处理函数
def index(request):     #该函数作用是处理URL，之后将与具体URL绑定。参数aiohttp.web.request实例包含了所有浏览器发送过来的HTTP协议里面的信息，一般不用自己构造
    summary = 'Lorem ipsum dolor sit amet,consectetur adipisicing elit,sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    blogs = [
        Blog(id='1',name='Test Blog',summary=summary,created_at=time.time()-120),
        Blog(id='2',name='Something New',summary=summary,created_at=time.time()-3600),
        Blog(id='3',name='Learn Python',summary=summary,created_at=time.time()-7200)
    ]
    return {
        '__template__':'blogs.html',
        'blogs':blogs
    }
    #response反馈回服务器网页信息，网页的HTML源码就在body中
    #返回值aiohttp.web.response实例，由web.Response(body='')构造，继承自StreamResponse，功能为构造一个HTTP响应
    #类声明class aiohttp.web.Response(*,status=200,headers=None,content_type=None,body=None,text=None)
    #HTTP协议格式为：POST /PATH /1.1 /r/n Header1:Value /r/n .. /r/n HeaderN:Value /r/n Body:Data

def init_jinja2(app,**kw):
    logging.info('init jinja2..')
    options = dict(
        autoescape = kw.get('autoescape',True),
        block_start_string = kw.get('block_start_string','{%'),
        block_end_string = kw.get('block_end_string','%}'),
        variable_start_string = kw.get('variable_start_string','{{'),
        variable_end_string = kw.get('variable_end_string','}}'),
        auto_reload = kw.get('auto_reload',True)
    )
    path = kw.get('path',None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'templates')
    logging.info('set jinja2 template path: %s' % path)
    env = Environment(loader=FileSystemLoader(path),**options)
    filters = kw.get('filters',None)
    if filters is not None:
        for name,f in filters.items():
            env.filters[name] = f
        app['__templating__'] = env

# middleware拦截器，一个URL在被函数处理前，可以经过一系列的middleware处理。
#记录URL日志的logger定义如下
@asyncio.coroutine
def logger_factory(app,handler):
    @asyncio.coroutine
    def logger(request):
        logging.info('Request: %s %s' % (request.method,request.path))
        # yield from asyncio.sleep(0.3)
        return (yield from handler(request))
    return logger

# response这个middleware把返回值转换为web.Response对象再返回，以保证满足aiohttp要求
@asyncio.coroutine
def response_factory(app,handler):
    @asyncio.coroutine
    def response(request):
        logging.info('Response handler..')
        r = yield from handler(request)
        if isinstance(r,web.StreamResponse):
            return r
        if isinstance(r,bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r,str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r,dict):
            template = r.get('__template__')
            if template is None:
                resp = web.Response(body=json.dumps(r,ensure_ascii=False,default=lambda o: o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                r['__user__'] = request.__user__
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r,int) and t >= 100 and t < 600:
            return web.Response(t)
        if isinstance(r,tuple) and len(r) == 2:
            t, m = r
            if isinstance(t,int) and t >= 100 and t < 600:
                return web.Response(t,str(m))
        # default
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp
    return response

# 使用jinja2的filter过滤器把Blog的创建日期由浮点数转换成日期字符串
def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u'%s秒前' % delta
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta <86400:
        return u'%s小时前' % (delta // 3600)
    if delta < 604800:
        return u'%s天前' % (delta //86400)
    dt = datetime.fromtimestamp(t)
    return u'%s年%s约%s日' % (dt.year,dt.month,dt.day)

#创建Web服务器，并将处理函数注册进其应用路径(Application.router)
@asyncio.coroutine
async def init(loop):
    await orm.create_pool(loop=loop,**configs.db)
    app = web.Application(loop = loop)  #创建Web服务器实例app，也就是aiohttp.web.Application类的实例，该实例作用是处理URL、HTTP协议
    init_jinja2(app,filters=dict(datetime=datetime_filter))
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