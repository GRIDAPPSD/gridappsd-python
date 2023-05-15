import json
from gridappsd import topics
from typing import Optional



class Query:
    """ Class to create and execute request to query timeseries data
    """
    
    def __init__(self, measurement):
        self.queryMeasurement = measurement
        self.queryFilter = []
        self.selectCriteria = []
        self.key = None

    def select(self, *keys):
        """ Defines what fields should be returned from the query.
        
        If this function is not called or is called without argument then 
        all the fields are returned.
        
        :param keys: list of fields to be returned 
        """
        for key in keys:
            self.selectCriteria.append(key)
        return self

    def first(self, n=Optional[int]):
        """ Method to add request to return first or oldest data to the query.
        
        When n is specified, query will return first or oldest 'n' rows.
        
        :param n:  
        """
        if n is not None:
            self.first = n;
        return self

    def last(self, n=Optional[int]):
        """ Method to add request to return last or latest data to the query.
        
        When n is specified, query will return last or latest 'n' rows.
        
        :param n:  
        """
        if n is not None:
            self.last = n;
        return self
    
    def ge(self, value):
        """ Method to add 'value greater than or equal to' filter to a key.
        
        :param value:  
        """
        if self.key is None:
            raise ValueError("Key is not specified. Call where_key first.")
        obj = {"key":self.key,"ge":value}
        self.queryFilter.append(obj)
        return self
    
    def le(self, value):
        """ Method to add 'value less than or equal to' filter to a key.
        
        :param value:  
        """
        if self.key is None:
            raise ValueError("Key is not specified. Call where_key first.")
        obj = {"key":self.key,"le":value}
        self.queryFilter.append(obj)
        return self
    
    def eq(self, value):
        """ Method to add 'value equal to' filter to a key.
        
        :param value:  
        """
        if self.key is None:
            raise ValueError("Key is not specified. Call where_key first.")
        obj = {"key":self.key,"eq":value}
        self.queryFilter.append(obj)
        return self
    
    def between(self, value1, value2):
        """ Method to add 'value between' value1 and value2 filter to a key.
        
        :param value1: defines 'greater than equal to' filter for key's value
        :param value2: defines 'less than equal to' filter for key's value
        """
        if self.key is None:
            raise ValueError("Key is not specified. Call where_key first.")
        obj = {"key":self.key,"ge":value1}
        self.queryFilter.append(obj)
        obj = {"key":self.key,"le":value2}
        self.queryFilter.append(obj)
        return self
    
    def where_key(self, key):
        self.key = key
        return self

    def execute(self, gridappsd_obj):
        del self.key 
        response = gridappsd_obj.get_response(topics.REQUEST_TIMESERIES_DATA, json.dumps(self.__dict__))
        return response