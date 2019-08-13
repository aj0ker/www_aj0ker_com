# _*_ coding: utf-8 _*_
#! /usr/bin/env python
# @Author   : aJ0ker
# @Time     : 2019/8/13 17:29
# @File     : apis.py

'''
JSON API definition.
'''

import json,logging,inspect,functools

class Page(object):
    '''
    Page object for display pages.
    '''

    def __init__(self,item_count,page_index=1,page_size=10):
        '''
        Init Pagination by item_count,page_index and page_size.

        >>> p1 = Page(100,1)
        >>> p1.page_count
        10
        >>> 
        '''