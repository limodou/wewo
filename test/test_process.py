import sys,os

sys.path.insert(0, '..')

from wewo import *

def test_basic():
    """
    >>> class MyProcess(Process):
    ...     author = Activity()
    ...     review = Activity()
    ...     publish = Activity()
    ...     reject = Activity()
    ...     Transitions = [('author', 'review'), ('review', 'publish'),
    ...         ('review', 'reject')]
    >>> p = MyProcess('sample')
    >>> p.activities.keys()
    ['review', 'author', 'publish', 'reject']
    """
    
if __name__ == '__main__':
    
    class ReviewApplication(Application):
        def start(self, workitem):
            workitem.finish()
        
        def finish(self, workitem):
            return False
        
    class MyProcess(Process):
        author = Activity()
        review = Activity(application=ReviewApplication())
        publish = Activity()
        reject = Activity()
        Transitions = [('author', 'review'), ('review', 'publish', lambda data:data),
            ('review', 'reject', lambda data: not data)]
    
    def log(event):
        print event
        
    queue = get_default_workitems_queue()
    engine = BasicProcessEngine(queue)
    engine.start()
    
#    def put_callback(run=run):
#        run.send(None)
#    queue.set_callback('put', put_callback)
    
    p = MyProcess(queue)
    p.event.connect(log)
    p.start()
    
    engine.join()