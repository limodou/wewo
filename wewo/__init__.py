# Author: limodou@gmail.com
# License: New BSD
#
# This is an simple workflow package
#

import time, threading
import logging

__all__ = ['Activity', 'Transition', 'BasicProcessEngine', 'Process',
    'Application', 'get_default_workitems_queue']

log = logging.getLogger('wewo')

class Error(Exception): pass
__default_workitems_queue__ = None

def now():
    import datetime
    return datetime.datetime.now()

def get_default_workitems_queue():
    global __default_workitems_queue__
    
    if not __default_workitems_queue__:
        __default_workitems_queue__ = BasicWorkItemQueue()
    return __default_workitems_queue__

def create_uuid():
    from uuid import uuid4
    return uuid4().hex

class StorageMixin(object):
    def save(self):
        """
        Save an object to a persistant system, but this method
        will do nothing, so you should implement real one yourself
        
        And object should has a serial method. And save() will
        return and Id value
        """
        self.serial()
        return create_uuid()
    
    @classmethod
    def get(cls, id):
        """
        Get data from a persistant system according the category, and 
        also create an object according the cls parameter
        """
        pass
    
class Event(object):
    def __init__(self, name, sender):
        self.sender = sender
        self.name = name
        
    def __repr__(self):
        return '%s(%r)' % (self.name, self.sender)
        
class EventManager(object):
    def __init__(self):
        self.listensers = {}
    
    def emit(self, event):
        for f in self.listensers.get(event.name, []) + self.listensers.get(None, []):
            f(event)
            
    def connect(self, function, name=None):
        funcs = self.listensers.setdefault(name, [])
        funcs.append(function)

class Application(object):
    def __init__(self):
        pass
    
    def start(self, workitem):
        workitem.finish()
    
    def finish(self, workitem):
        pass

class WorkItem(StorageMixin):
    def __init__(self, process, activity):
        self.status = -1 #-1 is ready, 0 is running, 1 is finished
        self.process = process
        self.activity = activity
        #persist the workitem
        self.id = self.save()
        self.begin_time = None
        self.finish_time = None
        
    def start(self):
        self.status = 0
        self.begin_time = now()
        if self.activity.application:
            self.activity.application.start(self)
            event = Event('WorkItemStarted', self)
            self.process.event.emit(event)
        else:
            event = Event('WorkItemStarted', self)
            self.process.event.emit(event)
            self.finish()
            
    def finish(self, data=None):
        self.status = 1
        self.finish_time = now()
        event = Event('WorkItemFinished', self)
        self.process.event.emit(event)
        self.process.put(self, data)
        
    def serial(self):
        return {'process':self.process.id, 'activity':self.activity.name, 
            'status':self.status}
        
    def __repr__(self):
        return 'WorkItem(%r)' % (self.activity)
        
class Activity(object):
    def __init__(self, name=None, application=None, data=None):
        self.name = name
        self.application = application
        self.data = data
        self.process = None
        
    def __repr__(self):
        return '%s(%s.%s)' % (self.__class__.__name__, self.process.__name__, self.name)
    
    def __property_config__(self, process):
        self.process = process
    
class Transition(object):
    def __init__(self, from_, to_, condition=None):
        self.from_ = from_
        self.to_ = to_
        self.condition = condition

    def IS(self, data):
        if not self.condition:
            return True
        else:
            return self.condition(data)
        
    def __repr__(self):
        return 'Transition(%s, %s)' % (self.from_, self.to_)
    
class BasicWorkItemQueue(object):
    def __init__(self):
        from collections import deque
        
#        self.put_callback = None
        self.queue = deque()
        
#    def set_callback(self, name, func):
#        if name == 'put':
#            self.put_callback = func
            
    def put(self, workitem):
        self.queue.append(workitem)
#        if self.put_callback:
#            self.put_callback()
        
    def get(self):
        try:
            return self.queue.popleft()
        except IndexError:
            return None
  
class BasicProcessEngine(threading.Thread):
    def __init__(self, queue=None):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.queue = queue or get_default_workitems_queue()
        self.is_stop = False
        
    def stop(self):
        """
        finish a process
        """
        self.is_stop = True
        
    def run(self):
        while 1:
            if self.is_stop: break
            x = self.queue.get()
            if x:
                workitem, data = x
                self.do(workitem, data)
            else:
                time.sleep(0.1)
        
    def do(self, workitem, data=None):
        if workitem.status == -1:
            workitem.start()
#            if workitem.status == 1:
#                self.put(workitem)
        elif workitem.status == 1:
            workitem.process.do_transition(workitem, data)
            
