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
    class MyProcess(Process):
        author = Activity()
        review = Activity()
        publish = Activity()
        reject = Activity()
        Transitions = [('author', 'review'), ('review', 'publish'),
            ('review', 'reject')]
    
    def log(event):
        print event
        
    p = MyProcess('sample')
    p.event.connect(log)
    p.start()