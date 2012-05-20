# Author: limodou@gmail.com
# License: New BSD
#
# This is an simple workflow package
#

__all__ = ['Activity', 'Transition', 'BasicProcessEngine', 'Process']

class Error(Exception): pass

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
        self.finish(workitem)
    
    def finish(self, workitem, *args, **kwargs):
        workitem.finish()

class WorkItem(object):
    def __init__(self, process, activity):
        self.status = 0 #indicated if the workitem is finished
        self.process = process
        self.activity = activity
        
    def start(self):
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
        event = Event('WorkItemFinished', self)
        self.process.event.emit(event)
        self.process.engine.put(self, data)
        
    def __repr__(self):
        return 'WorkItem(%r:%r)' % (self.process, self.activity)
        
class Activity(object):
    def __init__(self, name=None, application=None, data=None):
        self.name = name
        self.application = application
        self.data = data
        
    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.name)
    
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
    
class BasicProcessEngine(object):
    def __init__(self, process):
        self.process = process
        self.workitems = []
        
    def create_workitem(self, activity):
        if isinstance(activity, (str, unicode)):
            activity = self.process.activities[activity]
        return WorkItem(self.process, activity)
    
    def create_id(self):
        from uuid import uuid4
        
        return uuid4().hex
    
    def put(self, workitem, data=None):
        self.workitems.append((workitem, data))
        self.run()
        
    def get(self):
        if len(self.workitems) > 0:
            return self.workitems.pop(0)
        return None
        
    def start(self):
        """
        start will find the (None, Activity) transition and execute the
        applications associated with Activity
        """
        
        self.process.id = self.create_id()
        
        event = Event('ProcessStarted', self.process)
        self.process.event.emit(event)
        self.do_transition(None)
        
    def finish(self):
        """
        finish a process
        """
        self.process.status = 1
        event = Event('ProcessFinished', self.process)
        self.process.event.emit(event)
        
    def run(self):
        x = self.get()
        if x:
            workitem, data = x
            self.do(workitem, data)
                
    def do(self, workitem, data=None):
        if workitem.status == 0:
            workitem.start()
        else:
            self.do_transition(workitem.activity.name, data)
            
    def do_transition(self, from_=None, data=None):
        """
        Execute the transition process
        """
        nexts = self.process.transitions[from_]
        for x in nexts:
            #test if the transition will go through finish
            if x.to_ is None:
                self.finish()
                break
            
            if x.IS(data):
                event = Event('Transition', x)
                self.process.event.emit(event)
                w = self.create_workitem(x.to_)
                self.put(w)
                break
        
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
            
            if isinstance(attr, Activity):
                cls.activities[name] = attr
                attr.name = name
            
    
class Process(object):
    __metaclass__ = ProcessMetaClass
    
    engine_cls = BasicProcessEngine
    event_cls = EventManager
    
    def __init__(self, name):
        self.name = name
        self._engine = None
        self._event = None
        self.id = None
        self.status = 0
        
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
        self.engine.start()
    
    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.name)
    