class ProcessMetaClass(type):
    def __init__(cls, name, bases, dct):
        super(ProcessMetaClass, cls).__init__(name, bases, dct)
        
        cls.activities = {}
        cls.transitions = {}
        
        for base in bases:
            if hasattr(base, 'activies'):
                cls.activities.update(base.activities)
        
        for name in dct.keys():
            attr = dct[name]
            
            #process Transition
            if name == 'Transitions':
                nodes = {}
                starts, ends = [], []
                for x in attr:
                    if isinstance(x, (tuple, list)):
                        if len(x) == 2:
                            from_, to_ = x
                            f = None
                        elif len(x) == 3:
                            from_, to_, f = x
                        else:
                            raise Error('Transition should be defined as '
                                '(activity_name, activity_name) or '
                                '(activity_name, activity_name, condition_function)')
                        trans = Transition(from_, to_, condition=f)
                    else:
                        trans = attr
                    
                    #process start transition
                    d = nodes.setdefault(trans.from_, {'in':0, 'out':0})
                    d['out'] += 1
                    if d['in'] == 0 and trans.from_ not in starts:
                        starts.append(trans.from_)
                    if d['out'] > 0 and trans.from_ in ends:
                        ends.remove(trans.from_)
                        
                    #process finish transition
                    d = nodes.setdefault(trans.to_, {'in':0, 'out':0})
                    d['in'] += 1
                    if d['out'] == 0 and trans.to_ not in ends:
                        ends.append(trans.to_)
                    if d['in'] > 0 and trans.to_ in starts:
                        starts.remove(trans.to_)
                        
                    t = cls.transitions.setdefault(trans.from_, [])
                    t.append(trans)
                    
                #process start transition
                if len(starts) != 1:
                    raise Error('There should be only one start activity, but found %d' % len(starts))
                cls.transitions[None] = [Transition(None, starts[0])]
                
                #process finish transition
                if len(ends) == 0:
                    raise Error('There should be at least one finish activity, but found 0')
                for x in ends:
                    trans = Transition(x, None)
                    t = cls.transitions.setdefault(x, [])
                    t.append(trans)
                    
            if name == 'Activities':
                for x in attr:
                    if isinstance(x, (str, unicode)):
                        act = Activity(x)
                    else:
                        act = x
                    cls.activities[x.name] = act
                    act.__property_config__(cls)
            
            if isinstance(attr, Activity):
                cls.activities[name] = attr
                attr.name = name
                attr.__property_config__(cls)
    
class Process(StorageMixin):
    __metaclass__ = ProcessMetaClass
    
    engine_cls = BasicProcessEngine
    event_cls = EventManager
    
    def __init__(self, queue=None):
        self._engine = None
        self._event = None
        self.status = -1
        self.queue = queue or get_default_workitems_queue()
        self.begin_time = None
        self.finish_time = None
        self.id = None
        self.id = self.save()
        
    @property
    def engine(self):
        if not self._engine:
            self._engine = self.engine_cls(self)
        return self._engine
            
    @property
    def event(self):
        if not self._event:
            self._event = self.event_cls()
        return self._event
    
    def start(self):
        """
        start a process
        """
        self.status = 0
        self.begin_time = now()
        self.save()
        
        event = Event('ProcessStarted', self)
        self.event.emit(event)
        self.do_transition(None)
        
    def finish(self):
        self.status = 1
        self.finish_time = now()
        self.save()
        
        event = Event('ProcessFinished', self)
        self.event.emit(event)
        
    def put(self, workitem, data=None):
        self.queue.put((workitem, data))
        
    def create_workitem(self, activity):
        if isinstance(activity, (str, unicode)):
            activity = self.activities[activity]
        return WorkItem(self, activity)
    
    def do_transition(self, workitem, data=None):
        """
        Execute the transition process
        """
        if workitem:
            from_ = workitem.activity.name
        else:
            from_ = workitem
        nexts = self.transitions[from_]
        found = False
        for x in nexts:
            #test if the transition will go through finish
            if x.to_ is None:
                self.finish()
                return
            
            if x.IS(data):
                event = Event('Transition', x)
                self.event.emit(event)
                w = self.create_workitem(x.to_)
                self.put(w)
                found = True
                break

        if not found:
            raise Error('The process is not correct configured, '
                'no suitable transition can be used. '
                'Current activity is %r, and no next activity can be found' % from_)

    def serial(self):
        return {'id':self.id, 'status':self.status, 
            'begin_time':self.begin_time,
            'finish_time':self.finish_time}
    
    def __repr__(self):
        return 'Process(%s)' % (self.__class__.__name__)
    